"""
用户管理模块
负责：
  1. 新用户声纹注册（保存wav + 创建md）
  2. 已有用户偏好加载
  3. 用户行为习惯和偏好的记录与合并
"""
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
from config import USER_CONFIG_DIR, VOICEPRINT_DB_DIR
from services.voiceprint_service import VoiceprintService
from services.llm_service import LLMService


PROFILE_SUMMARY_PROMPT = (
    "你是一个用户画像总结助手。请根据以下用户的交互记录，"
    "用自然、亲切的语言总结这位用户的行为习惯和偏好特点。\n"
    "要求：\n"
    "1. 像描述一个朋友一样，用完整的句子描述\n"
    "2. 包含用户常用的指令类型、偏好习惯等\n"
    "3. 控制在100字以内\n"
    "4. 只输出总结内容，不要有前缀或解释"
)


class UserManager:
    """用户管理器"""

    def __init__(self):
        self._voiceprint = VoiceprintService()

    def is_registered(self, username: Optional[str]) -> bool:
        """判断用户是否已注册"""
        if not username:
            return False
        config_path = os.path.join(USER_CONFIG_DIR, f"{username}.md")
        return os.path.exists(config_path)

    def register_new_user(self, audio_path: str, username: str):
        """
        注册新用户
        1. 保存声纹wav
        2. 创建用户配置md
        """
        t0 = time.time()
        self._voiceprint.register(audio_path, username)

        config_path = os.path.join(USER_CONFIG_DIR, f"{username}.md")
        content = (
            f"# {username} 的行为偏好\n\n"
            f"- 注册时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- 常用指令: 暂无\n"
            f"- 偏好: 暂无\n"
        )
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[用户管理] 新用户注册完成: {username} | 耗时: {time.time() - t0:.2f}s")

    def load_user_profile(self, username: str) -> Dict[str, str]:
        """
        加载用户偏好配置（兼容新旧格式）
        Returns:
            包含 summary 和键值对的用户画像
        """
        t0 = time.time()
        config_path = os.path.join(USER_CONFIG_DIR, f"{username}.md")
        profile = {}

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            summary_lines = []
            in_summary = False
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("## 用户画像总结"):
                    in_summary = True
                    continue
                if in_summary:
                    if stripped.startswith("- ") or stripped.startswith("#"):
                        in_summary = False
                    elif stripped:
                        summary_lines.append(stripped)
                if stripped.startswith("- ") and ":" in stripped:
                    parts = stripped[2:].split(":", 1)
                    if len(parts) == 2:
                        profile[parts[0].strip()] = parts[1].strip()

            if summary_lines:
                profile["summary"] = " ".join(summary_lines)

        print(f"[用户管理] 用户配置加载: {username} | 耗时: {time.time() - t0:.2f}s")
        return profile

    def update_user_profile(self, username: str, new_info: Dict[str, Any]):
        """
        更新用户偏好（合并写入，使用LLM生成自然语言总结）
        Args:
            username: 用户名
            new_info: 新的行为/偏好信息
        """
        t0 = time.time()
        existing = self.load_user_profile(username)

        for key, value in new_info.items():
            if key in existing and key == "常用指令":
                old_cmds = [c.strip() for c in existing[key].split(",")]
                if isinstance(value, str):
                    value = [value]
                merged = list(dict.fromkeys(old_cmds + value))
                existing[key] = ", ".join(merged[-10:])
            else:
                existing[key] = str(value)

        existing["最后更新"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not existing.get("summary"):
            self._summarize_profile(username, existing, new_info)

        self._save_profile(username, existing)
        print(f"[用户管理] 用户配置更新: {username} | 耗时: {time.time() - t0:.2f}s")

    def summarize_and_update(self, username: str, conversation_history: list, new_info: Dict[str, Any] = None):
        """
        基于对话历史，用LLM重新生成用户画像总结并更新md文件
        Args:
            username: 用户名
            conversation_history: 对话历史 [{"role": ..., "content": ...}, ...]
            new_info: 额外的行为信息（如任务执行记录）
        """
        t0 = time.time()
        existing = self.load_user_profile(username)

        if new_info:
            for key, value in new_info.items():
                if key in existing and key == "常用指令":
                    old_cmds = [c.strip() for c in existing[key].split(",")]
                    if isinstance(value, str):
                        value = [value]
                    merged = list(dict.fromkeys(old_cmds + value))
                    existing[key] = ", ".join(merged[-10:])
                else:
                    existing[key] = str(value)

        existing["最后更新"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._summarize_profile(username, existing, new_info or {}, conversation_history)
        self._save_profile(username, existing)
        print(f"[用户管理] 用户画像LLM总结完成: {username} | 耗时: {time.time() - t0:.2f}s")

    def _summarize_profile(self, username: str, existing: Dict[str, str],
                           new_info: Dict[str, Any],
                           conversation_history: list = None):
        """使用LLM生成用户画像的自然语言总结"""
        try:
            llm = LLMService()
            if llm._client is None:
                llm.warm_up()

            context_parts = [f"用户名: {username}"]
            if existing.get("注册时间"):
                context_parts.append(f"注册时间: {existing['注册时间']}")
            if existing.get("常用指令"):
                context_parts.append(f"常用指令记录: {existing['常用指令']}")
            if existing.get("偏好") and existing["偏好"] not in ("暂无", "无"):
                context_parts.append(f"偏好记录: {existing['偏好']}")
            if existing.get("最后任务"):
                context_parts.append(f"最近任务: {existing['最后任务']}")
            if new_info:
                context_parts.append(f"本次交互: {new_info}")
            if conversation_history:
                recent = conversation_history[-10:]
                history_text = "\n".join(
                    f"{m['role']}: {m['content']}" for m in recent
                )
                context_parts.append(f"近期对话:\n{history_text}")

            context = "\n".join(context_parts)

            messages = [
                {"role": "system", "content": PROFILE_SUMMARY_PROMPT},
                {"role": "user", "content": context},
            ]

            result = llm.chat(messages, max_tokens=200).strip()
            if result and len(result) > 5:
                existing["summary"] = result
                print(f"[用户管理] LLM画像总结生成成功")
        except Exception as e:
            print(f"[用户管理] LLM画像总结失败: {e}")

    def _save_profile(self, username: str, profile: Dict[str, str]):
        """将用户配置写入md文件"""
        config_path = os.path.join(USER_CONFIG_DIR, f"{username}.md")
        lines = [f"# {username} 的行为偏好\n"]

        if profile.get("summary"):
            lines.append("## 用户画像总结\n")
            lines.append(profile["summary"])
            lines.append("")

        skip_keys = {"summary"}
        for k, v in profile.items():
            if k not in skip_keys:
                lines.append(f"- {k}: {v}")
        lines.append("")

        with open(config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
