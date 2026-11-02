# backend\utils\perf.py\

import logging
import time
from contextlib import contextmanager


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


@contextmanager
def perf_phase(logger: logging.Logger, scope: str, label: str, level: int = logging.INFO):
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.log(level, "[Perf/%s] %s in %.2f ms", scope, label, elapsed_ms(start))