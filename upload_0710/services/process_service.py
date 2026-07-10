"""
多进程服务代理模块
将ASR/TTS等服务部署为独立进程，避免GIL争用，提升并行性能
"""
import torch.multiprocessing as mp
from typing import Any


class ServiceProxy:
    """服务代理：将服务运行在独立进程中，通过队列通信"""

    def __init__(self, service_class):
        self._service_class = service_class
        self._request_queue = None
        self._response_queue = None
        self._process = None

    def warm_up(self):
        ctx = mp.get_context('spawn')
        self._request_queue = ctx.Queue()
        self._response_queue = ctx.Queue()
        self._process = ctx.Process(
            target=self._worker,
            args=(self._service_class, self._request_queue, self._response_queue),
            daemon=True,
        )
        self._process.start()
        self._call('warm_up')
        print(f"[进程服务] {self._service_class.__name__} 已在独立进程中启动")

    @staticmethod
    def _worker(service_class, request_queue, response_queue):
        import os
        os.environ["http_proxy"] = ""
        os.environ["https_proxy"] = ""
        os.environ["all_proxy"] = ""

        service = service_class()
        while True:
            msg = request_queue.get()
            if msg[0] is None:
                break
            method_name, args, kwargs = msg
            try:
                method = getattr(service, method_name)
                result = method(*args, **kwargs)
                response_queue.put(('ok', result))
            except Exception as e:
                response_queue.put(('error', str(e)))

    def _call(self, method_name: str, *args, **kwargs) -> Any:
        self._request_queue.put((method_name, args, kwargs))
        status, result = self._response_queue.get()
        if status == 'error':
            raise RuntimeError(f"进程服务调用失败: {result}")
        return result

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        def proxy_method(*args, **kwargs):
            return self._call(name, *args, **kwargs)
        return proxy_method

    def stop(self):
        if self._request_queue:
            self._request_queue.put((None, None, None))
        if self._process:
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.terminate()

    def __del__(self):
        self.stop()
