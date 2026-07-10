"""
音频播放工具
使用 PyAudio 播放 WAV 音频文件，支持流式播放
"""
import wave
import queue
import pyaudio
import numpy as np


class AudioPlayer:
    """音频播放器"""

    def __init__(self):
        self._pa = pyaudio.PyAudio()

    def play(self, wav_path: str, chunk_size: int = 1024):
        """
        播放 WAV 文件
        Args:
            wav_path: WAV 文件路径
            chunk_size: 每次读取的帧数
        """
        try:
            wf = wave.open(wav_path, 'rb')
            stream = self._pa.open(
                format=self._pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            data = wf.readframes(chunk_size)
            while data:
                stream.write(data)
                data = wf.readframes(chunk_size)

            stream.stop_stream()
            stream.close()
            wf.close()
        except Exception as e:
            print(f"[音频播放] 播放失败: {e}")

    def play_audio_data(self, audio_data: np.ndarray, sample_rate: int = 24000):
        """
        播放原始音频数据（numpy数组）
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
        """
        try:
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            stream = self._pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                output=True,
            )
            stream.write(audio_data.tobytes())
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[音频播放] 数据播放失败: {e}")

    def play_stream(self, audio_queue: queue.Queue, default_sample_rate: int = 24000):
        """
        从队列中逐段播放音频数据（流式播放）
        队列元素格式: (audio_data, sample_rate) 或 None（结束信号）
        Args:
            audio_queue: 音频数据队列
            default_sample_rate: 默认采样率
        """
        stream = None
        current_sr = default_sample_rate

        try:
            while True:
                try:
                    item = audio_queue.get(timeout=30)
                except queue.Empty:
                    print("[音频播放] 流式播放超时")
                    break

                if item is None:
                    break

                audio_data, sr = item

                if stream is None or sr != current_sr:
                    if stream is not None:
                        stream.stop_stream()
                        stream.close()
                    stream = self._pa.open(
                        format=pyaudio.paFloat32,
                        channels=1,
                        rate=sr,
                        output=True,
                    )
                    current_sr = sr

                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                stream.write(audio_data.tobytes())

        except Exception as e:
            print(f"[音频播放] 流式播放失败: {e}")
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()

    def __del__(self):
        if hasattr(self, '_pa') and self._pa:
            self._pa.terminate()
