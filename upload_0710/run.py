#!/usr/bin/env python3
"""
交互系统运行入口
支持命令行参数和交互式循环两种模式
"""
import sys
import os
import argparse
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.pipeline import Pipeline
from modules.wake_word_detector import WakeWordDetector
from utils.audio_recorder import AudioRecorder
from utils.camera_stream import CameraStream
from config import TEMP_AUDIO_PATH

_recorder = None


def _get_recorder():
    global _recorder
    if _recorder is None:
        _recorder = AudioRecorder()
    return _recorder


def record_from_microphone(frame_callback=None):
    try:
        recorder = _get_recorder()
        result = recorder.record_until_silence(TEMP_AUDIO_PATH, frame_callback=frame_callback)
        return result
    except Exception as e:
        print(f"话筒录音失败: {e}")
        return None


def main():
    global _recorder
    parser = argparse.ArgumentParser(description="对话和任务工具选择系统")
    parser.add_argument("--audio", type=str, help="音频文件路径")
    parser.add_argument("--image", type=str, help="图像文件路径")
    parser.add_argument("--interactive", action="store_true", help="进入交互式循环模式")
    parser.add_argument("--no-camera", action="store_true", help="禁用摄像头采集")
    args = parser.parse_args()

    pipeline = Pipeline()
    pipeline.warm_up_all()

    if args.interactive:
        print("\n进入交互模式（输入 quit 退出）")
        print("系统将通过唤醒词激活，请说\"哈喽\"唤醒")

        camera = None
        if not args.no_camera:
            camera = CameraStream()
            camera.start()

        wake_detector = WakeWordDetector()
        try:
            try:
                wake_detector.wait_for_wake_word()
            except KeyboardInterrupt:
                print("\n用户中断，退出")
                return

            print("\n[已唤醒] 进入对话模式，请说话...（说\"退出\"或\"任务结束\"结束对话）")

            while True:
                try:
                    audio_result = [None]
                    greeted_in_turn = [False]

                    def do_record():
                        audio_result[0] = record_from_microphone()

                    audio_thread = threading.Thread(target=do_record)
                    audio_thread.start()

                    if camera and not pipeline.has_greeted:
                        def detect_loop():
                            while audio_thread.is_alive() and not greeted_in_turn[0]:
                                frame_path = camera.get_latest_frame()
                                if frame_path and pipeline.quick_detect_person(frame_path):
                                    greeted_in_turn[0] = True
                                    greet_frame = camera.get_latest_frame()
                                    if greet_frame and not pipeline.has_greeted:
                                        def do_greet():
                                            person_detected, greet_msg = pipeline.try_greet(image_path=greet_frame)
                                            if person_detected and greet_msg:
                                                print(f"\n[打招呼] {greet_msg}")
                                                pipeline.speak(greet_msg)
                                        threading.Thread(target=do_greet, daemon=True).start()
                                    return
                                time.sleep(0.3)

                        detect_thread = threading.Thread(target=detect_loop, daemon=True)
                        detect_thread.start()

                    audio_thread.join()
                    audio = audio_result[0]

                    image = None
                    if camera:
                        image = camera.get_latest_frame()

                    if audio is None:
                        print("未能获取音频，请重试")
                        continue

                    response = pipeline.run(audio_path=audio, image_path=image)
                    print(f"\n系统响应: {response}")

                    if pipeline.is_exit_requested():
                        print("\n[对话结束] 用户偏好已保存，回到待机状态")
                        if camera:
                            camera.stop_display()
                        pipeline.reset_greeting()
                        break

                    if response and "退出" in response:
                        print("\n[对话结束] 回到待机状态")
                        if camera:
                            camera.stop_display()
                        pipeline.reset_greeting()
                        break

                    print("\n[请继续说话...]")

                except KeyboardInterrupt:
                    print("\n用户中断，退出")
                    if camera:
                        camera.stop_display()
                    break
        finally:
            del wake_detector
            if camera:
                camera.stop()

    elif args.audio:
        response = pipeline.run(audio_path=args.audio, image_path=args.image)
        print(f"\n系统响应: {response}")

    else:
        print("请指定 --audio 或使用 --interactive 模式")
        parser.print_help()

    if _recorder is not None:
        del _recorder


if __name__ == "__main__":
    main()
