# import cv2
# from config import CAMERA_INDEX, TEMP_IMAGE_PATH
#
#
# def capture_from_camera_live():
#     try:
#         # 1. 打开摄像头
#         cap = cv2.VideoCapture(1)
#         if not cap.isOpened():
#             print(f"无法打开摄像头 (index={CAMERA_INDEX})")
#             return None
#
#         print("进入实时预览模式。")
#         print("提示：[按下 空格键] 拍照并保存")
#         print("提示：[按下 Esc 键] 取消并退出")
#
#         saved_path = None
#
#         # 2. 循环读取帧，实现视频动起来的效果
#         while True:
#             ret, frame = cap.read()
#             if not ret or frame is None:
#                 print("无法获取摄像头画面")
#                 break
#
#             # 实时显示当前帧
#             cv2.imshow("Live Camera (Space to Capture, Esc to Exit)", frame)
#
#             # 每隔 1 毫秒检测一次按键
#             key = cv2.waitKey(1) & 0xFF
#
#             # 如果按下 Esc 键 (ASCII 码 27)，退出不保存
#             if key == 27:
#                 print("取消拍照。")
#                 break
#
#             # 如果按下 空格键 (ASCII 码 32)，拍照保存并退出
#             elif key == 32:
#                 cv2.imwrite(TEMP_IMAGE_PATH, frame)
#                 saved_path = TEMP_IMAGE_PATH
#                 print(f"拍照成功！图片已保存至: {saved_path}")
#                 break
#
#         # 3. 释放摄像头并销毁窗口
#         cap.release()
#         cv2.destroyAllWindows()
#         return saved_path
#
#     except Exception as e:
#         print(f"摄像头运行失败: {e}")
#         return None
#
#
# if __name__ == "__main__":
#     capture_from_camera_live()


import wave
import pyaudio


def record_audio(output_filename, duration=5, sample_rate=16000, channels=1):
    """录制音频并保存为 WAV 文件

    参数:
    - output_filename: 保存的文件名 (例如 'output.wav')
    - duration: 录音时长（秒）
    - sample_rate: 采样率，44100Hz 是 CD 级音质
    - channels: 声道数，1 为单声道，2 为双声道
    """
    chunk = 1024  # 每个缓冲区的帧数
    audio_format = pyaudio.paInt16  # 16位深

    p = pyaudio.PyAudio()

    # 打开录音流
    stream = p.open(
        format=audio_format,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk,
        # input_device_index=5
    )

    print(f"🎤 开始录音，请说话... (限时 {duration} 秒)")

    frames = []

    # 循环读取音频数据
    for _ in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("🛑 录音结束，正在保存...")

    # 停止和关闭录音流
    stream.stop_stream()
    stream.close()
    p.terminate()

    # 保存为 WAV 文件
    with wave.open(output_filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(audio_format))
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))

    print(f"💾 音频已成功保存为: {output_filename}")


if __name__ == "__main__":
    # 设定保存的文件名和录音时长（比如录制 8 秒）
    output_file = "my_record.wav"
    record_time = 8

    record_audio(output_file, duration=record_time)


# import pyaudio
# p = pyaudio.PyAudio()
# for i in range(p.get_device_count()):
#     dev = p.get_device_info_by_index(i)
#     if dev['maxInputChannels'] > 0:
#         print(f"🎤 发现可用麦克风 -> 设备 ID: {i}, 名称: {dev['name']}, 支持通道数: {dev['maxInputChannels']}")
# p.terminate()
