import cv2
import threading
import time
from config import CAMERA_INDEX, CAMERA_WARMUP_FRAMES, TEMP_IMAGE_PATH


class CameraStream:
    def __init__(self, camera_index=CAMERA_INDEX):
        self._camera_index = camera_index
        self._cap = None
        self._running = False
        self._show_display = False
        self._latest_frame = None
        self._lock = threading.Lock()
        self._thread = None
        self._window_name = "Camera Live"

    def start(self):
        if self._running:
            return
        self._cap = cv2.VideoCapture(self._camera_index)
        if not self._cap.isOpened():
            print(f"无法打开摄像头 (index={self._camera_index})")
            return
        for _ in range(CAMERA_WARMUP_FRAMES):
            self._cap.read()
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        while self._running:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
            with self._lock:
                self._latest_frame = frame
            if self._show_display:
                cv2.imshow(self._window_name, frame)
                cv2.waitKey(1)

    def start_display(self):
        self._show_display = True

    def stop_display(self):
        self._show_display = False
        cv2.destroyAllWindows()

    def get_latest_frame(self):
        with self._lock:
            if self._latest_frame is None:
                return None
            frame = self._latest_frame.copy()
        cv2.imwrite(TEMP_IMAGE_PATH, frame)
        return TEMP_IMAGE_PATH

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
        self.stop_display()

    def __del__(self):
        self.stop()
