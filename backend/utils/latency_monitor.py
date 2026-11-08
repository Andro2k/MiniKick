# backend\utils\latency_monitor.py

import logging
import time
from collections import deque
from typing import Callable

logger = logging.getLogger("minikick.utils.latency")


def _percentile_95(samples) -> float:
    ordered = sorted(samples)
    if not ordered:
        return 0.0
    return ordered[int(0.95 * (len(ordered) - 1))]


class LatencyMonitor:
    def __init__(
        self,
        name: str,
        warn_threshold_s: float = 2.0,
        report_interval_s: float = 60.0,
        warn_cooldown_s: float = 30.0,
        window: int = 500,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._name = name
        self._warn_threshold_s = warn_threshold_s
        self._report_interval_s = report_interval_s
        self._warn_cooldown_s = warn_cooldown_s
        self._clock = clock
        self._samples: deque[float] = deque(maxlen=window)
        self._interval_count = 0
        self._interval_sum = 0.0
        self._interval_max: float | None = None
        self._last_report = clock()
        self._last_warn: float | None = None

    @property
    def p95(self) -> float:
        return _percentile_95(self._samples)

    def record(self, seconds: float, *, warn: bool = True) -> None:
        now = self._clock()
        self._samples.append(seconds)
        self._interval_count += 1
        self._interval_sum += seconds
        self._interval_max = seconds if self._interval_max is None else max(self._interval_max, seconds)

        if warn and seconds >= self._warn_threshold_s and (
            self._last_warn is None or now - self._last_warn >= self._warn_cooldown_s
        ):
            self._last_warn = now
            logger.warning(
                "[Latency/%s] Slow sample: %.2fs (threshold %.1fs, rolling p95 %.2fs over %d samples)",
                self._name, seconds, self._warn_threshold_s, self.p95, len(self._samples),
            )

        if now - self._last_report >= self._report_interval_s:
            self._report(now)

    def _report(self, now: float) -> None:
        if self._interval_count and self._interval_max is not None:
            logger.info(
                "[Latency/%s] Last %.0fs: n=%d avg=%.3fs p95=%.3fs max=%.3fs",
                self._name, now - self._last_report, self._interval_count,
                self._interval_sum / self._interval_count, self.p95, self._interval_max,
            )
        self._interval_count = 0
        self._interval_sum = 0.0
        self._interval_max = None
        self._last_report = now
