"""
意图分类模块
使用文本向量化和余弦相似度区分「闲聊」和「任务指令」
command.txt 中以 # 开头的行为注释，不参与向量化
"""
import os
import time
import pickle
import numpy as np
from typing import Tuple, List
from config import (
    COMMAND_FILE_PATH,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_CACHE_PATH,
    INTENT_SIMILARITY_THRESHOLD,
)


class IntentClassifier:
    """意图分类器：基于文本向量化的闲聊/任务判别"""

    def __init__(self):
        self._model = None
        self._commands: List[str] = []
        self._command_embeddings: np.ndarray = None

    def warm_up(self):
        """预热：加载向量化模型并预计算命令向量"""
        if self._model is not None:
            return
        print("[意图分类] 正在加载向量化模型...")
        t0 = time.time()

        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)

        self._load_commands()
        self._build_embeddings()

        print(f"[意图分类] 预热完成 | 命令数: {len(self._commands)} | 耗时: {time.time() - t0:.2f}s")

    def _load_commands(self):
        """从command.txt加载命令，跳过#开头的注释行"""
        self._commands = []
        with open(COMMAND_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    self._commands.append(line)

    def _build_embeddings(self):
        """构建命令向量，优先从缓存加载"""
        if os.path.exists(EMBEDDING_CACHE_PATH):
            with open(EMBEDDING_CACHE_PATH, "rb") as f:
                cache = pickle.load(f)
            if cache.get("commands") == self._commands:
                self._command_embeddings = cache["embeddings"]
                print(f"[意图分类] 从缓存加载命令向量")
                return

        self._command_embeddings = self._model.encode(self._commands, show_progress_bar=False)

        os.makedirs(os.path.dirname(EMBEDDING_CACHE_PATH) or ".", exist_ok=True)
        with open(EMBEDDING_CACHE_PATH, "wb") as f:
            pickle.dump({"commands": self._commands, "embeddings": self._command_embeddings}, f)
        print(f"[意图分类] 命令向量已缓存")

    def classify(self, text: str) -> Tuple[str, float, bool]:
        """
        分类用户意图
        Args:
            text: 用户输入文本（ASR识别结果）
        Returns:
            (最匹配命令, 最高相似度, 是否为任务指令)
        """
        t0 = time.time()
        if self._model is None:
            self.warm_up()

        user_emb = self._model.encode([text], show_progress_bar=False)

        from sklearn.metrics.pairwise import cosine_similarity
        sims = cosine_similarity(user_emb, self._command_embeddings)[0]

        max_idx = int(np.argmax(sims))
        max_sim = float(sims[max_idx])
        best_cmd = self._commands[max_idx]
        is_task = max_sim >= INTENT_SIMILARITY_THRESHOLD

        print(f"[意图分类] 文本: {text[:30]} | 匹配: {best_cmd} | 相似度: {max_sim:.3f} | 任务: {is_task} | 耗时: {time.time() - t0:.2f}s")
        return best_cmd, max_sim, is_task
