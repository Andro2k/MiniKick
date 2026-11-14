# backend\utils\db_background_utils.py
"""Ejecutor en segundo plano para escrituras en la base de datos (envío y vaciado)."""

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable

logger = logging.getLogger("minikick.utils.db_background")

_executor: ThreadPoolExecutor | None = None
_lock = threading.Lock()
_pending: set[Future] = set()


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    with _lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="DbBackgroundWriter")
        return _executor


def submit_db_write(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future:
    future = _get_executor().submit(_run, fn, *args, **kwargs)
    with _lock:
        _pending.add(future)
    future.add_done_callback(_discard)
    return future


def _run(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    try:
        fn(*args, **kwargs)
    except Exception as e:
        logger.error("[DbBackgroundWriter] Write failed (%s): %s", getattr(fn, "__name__", fn), e)


def _discard(future: Future) -> None:
    with _lock:
        _pending.discard(future)


def flush_db_writes(timeout: float = 3.0) -> bool:
    with _lock:
        pending = list(_pending)
    for future in pending:
        try:
            future.result(timeout=timeout)
        except Exception:
            return False
    return True
