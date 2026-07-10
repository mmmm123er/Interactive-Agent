"""
响应精简模块
将大模型的冗长输出压缩为简短回复
可作为独立插件使用
"""
import time
from config import RESPONSE_MAX_LENGTH
from services.llm_service import LLMService


CONDENSE_PROMPT = (
    "请将以下回复精简为{max_len}字以内的简短回复，保留核心意思，不要丢失关键信息：\n"
    "只输出精简后的内容："
)


def condense_response(text: str, max_length: int = RESPONSE_MAX_LENGTH) -> str:
    """
    精简文本回复
    如果文本已经足够短，直接返回
    Args:
        text: 原始文本
        max_length: 目标最大长度
    Returns:
        精简后的文本
    """
    if len(text) <= max_length:
        return text

    t0 = time.time()
    llm = LLMService()

    messages = [
        {"role": "system", "content": CONDENSE_PROMPT.format(max_len=max_length)},
        {"role": "user", "content": text},
    ]

    result = llm.chat(messages, max_tokens=max_length * 2).strip()
    print(f"[响应精简] 原文{len(text)}字 -> {len(result)}字 | 耗时: {time.time() - t0:.2f}s")
    return result
