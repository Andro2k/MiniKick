# frontend\view_prewarmer.py

import logging
import time
from collections import deque
from typing import Callable, Iterable

logger = logging.getLogger("minikick.frontend.view_prewarmer")

class ViewPrewarmer:
    def __init__(
        self,
        create_view: Callable[[str], object],
        view_names: Iterable[str],
        is_created: Callable[[str], bool],
        is_active: Callable[[], bool],
        seconds_since_navigation: Callable[[], float],
        schedule: Callable[[int, Callable[[], None]], None],
        step_delay_ms: int = 150,
        busy_delay_ms: int = 600,
        idle_threshold_s: float = 0.6,
    ) -> None:
        self._create_view = create_view
        self._pending = deque(view_names)
        self._is_created = is_created
        self._is_active = is_active
        self._seconds_since_navigation = seconds_since_navigation
        self._schedule = schedule
        self._step_delay_ms = step_delay_ms
        self._busy_delay_ms = busy_delay_ms
        self._idle_threshold_s = idle_threshold_s
        self._started = False

    def start(self, initial_delay_ms: int = 0) -> None:
        if self._started:
            return
        self._started = True
        self._schedule(initial_delay_ms, self._step)

    def _step(self) -> None:
        if not self._is_active():
            return

        while self._pending and self._is_created(self._pending[0]):
            self._pending.popleft()
        if not self._pending:
            logger.info("[Perf/Prewarm] All views are ready.")
            return

        if self._seconds_since_navigation() < self._idle_threshold_s:
            self._schedule(self._busy_delay_ms, self._step)
            return

        view_name = self._pending.popleft()
        started = time.perf_counter()
        try:
            self._create_view(view_name)
        except Exception:
            logger.warning("[Perf/Prewarm] Could not prewarm view '%s'", view_name, exc_info=True)
        else:
            logger.info("[Perf/Prewarm] View '%s' prewarmed in %.2f ms", view_name, (time.perf_counter() - started) * 1000)
        self._schedule(self._step_delay_ms, self._step)
