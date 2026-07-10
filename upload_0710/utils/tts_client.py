import httpx
import time
import wave  # <--- 导入 wave 库


def tts(text: str, url: str = "http://localhost:8000/tts_stream") -> bytes:
    """发送文本，返回原始 PCM bytes"""
    start = time.time()
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, content=text.encode("utf-8"))
        resp.raise_for_status()
        duration = time.time() - start
        print(f"⏱️  TTS 耗时: {duration:.3f} 秒")
        return resp.content  # 返回的是原始的 PCM 字节


def save_pcm_as_wav(pcm_bytes: bytes, output_path: str, sample_rate: int = 24000):
    """将接收到的原始 PCM 字节转换为标准可播放的 WAV 文件"""
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16位(int16) 对应 2 字节
        wav_file.setframerate(sample_rate)  # 采样率 24000
        wav_file.writeframes(pcm_bytes)


if __name__ == "__main__":
    texts = [
        "0感知层：无人机群（搭载全景摄像头）、陆/水基停机坪",
        "1边缘计算层：机载计算单元（景摄像头+孪生基座用于三维重建；光电吊舱+边缘计算盒子用于日常基本任务）",
        "2平台层：数据处理中心、AI算法引擎、三维GIS平台",
        "3应用层：生态监测、安全预警、智慧管理、商业服务",
        "4展示层：地面端大屏幕、移动端APP、Web管理平台"
    ]

    for i, text in enumerate(texts):
        # 1. 获取原始音频流数据
        pcm_data = tts(text)

        # 2. 【关键修复】将原始 PCM 数据转换为带报头的标准 WAV 并保存
        wav_filename = f"{i}.wav"
        save_pcm_as_wav(pcm_data, wav_filename, sample_rate=24000)

        print(f"✅ 已保存并成功打包为标准可播放文件: {wav_filename}")