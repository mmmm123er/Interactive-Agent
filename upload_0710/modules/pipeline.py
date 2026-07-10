"""
主流程编排模块
整合所有子模块，实现完整的「对话 + 任务工具选择」交互流程
支持流式 LLM→TTS→播放 管道，大幅降低首次响应延迟
"""
import os
import re
import time
import threading
import queue
from typing import Optional, Dict, Any, List

from config import (
    VOICEPRINT_THRESHOLD, TEMP_TTS_OUTPUT_PATH,
    STREAMING_ENABLED, STREAMING_MAX_TOKENS,
    TTS_SAMPLE_RATE,
    USE_PROCESS_SERVICES,
)
from services.voiceprint_service import VoiceprintService
from services.llm_service import LLMService
from services.asr_service import ASRService
from services.tts_service import TTSService
from modules.intent_classifier import IntentClassifier
from modules.tool_selector import ToolSelector
from modules.user_manager import UserManager
from modules.multimodal_perception import MultimodalPerception
from modules.memory import ConversationMemory
from modules.response_condenser import condense_response
from utils.audio_player import AudioPlayer

EXIT_KEYWORDS = ["任务结束", "结束任务", "结束对话", "对话结束", "退出对话", "再见", "拜拜"]

NAME_EXTRACT_PROMPT = (
    "请从以下用户语音中提取用户的名字，只返回名字本身（2-10个字），不要有任何其他内容。"
    "如果无法确定名字，返回'未知'。"
)


