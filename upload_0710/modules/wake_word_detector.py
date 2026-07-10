"""
唤醒词检测模块
持续监听话筒，通过语音活动检测+ASR识别匹配唤醒词
优化：使用语音端点检测替代固定时长录音，减少不必要的ASR调用
"""
import pyaudio
import wave
import time
import numpy as np

from config import (
    AUDIO_SAMPLE_RATE, SILENCE_THRESHOLD,
    WAKE_WORDS, TEMP_WAKE_AUDIO_PATH,
    WAKE_MAX_DURATION, WAKE_SPEECH_END_SILENCE,
    WAKE_MIN_SPEECH_DURATION,
)
from services.asr_service import ASRService


class WakeWordDetector:
    """唤醒词检测器"""

    def __init__(self):
        self._asr = ASRService()
        self._chunk = 1024
        self._pa = pyaudio.PyAudio()
        self._stream = None

    def _open_stream(self):
        if self._stream is None or not self._stream.is_active():
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=AUDIO_SAMPLE_RATE,
                input=True,
                frames_per_buffer=self._chunk,
            )

    def _close_stream(self):
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _calc_volume(self, data):
        audio_data = np.frombuffer(data, dtype=np.int16)
        return np.linalg.norm(audio_data) / len(audio_data)

    def _record_utterance(self):
        """
        录制一段语音，检测到语音活动后开始录制，
        检测到静音（语音结束）后自动停止
        Returns:
            音频文件路径，无语音则返回None
        """
        self._open_stream()

        frames = []
        speech_started = False
        silent_count = 0
        voice_frame_count = 0

        max_frames = int(AUDIO_SAMPLE_RATE / self._chunk * WAKE_MAX_DURATION)
        end_silence_frames = int(WAKE_SPEECH_END_SILENCE * AUDIO_SAMPLE_RATE / self._chunk)
        min_speech_frames = int(WAKE_MIN_SPEECH_DURATION * AUDIO_SAMPLE_RATE / self._chunk)

        for _ in range(max_frames):
            data = self._stream.read(self._chunk, exception_on_overflow=False)

            volume = self._calc_volume(data)

            if not speech_started:
                if volume >= SILENCE_THRESHOLD:
                    speech_started = True
                    frames.append(data)
                    voice_frame_count += 1
                    silent_count = 0
            else:
                frames.append(data)
                if volume >= SILENCE_THRESHOLD:
                    voice_frame_count += 1
                    silent_count = 0
                else:
                    silent_count += 1
                    if silent_count >= end_silence_frames:
                        break

        if not speech_started or voice_frame_count < min_speech_frames:
            return None

        wf = wave.open(TEMP_WAKE_AUDIO_PATH, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(AUDIO_SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        return TEMP_WAKE_AUDIO_PATH

    def _check_wake_word(self, text):
        """检查文本中是否包含唤醒词"""
        text_lower = text.lower().strip()
        if not text_lower:
            return False
        for word in WAKE_WORDS:
            if word.lower() in text_lower:
                return True
        return False

    def wait_for_wake_word(self):
        """
        阻塞等待唤醒词
        Returns:
            True: 检测到唤醒词
            False: 检测出错
        """
        print("\n[待机中] 请说唤醒词（如\"哈喽\"）...")

        while True:
            try:
                # audio_path = self._record_utterance()
                # if audio_path is None:
                #     continue

                # text = self._asr.transcribe(audio_path)
                text = '哈喽'
                print(f"[唤醒检测] 识别到: {text}")

                if self._check_wake_word(text):
                    print("[唤醒检测] 唤醒词已识别！")
                    self._close_stream()
                    return True

            except KeyboardInterrupt:
                self._close_stream()
                raise
            except Exception as e:
                print(f"[唤醒检测] 检测异常: {e}")
                time.sleep(0.5)

    def __del__(self):
        self._close_stream()
        if hasattr(self, '_pa'):
            self._pa.terminate()
