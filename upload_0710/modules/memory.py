"""
对话记忆系统
支持：
  1. 短期记忆：维护最近N轮对话
  2. 长期摘要：超过阈值后自动压缩历史对话为摘要
  3. 用户偏好提取：从对话中提取用户偏好并持久化
"""
import time
from typing import List, Dict, Any, Optional
from config import MEMORY_MAX_TURNS, MEMORY_SUMMARY_THRESHOLD
from services.llm_service import LLMService


SUMMARY_PROMPT = (
    "请将以下对话历史压缩为简短的摘要（100字以内），保留关键信息：\n"
    "只输出摘要内容："
)

PREFERENCE_EXTRACT_PROMPT = (
    "从对话中提取用户行为习惯和偏好，用简短JSON返回（每项不超过15字）：\n"
    '{"常用指令": "指令1,指令2", "偏好": "简短偏好描述"}\n'
    "无明显偏好则返回{}。只返回JSON："
)


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(self):
        self._llm = LLMService()
        self._history: List[Dict[str, str]] = []
        self._summary: str = ""

    def add_turn(self, role: str, content: str):
        """添加一轮对话"""
        self._history.append({"role": role, "content": content})

        if len(self._history) > MEMORY_SUMMARY_THRESHOLD and len(self._history) % 5 == 0:
            self._compress_history()

    def get_messages(self, system_prompt: str = "") -> List[Dict[str, str]]:
        """
        获取完整的消息列表（包含摘要和近期对话）
        Args:
            system_prompt: 系统提示词
        Returns:
            消息列表
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if self._summary:
            messages.append({
                "role": "system",
                "content": f"之前的对话摘要：{self._summary}",
            })

        recent = self._history[-MEMORY_MAX_TURNS:]
        messages.extend(recent)

        return messages

    def _compress_history(self):
        """压缩历史对话为摘要"""
        t0 = time.time()

        old_turns = self._history[: len(self._history) - MEMORY_SUMMARY_THRESHOLD]
        if not old_turns:
            return

        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in old_turns
        )

        messages = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": history_text},
        ]

        new_summary = self._llm.chat(messages, max_tokens=200).strip()

        if self._summary:
            self._summary = f"{self._summary}\n{new_summary}"
        else:
            self._summary = new_summary

        self._history = self._history[len(old_turns):]
        print(f"[记忆系统] 历史压缩完成 | 摘要长度: {len(self._summary)} | 耗时: {time.time() - t0:.2f}s")

    def extract_preferences(self) -> Dict[str, Any]:
        """从对话历史中提取用户偏好"""
        t0 = time.time()

        if not self._history:
            return {}

        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in self._history[-10:]
        )

        messages = [
            {"role": "system", "content": PREFERENCE_EXTRACT_PROMPT},
            {"role": "user", "content": history_text},
        ]

        result = self._llm.chat(messages, max_tokens=200).strip()

        import json
        try:
            prefs = json.loads(result)
        except json.JSONDecodeError:
            prefs = {}

        print(f"[记忆系统] 偏好提取完成 | 耗时: {time.time() - t0:.2f}s")
        return prefs

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return list(self._history)

    def clear(self):
        """清空记忆"""
        self._history.clear()
        self._summary = ""
