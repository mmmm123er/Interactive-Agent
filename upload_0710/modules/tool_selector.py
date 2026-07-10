"""
MCP工具选择模块
两层设计：
  第一层 - 选择能力类别（状态查询/空间记忆/探索/导航/任务控制）
  第二层 - 在对应能力下选择具体MCP工具
"""
import time
import json
from typing import Dict, Any, Optional, List
from config import CAPABILITY_TYPES
from services.llm_service import LLMService


def _build_capability_prompt() -> str:
    """构建第一层能力分类的提示词"""
    cap_list = "\n".join(
        f"- {name}: {info['description']}"
        for name, info in CAPABILITY_TYPES.items()
    )
    return (
        f"你是一个机器人任务调度助手。\n"
        f"请根据用户的指令，判断其属于以下哪种能力类别（只返回类别名称，不要多余文字）：\n"
        f"{cap_list}\n"
        f"只返回类别名称："
    )


def _build_tool_prompt(capability_name: str) -> str:
    """构建第二层工具选择的提示词"""
    tools = CAPABILITY_TYPES.get(capability_name, {}).get("tools", [])
    tool_list = "\n".join(
        f"- {t['name']}: {t['description']}" for t in tools
    )
    return (
        f"你是一个机器人工具选择助手。\n"
        f"当前能力类别为「{capability_name}」，可用工具如下：\n"
        f"{tool_list}\n"
        f"请根据用户指令，选择最合适的工具，返回JSON格式：\n"
        f'{{"tool_name": "工具名", "arguments": {{参数}}}}\n'
        f"只返回JSON："
    )


def _build_openai_tools(capability_name: str) -> List[Dict[str, Any]]:
    """将能力下的工具转为OpenAI function calling格式"""
    tools = CAPABILITY_TYPES.get(capability_name, {}).get("tools", [])
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                            "description": "用户指令的详细描述"
                        }
                    },
                    "required": ["detail"],
                },
            },
        }
        for t in tools
    ]


class ToolSelector:
    """两层MCP工具选择器"""

    def __init__(self):
        self._llm = LLMService()

    def select(self, user_input: str) -> Dict[str, Any]:
        """
        选择工具
        Args:
            user_input: 用户指令文本
        Returns:
            {
                "capability": 能力类别,
                "tool_name": 工具名,
                "arguments": 参数dict
            }
        """
        t0 = time.time()

        cap_name = self._select_capability(user_input)
        tool_result = self._select_tool(user_input, cap_name)

        result = {
            "capability": cap_name,
            "tool_name": tool_result.get("tool_name"),
            "arguments": tool_result.get("arguments", {}),
        }
        print(f"[工具选择] 能力: {cap_name} | 工具: {result['tool_name']} | 耗时: {time.time() - t0:.2f}s")
        return result

    def _select_capability(self, user_input: str) -> str:
        """第一层：选择能力类别"""
        messages = [
            {"role": "system", "content": _build_capability_prompt()},
            {"role": "user", "content": user_input},
        ]
        cap_name = self._llm.chat(messages, max_tokens=50).strip()

        if cap_name not in CAPABILITY_TYPES:
            for key in CAPABILITY_TYPES:
                if key in cap_name:
                    cap_name = key
                    break
            else:
                cap_name = "状态查询"

        return cap_name

    def _select_tool(self, user_input: str, capability_name: str) -> Dict[str, Any]:
        """第二层：在能力类别下选择具体工具（使用function calling）"""
        tools_def = _build_openai_tools(capability_name)

        messages = [
            {"role": "system", "content": _build_tool_prompt(capability_name)},
            {"role": "user", "content": user_input},
        ]

        result = self._llm.function_call(messages, tools_def)
        return result
