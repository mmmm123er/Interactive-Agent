"""
声纹识别服务模块
基于modelscope的CAM++声纹验证pipeline，预热后常驻内存
"""
import os
import time
import shutil
import numpy as np
from typing import Optional, Tuple, List
from config import (
    CAMPPLUS_MODEL_PATH,
    VOICEPRINT_DB_DIR,
    VOICEPRINT_THRESHOLD,
)


class VoiceprintService:
    """声纹识别服务 - 单例模式，预热后直接使用"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._pipeline = None
        self._db_cache: dict = {}
        self._initialized = True

    def warm_up(self):
        """预热：加载CAM++声纹验证模型"""
        if self._pipeline is not None:
            return
        print("[声纹服务] 正在加载CAM++模型...")
        t0 = time.time()
        from modelscope.pipelines import pipeline
        self._pipeline = pipeline(
            task="speaker-verification",
            model=CAMPPLUS_MODEL_PATH,
        )
        self._load_database()
        print(f"[声纹服务] 模型加载完成，耗时: {time.time() - t0:.2f}s")

    def _load_database(self):
        """加载声纹数据库中所有已注册用户的wav路径"""
        self._db_cache.clear()
        if not os.path.isdir(VOICEPRINT_DB_DIR):
            return
        for fname in os.listdir(VOICEPRINT_DB_DIR):
            if fname.lower().endswith(".wav"):
                username = os.path.splitext(fname)[0]
                filepath = os.path.join(VOICEPRINT_DB_DIR, fname)
                self._db_cache[filepath] = username

    def recognize(self, audio_path: str) -> Tuple[Optional[str], float]:
        """
        声纹识别：将输入音频与数据库中所有注册音频比对
        Args:
            audio_path: 待识别音频文件路径
        Returns:
            (匹配用户名, 最高相似度分数)；未匹配到返回 (None, 0.0)
        """
        t0 = time.time()
        if self._pipeline is None:
            self.warm_up()

        best_user = None
        best_score = 0.0

        for db_path, username in self._db_cache.items():
            result = self._pipeline([audio_path, db_path], thr=VOICEPRINT_THRESHOLD)
            score = result[0]["score"] if isinstance(result, list) else result["score"]
            if score > best_score:
                best_score = score
                best_user = username

        elapsed = time.time() - t0
        matched = best_score >= VOICEPRINT_THRESHOLD
        print(f"[声纹服务] 识别完成 | 用户: {best_user} | 分数: {best_score:.3f} | 匹配: {matched} | 耗时: {elapsed:.2f}s")
        return best_user if matched else None, best_score

    def register(self, audio_path: str, username: str) -> str:
        """
        注册新用户声纹
        Args:
            audio_path: 原始音频路径
            username: 用户名
        Returns:
            保存后的声纹文件路径
        """
        t0 = time.time()
        dest = os.path.join(VOICEPRINT_DB_DIR, f"{username}.wav")
        shutil.copy2(audio_path, dest)
        self._db_cache[dest] = username
        print(f"[声纹服务] 新用户注册: {username} | 耗时: {time.time() - t0:.2f}s")
        return dest

    def get_registered_users(self) -> List[str]:
        """获取所有已注册用户名"""
        return list(set(self._db_cache.values()))
