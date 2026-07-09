# tts_client_websocket.py
import asyncio
import json
import gzip
import time

import websockets
import numpy as np
import soundfile as sf


class WebSocketTTSClient:
    def __init__(self, server_url="ws://localhost:8000/ws/tts"):
        self.server_url = server_url
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.server_url)

    async def tts(self, text, voice="zf_001", speed=1.0, save_path="output.wav"):
        if not self.websocket:
            await self.connect()

        start_time = time.time()

        # 发送请求
        await self.websocket.send(json.dumps({
            "text": text,
            "voice": voice,
            "speed": speed
        }))

        # 接收元数据
        metadata = json.loads(await self.websocket.recv())
        sample_rate = metadata["sample_rate"]
        inference_time = metadata["inference_time"]

        # 接收音频数据
        compressed_data = await self.websocket.recv()

        # 解压
        pcm_data = gzip.decompress(compressed_data)
        samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32767.0

        # 保存
        if save_path:
            sf.write(save_path, samples, sample_rate)

        total_time = time.time() - start_time

        print(f"服务器推理耗时: {inference_time:.3f}秒")
        print(f"总耗时(含网络传输): {total_time:.3f}秒")
        # print(f"网络传输耗时: {total_time - inference_time:.3f}秒")

    async def close(self):
        if self.websocket:
            await self.websocket.close()


# 使用示例
async def main():
    client = WebSocketTTSClient()
    await client.connect()

    # 多次请求，复用同一连接
    for i in range(5):
        print(f"\n第{i + 1}次请求:")
        await client.tts(text[i], save_path=f"audio{i + 1}.wav")

    await client.close()


if __name__ == "__main__":
    text = ["文本转语音（Text-to-Speech，简称TTS）技术允许将电子文本转化为清晰、自然的语音输出。TTS在移动平台的应用不断扩展，主要用于改善用户体验、提供辅助功能以及实现交互式通讯等。",
    "TTS技术通过计算机软件将文本信息转换为听得见的语音信息，广泛应用于智能助手、阅读器和导航系统。它不仅增加了信息获取的渠道，还提升了服务的可达性和包容性。",
    "在移动平台，TTS扮演着至关重要的角色，它使得视障用户能够“听到”屏幕上的内容，同时也为忙碌的用户提供了方便。借助TTS技术，开发者能够构建更加人性化和无障碍的应用。",
    "文本到语音的转换开始于将需要读出的文本准备好。这个文本可以是从用户界面中获取，也可以是从本地或网络资源中读取。接下来，使用TTS对象的 speak 方法将其转换为语音输出。",
    "TTS服务在转换过程中可能会遇到各种异常，如网络问题、语音合成失败、语音引擎不可用等。因此，正确地处理这些异常是必要的。"]
    asyncio.run(main())