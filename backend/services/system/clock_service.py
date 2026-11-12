# backend\services\system\clock_service.py

import re
import time
from typing import Callable, Optional

_UNIT_MS = {"h": 3_600_000, "m": 60_000, "s": 1_000}
_UNITS_RE = re.compile(r"^(?:\d+[hms])+$")
_PART_RE = re.compile(r"(\d+)([hms])")


def parse_duration(text: str) -> Optional[int]:
    text = text.strip().lower()
    if text.isdigit():
        return int(text) * 1000 or None
    if ":" in text:
        parts = text.split(":")
        if not 2 <= len(parts) <= 3 or not all(p.isdigit() for p in parts):
            return None
        seconds = 0
        for p in parts:
            seconds = seconds * 60 + int(p)
        return seconds * 1000 or None
    if _UNITS_RE.match(text):
        return sum(int(n) * _UNIT_MS[u] for n, u in _PART_RE.findall(text)) or None
    return None


class _ElapsedClock:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._base_ms = 0
        self._anchor: Optional[float] = None

    @property
    def running(self) -> bool:
        return self._anchor is not None

    def elapsed_ms(self) -> int:
        extra = int((self._clock() - self._anchor) * 1000) if self.running else 0
        return self._base_ms + extra

    def start(self) -> None:
        if not self.running:
            self._anchor = self._clock()

    def pause(self) -> None:
        if self.running:
            self._base_ms = self.elapsed_ms()
            self._anchor = None

    def reset(self) -> None:
        self._base_ms = 0
        self._anchor = None


class CountdownTimer:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._elapsed = _ElapsedClock(clock)
        self._total_ms = 0
        self._label = ""
        self._active = False

    def start(self, duration_ms: int, label: str = "") -> None:
        self._elapsed.reset()
        self._elapsed.start()
        self._total_ms, self._label, self._active = duration_ms, label, True

    def pause(self) -> None:
        self._elapsed.pause()

    def resume(self) -> None:
        if self._active:
            self._elapsed.start()

    def stop(self) -> None:
        self._elapsed.reset()
        self._active = False

    def snapshot(self) -> dict:
        remaining = max(0, self._total_ms - self._elapsed.elapsed_ms())
        if not self._active:
            status = "stopped"
        elif remaining == 0:
            status = "finished"
        else:
            status = "running" if self._elapsed.running else "paused"
        return {"status": status, "remaining_ms": remaining, "total_ms": self._total_ms, "label": self._label}


class Stopwatch:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._elapsed = _ElapsedClock(clock)
        self._active = False

    def start(self) -> None:
        self._elapsed.start()
        self._active = True

    def pause(self) -> None:
        self._elapsed.pause()

    def reset(self) -> None:
        self._elapsed.reset()
        self._active = False

    def snapshot(self) -> dict:
        if not self._active:
            status = "stopped"
        else:
            status = "running" if self._elapsed.running else "paused"
        return {"status": status, "elapsed_ms": self._elapsed.elapsed_ms()}
