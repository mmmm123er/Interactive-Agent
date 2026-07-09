from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from kokoro import KModel, KPipeline
import soundfile as sf
import io
import uvicorn

# === 配置 ===
REPO_ID = 'hexgrad/Kokoro-82M-v1.1-zh'
SAMPLE_RATE = 24000
VOICE = 'zf_001'
device = 'cuda'

# 全局模型
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, zh_pipeline, en_pipeline
    en_pipeline = KPipeline(lang_code='a', repo_id=REPO_ID, model=False)
    model = KModel(repo_id=REPO_ID).to(device).eval()
    zh_pipeline = KPipeline(lang_code='z', repo_id=REPO_ID, model=model, en_callable=en_callable)
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)  # 关闭文档减少开销

@app.post("/tts")
async def tts(request: Request):
    # 直接读取原始文本（UTF-8）
    text = (await request.body()).decode("utf-8").strip()
    if not text:
        return Response(status_code=400)

    # 执行推理（完全复用你的逻辑）
    result = next(zh_pipeline(text, voice=VOICE, speed=speed_callable))
    wav = result.audio

    # 写入内存并返回
    buffer = io.BytesIO()
    sf.write(buffer, wav, SAMPLE_RATE, format='WAV')
    return Response(content=buffer.getvalue(), media_type="audio/wav")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="critical", workers=1)