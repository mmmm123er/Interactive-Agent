"""
多模态感知模块
使用 YOLO 目标检测小模型快速判断画面中是否有人，
检测到人物后再通过多模态大模型生成个性化打招呼内容
"""
import time
from typing import Optional, Tuple

import cv2
from ultralytics import YOLO

from config import YOLO_MODEL_PATH, YOLO_DEVICE, YOLO_CONFIDENCE_THRESHOLD
from services.llm_service import LLMService


GREET_SYSTEM_PROMPT = (
    "你是一个友好的机器人助手，正在通过摄像头观察用户。\n"
    "请根据图像描述，简短地向用户打招呼。\n"
    "要求：\n"
    "1. 识别用户的性别和大致年龄\n"
    "2. 可以夸赞用户的打扮或外表\n"
    "3. 询问有什么可以帮忙的\n"
    "4. 回复控制在30字以内，自然亲切\n"
    "只输出打招呼的话，不要输出分析过程。"
)


class MultimodalPerception:
    """多模态感知：YOLO 检测人 + 大模型生成打招呼"""

    def __init__(self):
        self._llm = LLMService()
        print("[多模态感知] 正在加载 YOLO 目标检测模型...")
        self._detector = YOLO(YOLO_MODEL_PATH)
        print("[多模态感知] YOLO 模型加载完成")

    def _detect_person(self, image_path: str) -> bool:
        """使用 YOLO 检测图像中是否有人（class 0 = person）"""
        frame = cv2.imread(image_path)
        if frame is None:
            print("[多模态感知] 无法读取图像，跳过检测")
            return False

        results = self._detector(frame, verbose=False, device=YOLO_DEVICE)
        for r in results:
            for cls_id, conf in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()):
                if int(cls_id) == 0 and conf >= YOLO_CONFIDENCE_THRESHOLD:
                    return True
        return False

    def detect_person_only(self, image_path: str) -> bool:
        """仅使用YOLO检测图像中是否有人，不调用大模型"""
        return self._detect_person(image_path)

    def detect_and_greet(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        检测图像中的人物并生成打招呼内容
        Args:
            image_path: 本地图像路径
            image_url: 图像URL
        Returns:
            (是否检测到人, 打招呼文本)
        """
        t0 = time.time()

        if not image_path and not image_url:
            print(f"[多模态感知] 无图像输入，跳过 | 耗时: {time.time() - t0:.2f}s")
            return False, ""

        if image_path:
            detected = self._detect_person(image_path)
        else:
            detected = True

        if not detected:
            print(f"[多模态感知] YOLO 未检测到人 | 耗时: {time.time() - t0:.2f}s")
            return False, ""

        result = self._llm.multimodal_chat(
            text=GREET_SYSTEM_PROMPT,
            image_url=image_url,
            image_path=image_path,
        )

        greet_text = result.strip() if result else ""
        print(f"[多模态感知] 检测到人: True | 耗时: {time.time() - t0:.2f}s")
        return True, greet_text
