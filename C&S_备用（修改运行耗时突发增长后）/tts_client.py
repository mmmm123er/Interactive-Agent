import httpx
import time

def tts(text: str, url: str = "http://localhost:8000/tts") -> bytes:
    """发送文本，返回 WAV bytes"""
    start = time.time()
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, content=text.encode("utf-8"))
        resp.raise_for_status()
        duration = time.time() - start
        print(f"⏱️  TTS 耗时: {duration:.3f} 秒")
        return resp.content

if __name__ == "__main__":

    # texts = ["0感知层：无人机群（搭载全景摄像头）、陆/水基停机坪",
    # "1边缘计算层：机载计算单元（景摄像头+孪生基座用于三维重建；光电吊舱+边缘计算盒子用于日常基本任务）",
    # "2平台层：数据处理中心、AI算法引擎、三维GIS平台",
    # "3应用层：生态监测、安全预警、智慧管理、商业服务",
    # "4展示层：地面端大屏幕、移动端APP、Web管理平台"
    # ]
    i = 0
    # for text in texts:
    while True:
        text = input("input text")
        wav_bytes = tts(text)

        with open(f"{i}.wav", "wb") as f:
            f.write(wav_bytes)
        i+=1
        print("✅ 已保存 output.wav")