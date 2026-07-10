"""
大模型推理服务模块
基于OpenAI兼容API，支持普通对话、多模态、function calling、流式输出
"""
import time
from typing import List, Dict, Any, Optional, Generator
from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL_NAME,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_TOP_P,
)

import os
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["all_proxy"] = ""


class LLMService:
    """大模型推理服务 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._client = None
        self._initialized = True

    def warm_up(self):
        """预热：初始化OpenAI客户端"""
        if self._client is not None:
            return
        print("[LLM服务] 正在初始化OpenAI客户端...")
        t0 = time.time()
        from openai import OpenAI
        self._client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        print(f"[LLM服务] 客户端初始化完成，耗时: {time.time() - t0:.2f}s")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
        stream: bool = False,
    ) -> str:
        """
        普通对话补全
        Args:
            messages: 消息列表
            temperature: 温度
            max_tokens: 最大token数
            stream: 是否流式
        Returns:
            模型回复文本
        """
        t0 = time.time()
        if self._client is None:
            self.warm_up()

        response = self._client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=LLM_TOP_P,
            presence_penalty=0.0,
            extra_body={"enable_thinking": False},
            stream=stream,
        )

        if stream:
            full_text = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_text += chunk.choices[0].delta.content
            result = full_text
        else:
            result = response.choices[0].message.content

        print(f"[LLM服务] 对话完成 | 耗时: {time.time() - t0:.2f}s")
        return result

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
    ) -> Generator[str, None, None]:
        """
        流式对话，逐块返回文本
        Args:
            messages: 消息列表
        Yields:
            文本片段
        """
        if self._client is None:
            self.warm_up()

        response = self._client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=LLM_TOP_P,
            presence_penalty=0.0,
            extra_body={"enable_thinking": False},
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def multimodal_chat(
        self,
        text: str,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
    ) -> str:
        """
        多模态对话（文本+图像）
        Args:
            text: 文本内容
            image_url: 图像URL
            image_path: 本地图像路径
        Returns:
            模型回复
        """
        t0 = time.time()
        if self._client is None:
            self.warm_up()

        content = []
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_path:
            import base64
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        content.append({"type": "text", "text": text})

        messages = [{"role": "user", "content": content}]
        response = self._client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            top_p=LLM_TOP_P,
            extra_body={"enable_thinking": False},
            stream=False,
        )

        result = response.choices[0].message.content
        print(f"[LLM服务] 多模态对话完成 | 耗时: {time.time() - t0:.2f}s")
        return result

    def function_call(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        函数调用
        Args:
            messages: 消息列表
            tools: 工具定义列表（OpenAI function calling格式）
        Returns:
            {"tool_name": str, "arguments": dict}
        """
        t0 = time.time()
        if self._client is None:
            self.warm_up()

        response = self._client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            extra_body={"enable_thinking": False},
        )

        message = response.choices[0].message
        result = {"tool_name": None, "arguments": {}}

        if message.tool_calls:
            tc = message.tool_calls[0]
            result["tool_name"] = tc.function.name
            import json
            try:
                result["arguments"] = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                result["arguments"] = {"raw": tc.function.arguments}

        print(f"[LLM服务] 函数调用完成 | 工具: {result['tool_name']} | 耗时: {time.time() - t0:.2f}s")
        return result
