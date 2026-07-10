"""
TTS语音合成服务模块
基于远程TTS服务器（通过HTTP客户端），支持流式合成接口
"""
import time
import os
import numpy as np
from typing import Optional, Generator

from config import TTS_SERVER_URL, TTS_SAMPLE_RATE
from utils.tts_client import tts, save_pcm_as_wav


class TTSService:
    """TTS语音合成服务 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._sample_rate = TTS_SAMPLE_RATE
        self._initialized = True

    def warm_up(self):
        """预热：检查TTS服务器连通性"""
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(TTS_SERVER_URL, content="测试".encode("utf-8"))
                resp.raise_for_status()
            print("[TTS服务] 服务器连接正常")
        except Exception as e:
            print(f"[TTS服务] 服务器连接失败: {e}")

    def synthesize(
        self,
        text: str,
        output_path: str,
        speaker: str = None,
        language: str = None,
        instruct: Optional[str] = None,
    ) -> str:
        """
        文本转语音
        Args:
            text: 待合成文本
            output_path: 输出音频路径
            speaker: 说话人（远程服务端已配置，此参数保留兼容性）
            language: 语言（保留兼容性）
            instruct: 指令（保留兼容性）
        Returns:
            输出文件路径
        """
        t0 = time.time()

        pcm_data = tts(text, TTS_SERVER_URL)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        save_pcm_as_wav(pcm_data, output_path, sample_rate=TTS_SAMPLE_RATE)

        print(f"[TTS服务] 合成完成 | 文本长度: {len(text)} | 耗时: {time.time() - t0:.2f}s")
        return output_path

    def synthesize_to_data(
        self,
        text: str,
        speaker: str = None,
        language: str = None,
    ):
        """
        合成文本并返回音频数据（不写文件）
        Args:
            text: 待合成文本
            speaker: 说话人（保留兼容性）
            language: 语言（保留兼容性）
        Returns:
            (audio_data, sample_rate) - audio_data为float32 numpy数组
        """
        t0 = time.time()

        pcm_data = tts(text, TTS_SERVER_URL)

        audio_int16 = np.frombuffer(pcm_data, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        print(f"[TTS服务] 合成完成 | 文本: {text[:30]}... | 耗时: {time.time() - t0:.2f}s")
        return audio_float32, TTS_SAMPLE_RATE

    def stream_synthesize(
        self,
        text_generator: Generator[str, None, None],
        output_path: str,
        speaker: str = None,
        language: str = None,
    ) -> str:
        """
        流式合成：接收文本生成器，按句分段合成
        Args:
            text_generator: LLM流式输出的文本生成器
            output_path: 输出音频路径
        Returns:
            输出文件路径
        """
        t0 = time.time()

        full_text = ""
        for token in text_generator:
            full_text += token

        if full_text.strip():
            pcm_data = tts(full_text.strip(), TTS_SERVER_URL)
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            save_pcm_as_wav(pcm_data, output_path, sample_rate=TTS_SAMPLE_RATE)

        print(f"[TTS服务] 流式合成完成 | 耗时: {time.time() - t0:.2f}s")
        return output_path

    @property
    def sample_rate(self) -> int:
        return self._sample_rate or TTS_SAMPLE_RATE
