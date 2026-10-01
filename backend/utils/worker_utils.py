# backend\utils\worker_utils.py

import logging
import random

logger = logging.getLogger("minikick.utils.worker_utils")

def stop_provider_chat_worker(worker, provider, target_logger: logging.Logger, worker_tag: str, target: str) -> None:
    target_logger.info("[%s] Stopping chat worker for '%s'...", worker_tag, target)
    worker._is_stopped = True
    worker.requestInterruption()
    if provider and hasattr(provider, "stop_chat"):
        provider.stop_chat()
    worker.quit()

class ExponentialBackoff:
    def __init__(
        self,
        initial: float = 1.0,
        max_backoff: float = 30.0,
        factor: float = 2.0,
        jitter: float = 0.2
    ) -> None:
        self.initial = initial
        self.max_backoff = max_backoff
        self.factor = factor
        self.jitter = jitter
        self._current: float = initial
        self._attempts: int = 0

    def next_delay(self) -> float:
        delay = self._current
        jitter_range = delay * self.jitter
        adjusted_delay = delay + random.uniform(-jitter_range, jitter_range)
        adjusted_delay = max(0.1, min(self.max_backoff, adjusted_delay))

        self._current = min(self.max_backoff, self._current * self.factor)
        self._attempts += 1
        return adjusted_delay

    def reset(self) -> None:
        self._current = self.initial
        self._attempts = 0

    @property
    def attempts(self) -> int:
        return self._attempts
