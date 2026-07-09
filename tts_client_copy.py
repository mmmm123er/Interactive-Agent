# enhanced_tts_client.py

import httpx
import pyaudio
import numpy as np
import re
import time

# ===== 配置 =====
TTS_URL = "http://localhost:8000/tts_stream"
SAMPLE_RATE = 24000
CHANNELS = 1
DTYPE = np.int16

# ===== 音频设备检测 =====
def find_headphone_device(p: pyaudio.PyAudio):
    """尝试找到包含 'headphone' 或 '耳机' 的输出设备"""
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    for i in range(num_devices):
        device = p.get_device_info_by_host_api_device_index(0, i)
        if device['maxOutputChannels'] > 0:
            name = device['name'].lower()
            if any(kw in name for kw in ['headphone', '耳机', 'output', '扬声器', 'speaker']):
                print(f"🎧 候选音频输出设备 [{i}]: {device['name']}")
                return i
    # 默认使用系统默认
    print("⚠️ 未找到明确耳机设备，使用默认输出")
    return p.get_default_output_device_info()['index']

# ===== 播放函数 =====
def play_streaming_tts(text: str):
    p = pyaudio.PyAudio()
    try:
        device_index = find_headphone_device(p)
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            output_device_index=device_index,
            frames_per_buffer=1024
        )

        print(f"🔊 开始播放文本: {text[:50]}...")
        total_bytes = 0

        # 在 play_streaming_tts 函数中
        with httpx.stream("POST", TTS_URL, content=text.encode("utf-8"), timeout=60) as resp:
            resp.raise_for_status()
            total_bytes = 0
            for chunk in resp.iter_bytes(chunk_size=1024):
                if chunk:
                    total_bytes += len(chunk)
                    stream.write(chunk)
            print(f"📥 共接收到 {total_bytes} 字节音频数据")

        print(f"✅ 播放完成，总音频字节数: {total_bytes} (约 {total_bytes / (2 * SAMPLE_RATE):.2f} 秒)")

    except Exception as e:
        print(f"❌ 播放错误: {e}")
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except:
            pass
        p.terminate()

# ===== 测试 =====
if __name__ == "__main__":
    test_text = "你好，这是测试音频。请确认耳机是否正常工作。"
    play_streaming_tts(test_text)