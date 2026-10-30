# backend\services\system\log_writer.py

import logging
import queue
import sys
import threading
import time
from typing import Callable

logger = logging.getLogger("minikick.services.log_writer")

_STOP = object()

class BatchedLogWriter:
    def __init__(
        self,
        write_batch: Callable[[list], None],
        flush_interval_s: float = 0.25,
        max_batch: int = 200,
    ) -> None:
        self._write_batch = write_batch
        self._flush_interval_s = flush_interval_s
        self._max_batch = max_batch
        self._queue: queue.Queue = queue.Queue()
        self._wake = threading.Event()
        self._state_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._closed = False

    def submit(self, record) -> None:
        with self._state_lock:
            if self._closed:
                return
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name="LogBatchWriter", daemon=True)
                self._thread.start()
            self._queue.put(record)

    def flush(self, timeout: float = 2.0) -> bool:
        self._wake.set()
        deadline = time.monotonic() + timeout
        with self._queue.all_tasks_done:
            while self._queue.unfinished_tasks:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._queue.all_tasks_done.wait(remaining)
        return True

    def close(self, timeout: float = 2.0) -> None:
        with self._state_lock:
            if self._closed:
                return
            self._closed = True
            thread = self._thread
            if thread is not None:
                self._queue.put(_STOP)
        self._wake.set()
        if thread is not None:
            thread.join(timeout)

    def _run(self) -> None:
        stopping = False
        while not stopping:
            batch = [self._queue.get()]
            self._wake.wait(self._flush_interval_s)
            self._wake.clear()
            while len(batch) < self._max_batch:
                try:
                    batch.append(self._queue.get_nowait())
                except queue.Empty:
                    break

            records = [item for item in batch if item is not _STOP]
            stopping = len(records) != len(batch)
            self._write(records)
            for _ in batch:
                self._queue.task_done()

    def _write(self, records: list) -> None:
        if not records:
            return
        try:
            self._write_batch(records)
        except Exception as err:
            if sys.__stderr__ is not None:
                try:
                    sys.__stderr__.write(f"[LogBatchWriter] Could not persist {len(records)} log records: {err}\n")
                except Exception:
                    pass
