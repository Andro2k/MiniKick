# backend\utils\io_background.py

import logging
import queue
import threading
import time
from typing import Any, Callable

logger = logging.getLogger("minikick.utils.io_background")

_DROP_WARN_INTERVAL_S = 30.0


class BoundedBackgroundWorker:
    def __init__(self, name: str, max_pending: int = 200) -> None:
        self._name = name
        self._queue: queue.Queue = queue.Queue(maxsize=max_pending)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._dropped = 0
        self._last_drop_warning = 0.0

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        self._ensure_thread()
        try:
            self._queue.put_nowait((fn, args, kwargs))
            return True
        except queue.Full:
            self._report_drop(fn)
            return False

    def flush(self, timeout: float = 3.0) -> bool:
        deadline = time.monotonic() + timeout
        with self._queue.all_tasks_done:
            while self._queue.unfinished_tasks:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._queue.all_tasks_done.wait(remaining)
        return True

    def _ensure_thread(self) -> None:
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name=self._name, daemon=True)
                self._thread.start()

    def _run(self) -> None:
        while True:
            fn, args, kwargs = self._queue.get()
            try:
                fn(*args, **kwargs)
            except Exception as e:
                logger.error("[%s] Job failed (%s): %s", self._name, getattr(fn, "__name__", fn), e)
            finally:
                self._queue.task_done()

    def _report_drop(self, fn: Callable[..., Any]) -> None:
        self._dropped += 1
        now = time.monotonic()
        if now - self._last_drop_warning >= _DROP_WARN_INTERVAL_S:
            self._last_drop_warning = now
            logger.warning(
                "[%s] Backlog full; dropped %d job(s) so far (latest: %s).",
                self._name, self._dropped, getattr(fn, "__name__", fn),
            )


_network_worker = BoundedBackgroundWorker("NetworkIOWorker", max_pending=200)


def submit_network_io(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
    return _network_worker.submit(fn, *args, **kwargs)


def flush_network_io(timeout: float = 3.0) -> bool:
    return _network_worker.flush(timeout)
