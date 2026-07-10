"""
ASR语音识别服务模块
基于Qwen3-ASR，预热后常驻内存，预留流式识别接口
"""
import time
from typing import Optional
from config import ASR_MODEL_PATH, ASR_DEVICE, ASR_MAX_BATCH_SIZE, ASR_MAX_NEW_TOKENS


class ASRService:
    """ASR语音识别服务 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._model = None
        self._initialized = True

    def warm_up(self):
        """预热：加载Qwen3-ASR模型"""
        if self._model is not None:
            return
        print("[ASR服务] 正在加载Qwen3-ASR模型...")
        t0 = time.time()
        import torch
        from qwen_asr import Qwen3ASRModel
        self._model = Qwen3ASRModel.from_pretrained(
            ASR_MODEL_PATH,
            dtype=torch.float32,
            device_map=ASR_DEVICE,
            max_inference_batch_size=ASR_MAX_BATCH_SIZE,
            max_new_tokens=ASR_MAX_NEW_TOKENS,
        )
        print(f"[ASR服务] 模型加载完成，耗时: {time.time() - t0:.2f}s")

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        语音转文字
        Args:
            audio_path: 音频文件路径
            language: 指定语言（None为自动检测）
        Returns:
            识别文本
        """
        t0 = time.time()
        if self._model is None:
            self.warm_up()

        results = self._model.transcribe(audio=audio_path, language=language)
        text = results[0].text

        print(f"[ASR服务] 识别完成 | 文本: {text[:50]}... | 耗时: {time.time() - t0:.2f}s")
        return text

    def stream_transcribe(self, audio_stream):
        """
        流式语音识别（预留接口，后续实现）
        Args:
            audio_stream: 音频流
        """
        raise NotImplementedError("流式ASR功能将在后续版本中实现")
