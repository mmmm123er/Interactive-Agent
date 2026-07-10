# import torch
# import soundfile as sf
# from qwen_tts import Qwen3TTSModel
#
# # Load the model
# model = Qwen3TTSModel.from_pretrained(
#     "models/Qwen3-TTS-12Hz-0.6B-CustomVoice",
#     device_map="cuda:0",
#     dtype=torch.bfloat16,
#     # attn_implementation="flash_attention_2",
# )
#
# # Generate speech with specific instructions
# wavs, sr = model.generate_custom_voice(
#     text="其实我真的有发现，我是一个特别善于观察别人情绪的人。",
#     language="Chinese",
#     speaker="Vivian",
#     instruct="用贴心的语气温声细雨的说",
# )
#
# # Save the generated audio
# sf.write("output_custom_voice.wav", wavs[0], sr)


# tts_server.py
import torch
import io
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from qwen_tts import Qwen3TTSModel

app = FastAPI()

print("正在加载 TTS 模型至 GPU (cuda:0) 独占...")
model = Qwen3TTSModel.from_pretrained(
    "models/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    device_map="cuda:0",
    dtype=torch.bfloat16
)
print("TTS 独立 API 服务加载完毕。")


@app.get("/tts")
async def tts_endpoint(
        text: str = Query(..., description="要合成的文本"),
        speaker: str = "Vivian",
        instruct: str = "温声细雨的说"
):
    # 强制使用 PyTorch 极速推理模式，彻底消除梯度开销
    with torch.inference_mode():
        wavs, sr = model.generate_custom_voice(
            text=text,
            language="Chinese",
            speaker=speaker,
            instruct=instruct
        )

    # 转换为 numpy.float32 字节流
    raw_wav = wavs[0]
    if torch.is_tensor(raw_wav):
        chunk_data = raw_wav.detach().cpu().to(torch.float32).numpy().tobytes()
    else:
        chunk_data = raw_wav.astype(np.float32).tobytes()

    return StreamingResponse(io.BytesIO(chunk_data), media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn

    # 启动 API 服务，绑定 8001 端口
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")