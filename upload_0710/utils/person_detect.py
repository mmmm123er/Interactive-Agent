import cv2
import time
from threading import Thread
from ultralytics import YOLO

# 1. 加载极轻量视觉过滤模型（在 GPU 上推理仅需约 5ms）
print("正在后台启动视觉感应系统...")
detector = YOLO("yolov8n.pt")

CAMERA_INDEX = 0  # 摄像头 ID
TEMP_CAPTURE_PATH = "captured_person.jpg"  # 触发时保存的抓图路径


# 2. 异步处理函数：感应到人后，在后台调用大模型和 TTS
def async_visual_understanding(image_path):
    print("⚡ [触发成功] 检测到新人，后台开始请求多模态大模型和 TTS...")
    t0 = time.time()
    try:
        # 这里放置你之前写好的多模态大模型 API 和 TTS 播放代码
        # text = call_vlm_api(image_path)
        # play_tts(text)

        # 模拟 500ms 大模型加语音合成延迟
        time.sleep(0.5)
        print(f"🎙️ [系统响应完毕] 总耗时: {time.time() - t0:.2f}s")

    except Exception as e:
        print(f"大模型或 TTS 调用失败: {e}")


# 3. 核心：后台视频流感应循环
def run_background_detection_loop():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"无法打开摄像头 (Index={CAMERA_INDEX})")
        return

    print("\n" + "=" * 40)
    print("👁️ 视觉感应系统已就绪，正在静默监控视频流...")
    print("=" * 40)

    person_present = False  # 状态锁：记录上一次检测是否有人
    last_detection_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("无法获取视频帧，请检查相机连接。")
                time.sleep(1)
                continue

            current_time = time.time()

            # 【性能优化】每 100ms（每秒10帧）用 YOLO 扫描一次，兼顾实时性与极低的算力消耗
            if current_time - last_detection_time > 0.1:
                last_detection_time = current_time

                # 极速预测（指定在 GPU 运行）
                results = detector(frame, verbose=False, device="cuda:0")

                # 仅判断当前帧类别中是否有人（Class 0 代表 person）
                has_person = False
                for r in results:
                    if 0 in r.boxes.cls.tolist():
                        has_person = True
                        break

                # 状态机逻辑
                if has_person and not person_present:
                    # 状态突变：没人 -> 有人
                    print("\n🔔 [状态变更] 画面中出现用户！")
                    person_present = True

                    # 抓拍当前帧并保存
                    cv2.imwrite(TEMP_CAPTURE_PATH, frame)

                    # 启动后台旁路线程，绝对不阻塞视频流读取
                    Thread(target=async_visual_understanding, args=(TEMP_CAPTURE_PATH,), daemon=True).start()

                elif not has_person and person_present:
                    # 状态突变：有人 -> 没人
                    print("\n🔕 [状态变更] 用户离开。系统已重置，等待下一个人...")
                    person_present = False

    except KeyboardInterrupt:
        print("\n检测被用户手动终止。")
    finally:
        cap.release()
        print("摄像头资源已释放。")


if __name__ == "__main__":
    run_background_detection_loop()