from __future__ import annotations

import logging
import time
from collections import deque
from collections.abc import Callable, Iterable

from PySide6.QtCore import QTimer


class StartupSequencer:
    WHATS_NEW_DELAY_MS = 750
    PREWARM_DELAY_MS = 300
    DATABASE_MAINTENANCE_DELAY_MS = 10_000
    INITIAL_HYDRATION_DELAY_MS = 50
    NEXT_HYDRATION_DELAY_MS = 16

    def __init__(
        self,
        logger: logging.Logger,
        is_active: Callable[[], bool],
        whats_new_check: Callable[[], None],
        prewarm_views: Callable[[int], None],
        start_database_maintenance: Callable[[], None],
        schedule: Callable[[int, Callable[[], None]], None] = QTimer.singleShot,
    ) -> None:
        self._logger = logger
        self._is_active = is_active
        self._whats_new_check = whats_new_check
        self._prewarm_views = prewarm_views
        self._start_database_maintenance = start_database_maintenance
        self._schedule = schedule
        self._steps: deque[tuple[str, Callable[[], None]]] = deque()

    def start(self, steps: Iterable[tuple[str, Callable[[], None]]]) -> None:
        self._steps = deque(steps)
        self._schedule(self.INITIAL_HYDRATION_DELAY_MS, self._run_next)

    def _run_next(self) -> None:
        if not self._is_active() or not self._steps:
            return

        step_name, step = self._steps.popleft()
        step_started = time.perf_counter()
        try:
            step()
        except Exception:
            self._logger.exception("[Startup] Hydration phase '%s' failed.", step_name)
        else:
            self._logger.info(
                "[Perf/Startup] Hydration phase '%s' completed in %.2f ms",
                step_name,
                (time.perf_counter() - step_started) * 1000,
            )

        if self._steps:
            self._schedule(self.NEXT_HYDRATION_DELAY_MS, self._run_next)
        else:
            self._schedule_followups()

    def _schedule_followups(self) -> None:
        self._schedule(self.WHATS_NEW_DELAY_MS, self._whats_new_check)
        self._prewarm_views(self.PREWARM_DELAY_MS)
        self._schedule(
            self.DATABASE_MAINTENANCE_DELAY_MS,
            self._start_database_maintenance,
        )
