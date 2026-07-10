
# tts_server.py (修改版)

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from kokoro import KModel, KPipeline
import numpy as np
import re
import io
import uvicorn

LOCAL_MODEL_DIR = "/home/GNC618/WokSpace/Interactive_System/utils/models/Kokoro-82M-v1.1-zh"

REPO_ID = 'hexgrad/Kokoro-82M-v1.1-zh'
SAMPLE_RATE = 24000
VOICE = '/home/GNC618/Downloads/zf_001.pt'
device = 'cpu'

model = None
zh_pipeline = None
en_pipeline = None


def en_callable(text):
    if text == 'Kokoro':
        return 'kˈOkəɹO'
    elif text == 'Sol':
        return 'sˈOl'
    return next(en_pipeline(text)).phonemes


def speed_callable(len_ps):
    speed = 0.8
    if len_ps <= 83:
        speed = 1
    elif len_ps < 183:
        speed = 1 - (len_ps - 83) / 500
    return speed * 1.1


# 按句子切分（简单规则）
def split_sentences(text: str):
    # 保留分隔符，避免丢失标点
    parts = re.split(r'([。！？；\n])', text)
    sentences = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts):
            s = parts[i] + parts[i + 1]
            if s.strip():
                sentences.append(s.strip())
            i += 2
        else:
            if parts[i].strip():
                sentences.append(parts[i].strip())
            i += 1
    if not sentences:
        sentences = [text]
    return sentences


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, zh_pipeline, en_pipeline
    print("🔧 正在加载模型...")
    en_pipeline = KPipeline(lang_code='a', repo_id=REPO_ID, model=False)
    model = KModel(
        repo_id="local/Kokoro-82M-v1.1-zh",  # 传入自定义的本地 repo_id 占位符
        config=f"{LOCAL_MODEL_DIR}/config.json",  # 指向本地 config.json 路径
        model=f"{LOCAL_MODEL_DIR}/kokoro-v1_1-zh.pth"  # 指向本地 pth 权重路径
    ).to(device).eval()
    zh_pipeline = KPipeline(lang_code='z', repo_id=REPO_ID, model=model, en_callable=en_callable)

    print("🔥 正在预热模型...")
    _ = next(zh_pipeline("预热测试。", voice=VOICE, speed=1.0))
    print("✅ 模型预热完成！")

    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


def generate_audio_stream(text: str):
    print(f"📥 接收到文本: {repr(text)}")

    if not text.strip():
        return
    try:
        result = next(zh_pipeline(text, voice=VOICE, speed=1.0))
        audio_tensor = result.audio

        if hasattr(audio_tensor, 'cpu'):
            audio = audio_tensor.cpu().numpy()
        else:
            audio = np.array(audio_tensor)

        print(f"✅ 合成成功 | 文本长度: {len(text)} | 音频长度: {len(audio)}")

        audio = np.clip(audio, -1.0, 1.0)
        audio_int16 = (audio * 32767).astype(np.int16)
        yield audio_int16.tobytes()

    except Exception as e:
        print(f"💥 合成失败: {text[:50]}... | 错误: {e}")


@app.post("/tts_stream")
async def tts_stream(request: Request):
    text = (await request.body()).decode("utf-8").strip()
    if not text:
        return StreamingResponse(iter([]), media_type="audio/pcm")

    return StreamingResponse(
        generate_audio_stream(text),
        media_type="audio/pcm; rate=24000; channels=1; format=int16"
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="critical", workers=1)