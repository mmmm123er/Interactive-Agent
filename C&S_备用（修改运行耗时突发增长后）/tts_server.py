# server.py
from fastapi import FastAPI, Response, Request
from fastapi.responses import StreamingResponse
import io
import time

# 全局初始化模型（只加载一次）
print("🔄 正在加载TTS模型...")
tts_model = None


def init_model():
    """初始化模型（应该只调用一次）"""
    global tts_model
    if tts_model is None:
        # 这里替换为您的实际模型加载代码
        # 例如：
        # from your_tts_module import YourTTSModel
        # tts_model = YourTTSModel()

        # 临时模拟模型
        class MockTTSModel:
            def synthesize(self, text):
                # 这里应该是实际的TTS合成代码
                # 返回 WAV 格式的 bytes
                import wave
                import numpy as np

                # 生成模拟音频数据
                sample_rate = 16000
                duration = 1.0
                samples = int(sample_rate * duration)
                audio_data = np.random.randint(-32768, 32767, samples, dtype=np.int16)

                # 创建WAV文件
                buffer = io.BytesIO()
                with wave.open(buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data.tobytes())

                return buffer.getvalue()

        tts_model = MockTTSModel()
        print("✅ TTS模型加载完成")
    return tts_model


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """服务启动时加载模型"""
    init_model()
    print("🚀 服务启动完成")


@app.post("/tts")
async def text_to_speech(request: Request):
    """TTS接口"""
    start_time = time.perf_counter()

    # 获取请求体中的文本
    body = await request.body()
    text = body.decode("utf-8")

    print(f"📝 收到文本: {text[:50]}..." if len(text) > 50 else f"📝 收到文本: {text}")

    # 使用全局模型实例进行合成
    wav_bytes = tts_model.synthesize(text)

    # 计算处理时间
    process_time = time.perf_counter() - start_time
    print(f"⚡ 服务端处理耗时: {process_time:.3f}秒")

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "X-Process-Time": str(process_time),
            "Content-Length": str(len(wav_bytes))
        }
    )


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "model_loaded": tts_model is not None
    }


if __name__ == "__main__":
    import uvicorn

    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        # 工作进程数设为1，确保模型只加载一次
        workers=1
    )