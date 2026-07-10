"""音频录制模块"""
import pyaudio
import wave
import time
import threading
from config import AUDIO_SAMPLE_RATE, SILENCE_TIMEOUT, SILENCE_THRESHOLD
import numpy as np


class AudioRecorder:
    def __init__(self, sample_rate=AUDIO_SAMPLE_RATE, channels=1, format=pyaudio.paInt16):
        """
        初始化音频录制器
        Args:
            sample_rate: 采样率
            channels: 声道数
            format: 音频格式
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()

    def _calc_volume(self, data):
        audio_data = np.frombuffer(data, dtype=np.int16)
        return np.linalg.norm(audio_data) / len(audio_data)

    def _trim_silence(self, frames, threshold):
        start = 0
        end = len(frames) - 1

        while start < len(frames):
            if self._calc_volume(frames[start]) >= threshold:
                break
            start += 1

        while end > start:
            if self._calc_volume(frames[end]) >= threshold:
                break
            end -= 1

        padding = int((0.1 * self.sample_rate) / self.chunk)
        start = max(0, start - padding)
        end = min(len(frames) - 1, end + padding)

        return frames[start:end + 1]

    def record_until_silence(self, output_path: str, silence_timeout: float = SILENCE_TIMEOUT,
                             max_duration: float = 30.0, frame_callback=None):
        """
        录制音频直到静音超时
        Args:
            output_path: 输出文件路径
            silence_timeout: 静音超时时间（秒），检测到语音后连续静音超过此时间则停止
            max_duration: 最大录音时长（秒）
            frame_callback: 每次循环调用的回调函数（用于在主线程更新GUI）
        """
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        print("开始录音，请说话...")

        frames = []
        silent_frames = 0
        speech_started = False
        max_silent_frames = int((silence_timeout * self.sample_rate) / self.chunk)
        max_total_frames = int((max_duration * self.sample_rate) / self.chunk)

        for i in range(max_total_frames):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

            if frame_callback:
                frame_callback()

            volume = self._calc_volume(data)

            if not speech_started:
                if volume >= SILENCE_THRESHOLD:
                    speech_started = True
                    silent_frames = 0
            else:
                if volume < SILENCE_THRESHOLD:
                    silent_frames += 1
                    if silent_frames >= max_silent_frames:
                        break
                else:
                    silent_frames = 0

        if not speech_started:
            print("未检测到语音")
            stream.stop_stream()
            stream.close()
            return None

        print("录音结束")

        stream.stop_stream()
        stream.close()

        trimmed = self._trim_silence(frames, SILENCE_THRESHOLD)

        wf = wave.open(output_path, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(trimmed))
        wf.close()

        print(f"音频已保存到: {output_path}")
        return output_path
    
    def record_fixed_duration(self, output_path: str, duration: float):
        """
        录制固定时长的音频
        Args:
            output_path: 输出文件路径
            duration: 录制时长（秒）
        """
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        print(f"开始录制 {duration} 秒音频...")

        frames = []
        total_frames = int(self.sample_rate / self.chunk * duration)

        for i in range(total_frames):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

        print("录制完成")

        stream.stop_stream()
        stream.close()

        wf = wave.open(output_path, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        print(f"音频已保存到: {output_path}")

    def __del__(self):
        """清理资源"""
        self.audio.terminate()


def record_audio_with_timeout(output_path: str, timeout: float = SILENCE_TIMEOUT):
    """
    使用全局函数录制音频
    Args:
        output_path: 输出文件路径
        timeout: 静音超时时间
    """
    recorder = AudioRecorder()
    return recorder.record_until_silence(output_path, timeout)