class Pipeline:
    """交互系统主流程"""

    def __init__(self):
        if USE_PROCESS_SERVICES:
            from services.process_service import ServiceProxy
            self._voiceprint = VoiceprintService()
            self._llm = LLMService()
            self._asr = ServiceProxy(ASRService)
            self._tts = ServiceProxy(TTSService)
        else:
            self._voiceprint = VoiceprintService()
            self._llm = LLMService()
            self._asr = ASRService()
            self._tts = TTSService()

        self._intent = IntentClassifier()
        self._tool_selector = ToolSelector()
        self._user_mgr = UserManager()
        self._perception = MultimodalPerception()
        self._memory = ConversationMemory()
        self._audio_player = AudioPlayer()
        self._has_greeted = False
        self._has_voice_greeted = False
        self._awaiting_name = False
        self._pending_audio = None
        self._exit_requested = False

    @property
    def has_greeted(self):
        return self._has_greeted

    def reset_greeting(self):
        """重置打招呼状态，下次唤醒时会重新打招呼"""
        self._has_greeted = False
        self._has_voice_greeted = False
        self._awaiting_name = False
        self._pending_audio = None
        self._exit_requested = False
        self._memory = ConversationMemory()

    def is_exit_requested(self):
        return self._exit_requested

    def quick_detect_person(self, image_path: str) -> bool:
        """快速检测图像中是否有人（仅YOLO，不调用大模型）"""
        return self._perception.detect_person_only(image_path)

    def try_greet(self, image_path=None, image_url=None):
        """
        检测图像中的人物并生成打招呼内容，设置 _has_greeted 标志
        Returns:
            (是否检测到人, 打招呼文本)
        """
        person_detected, greet_msg = self._perception.detect_and_greet(
            image_path=image_path, image_url=image_url
        )
        if person_detected:
            self._has_greeted = True
        return person_detected, greet_msg

    def speak(self, text):
        """合成并播放语音"""
        try:
            self._tts.synthesize(text, TEMP_TTS_OUTPUT_PATH)
            self._audio_player.play(TEMP_TTS_OUTPUT_PATH)
        except Exception as e:
            print(f"[语音播放] 失败: {e}")

    def warm_up_all(self):
        """并行预热所有服务"""
        print("=" * 50)
        print("开始预热所有模块...")
        t0 = time.time()

        targets = [
            self._voiceprint.warm_up,
            self._llm.warm_up,
            self._asr.warm_up,
            self._tts.warm_up,
            self._intent.warm_up,
        ]

        threads = [threading.Thread(target=fn) for fn in targets]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print(f"所有模块预热完成，总耗时: {time.time() - t0:.2f}s")
        print("=" * 50)

    def run(
        self,
        audio_path: Optional[str] = None,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> str:
        """
        执行一次完整交互
        Args:
            audio_path: 用户语音文件路径
            image_path: 摄像头图像路径
            image_url: 摄像头图像URL
        Returns:
            系统响应文本
        """
        total_t0 = time.time()
        print("\n" + "=" * 50)
        print("开始处理交互...")

        # ====== 步骤1: 多模态感知（图像识人+打招呼，仅首次） ======
        person_detected, greet_msg = False, ""
        if not self._has_greeted:
            person_detected, greet_msg = self._perception.detect_and_greet(
                image_path=image_path, image_url=image_url
            )
            if person_detected:
                self._has_greeted = True

        # ====== 步骤2: 并行执行声纹识别 + ASR ======
        username = None
        asr_text = ""

        if audio_path and os.path.exists(audio_path):
            username, asr_text = self._parallel_voice_asr(audio_path)

        # ====== 步骤3: 用户认证处理 ======
        is_new_user = False
        just_registered = False
        user_profile = {}

        if username:
            user_profile = self._user_mgr.load_user_profile(username)
            print(f"[流程] 已识别用户: {username}")
            self._awaiting_name = False
            self._pending_audio = None
        elif audio_path:
            if self._awaiting_name and asr_text:
                extracted_name = self._extract_name(asr_text)
                if extracted_name:
                    username = extracted_name
                    is_new_user = False
                    just_registered = True
                    self._user_mgr.register_new_user(audio_path, username)
                    user_profile = self._user_mgr.load_user_profile(username)
                    print(f"[流程] 新用户注册完成: {username}")
                    self._awaiting_name = False
                    self._pending_audio = None
                else:
                    is_new_user = True
                    self._pending_audio = audio_path
                    print("[流程] 未能提取用户名字，将继续询问")
            else:
                is_new_user = True
                self._awaiting_name = True
                self._pending_audio = audio_path
                print("[流程] 未识别到注册用户")

        # ====== 步骤4: 构建系统提示词 ======
        system_prompt = self._build_system_prompt(username, user_profile, is_new_user)

        # ====== 组装前缀部分（打招呼 + 用户问候） ======
        prefix_parts: List[str] = []
        if person_detected and greet_msg:
            prefix_parts.append(greet_msg)
        if username and not is_new_user:
            if just_registered:
                prefix_parts.append(f"{username}，你好！很高兴认识你！")
                self._has_voice_greeted = True
            elif not self._has_voice_greeted:
                prefix_parts.append(f"又见面了{username}")
                self._has_voice_greeted = True

        # ====== 步骤5: 意图分类与响应生成 ======
        response = ""
        used_streaming = False

        if asr_text:
            self._memory.add_turn("user", asr_text)

            if self._is_exit_command(asr_text):
                response = self._handle_exit(username)
                self._memory.add_turn("assistant", response)
                try:
                    self._tts.synthesize(response, TEMP_TTS_OUTPUT_PATH)
                    self._audio_player.play(TEMP_TTS_OUTPUT_PATH)
                except Exception as e:
                    print(f"[TTS播放] 失败: {e}")
                elapsed = time.time() - total_t0
                print(f"\n交互完成 | 总耗时: {elapsed:.2f}s")
                print(f"响应: {response}")
                print("=" * 50)
                return response

            _, _, is_task = self._intent.classify(asr_text)

            if is_task:
                response = self._handle_task(asr_text, system_prompt, username)
            elif STREAMING_ENABLED:
                try:
                    response = self._handle_chat_streaming(
                        asr_text, system_prompt, prefix_parts
                    )
                    used_streaming = True
                except Exception as e:
                    print(f"[流式处理] 失败，回退到非流式模式: {e}")
                    response = self._handle_chat(asr_text, system_prompt)
            else:
                response = self._handle_chat(asr_text, system_prompt)

            self._memory.add_turn("assistant", response)

        # ====== 步骤6-8: 非流式路径（合成+播放） ======
        if not used_streaming:
            parts = prefix_parts[:]
            if response:
                parts.append(response)
            final_response = " ".join(parts) if parts else "我没有听清楚，请再说一遍。"

            if final_response:
                try:
                    self._tts.synthesize(final_response, TEMP_TTS_OUTPUT_PATH)
                    self._audio_player.play(TEMP_TTS_OUTPUT_PATH)
                except Exception as e:
                    print(f"[TTS播放] 失败: {e}")
        else:
            parts = prefix_parts[:]
            if response:
                parts.append(response)
            final_response = " ".join(parts) if parts else ""

        # ====== 步骤7: 任务完成后用LLM总结更新用户画像 ======
        if username:
            prefs = self._memory.extract_preferences()
            history = self._memory.get_history()
            self._user_mgr.summarize_and_update(
                username, history, prefs if prefs else {}
            )
        elif is_new_user:
            pass

        elapsed = time.time() - total_t0
        print(f"\n交互完成 | 总耗时: {elapsed:.2f}s")
        print(f"响应: {final_response}")
        print("=" * 50)

        return final_response

    def _parallel_voice_asr(self, audio_path: str):
        """并行执行声纹识别和ASR"""
        vp_queue = queue.Queue()
        asr_queue = queue.Queue()

        def do_voiceprint():
            user, score = self._voiceprint.recognize(audio_path)
            vp_queue.put((user, score))

        def do_asr():
            text = self._asr.transcribe(audio_path)
            asr_queue.put(text)

        t_vp = threading.Thread(target=do_voiceprint)
        t_asr = threading.Thread(target=do_asr)

        t_vp.start()
        t_asr.start()
        t_vp.join()
        t_asr.join()

        username, vp_score = vp_queue.get()
        asr_text = asr_queue.get()

        return username, asr_text

    def _build_system_prompt(
        self,
        username: Optional[str],
        user_profile: Dict[str, str],
        is_new_user: bool,
    ) -> str:
        """构建系统提示词"""
        prompt = "你是一个智能机器人助手，回复要简短亲切，控制在80字以内。"

        if username and not is_new_user:
            prompt += f"\n当前用户是{username}。"
            if user_profile:
                if user_profile.get("summary"):
                    prompt += f"\n用户画像：{user_profile['summary']}"
                else:
                    pref_str = "；".join(
                        f"{k}:{v}" for k, v in user_profile.items()
                        if k not in ("注册时间", "最后更新")
                    )
                    if pref_str:
                        prompt += f"\n用户偏好：{pref_str}"

        if is_new_user:
            prompt += "\n这是一位新用户，请先询问用户的名字。"

        return prompt

    def _handle_task(self, user_input: str, system_prompt: str, username: Optional[str]) -> str:
        """处理任务执行类意图"""
        tool_result = self._tool_selector.select(user_input)

        cap = tool_result.get("capability", "")
        tool_name = tool_result.get("tool_name", "")

        response = f"好的，下面我将执行{cap}任务：{tool_name}"

        if username:
            self._user_mgr.update_user_profile(username, {
                "常用指令": user_input,
                "最后任务": f"{cap}/{tool_name}",
            })

        return response

    def _handle_chat(self, user_input: str, system_prompt: str) -> str:
        """处理闲聊类意图（非流式）"""
        messages = self._memory.get_messages(system_prompt)
        raw_response = self._llm.chat(messages)
        return condense_response(raw_response)

    def _handle_chat_streaming(
        self,
        user_input: str,
        system_prompt: str,
        prefix_parts: List[str],
    ) -> str:
        """
        流式处理：LLM流式输出 → 按句TTS合成 → 即时播放
        大幅降低首次响应延迟（首句音频在LLM输出第一句时即可播放）
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            prefix_parts: 前缀文本列表（打招呼、用户问候等）
        Returns:
            完整的LLM响应文本
        """
        t0 = time.time()
        messages = self._memory.get_messages(system_prompt)

        audio_queue: queue.Queue = queue.Queue()

        playback_thread = threading.Thread(
            target=self._audio_player.play_stream,
            args=(audio_queue, TTS_SAMPLE_RATE),
            daemon=True,
        )
        playback_thread.start()

        for part in prefix_parts:
            try:
                audio_data, sr = self._tts.synthesize_to_data(part)
                audio_queue.put((audio_data, sr))
            except Exception as e:
                print(f"[流式TTS] 前缀合成失败: {e}")

        full_response = ""

        try:
            for token in self._llm.chat_stream(messages, max_tokens=STREAMING_MAX_TOKENS):
                full_response += token
        except Exception as e:
            print(f"[流式LLM] 流式输出异常: {e}")

        if full_response.strip():
            try:
                audio_data, sr = self._tts.synthesize_to_data(full_response.strip())
                audio_queue.put((audio_data, sr))
            except Exception as e:
                print(f"[流式TTS] 全句合成失败: {e}")

        audio_queue.put(None)
        playback_thread.join(timeout=30)

        print(f"[流式处理] 完成 | 响应: {full_response[:50]}... | 耗时: {time.time() - t0:.2f}s")
        return full_response

    def register_new_user(self, audio_path: str, username: str):
        """手动注册新用户"""
        self._user_mgr.register_new_user(audio_path, username)

    def _extract_name(self, text: str) -> Optional[str]:
        patterns = [
            r"我叫([^\s，。,.！!？?]{1,10})",
            r"我的名字是([^\s，。,.！!？?]{1,10})",
            r"我是([^\s，。,.！!？?]{1,10})",
            r"叫我([^\s，。,.！!？?]{1,10})",
            r"名字是([^\s，。,.！!？?]{1,10})",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()

        try:
            messages = [
                {"role": "system", "content": NAME_EXTRACT_PROMPT},
                {"role": "user", "content": text},
            ]
            result = self._llm.chat(messages, max_tokens=20).strip()
            result = result.strip('"\'""\'')
            if result and result not in ("未知", "无法确定", "无", "没有"):
                return result
        except Exception:
            pass
        return None

    def _is_exit_command(self, text: str) -> bool:
        for kw in EXIT_KEYWORDS:
            if kw in text:
                return True
        return False

    def _handle_exit(self, username: Optional[str]) -> str:
        self._exit_requested = True
        if username:
            prefs = self._memory.extract_preferences()
            history = self._memory.get_history()
            self._user_mgr.summarize_and_update(
                username, history, prefs if prefs else {}
            )
            print(f"[流程] 用户画像已保存: {username}")
        return "好的，任务结束。再见！"
