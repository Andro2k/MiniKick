# frontend\window\session_metrics_tracker.py
"""Contadores de métricas de la sesión."""

import logging
import threading
from datetime import datetime
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from backend.utils.db_background_utils import submit_db_write

logger = logging.getLogger("minikick.core")


class SessionMetrics(QObject):
    refresh_requested = Signal()
    analytics_loaded = Signal(dict)
    _analytics_ready = Signal(object)

    PLATFORMS = ("kick", "twitch", "youtube", "tiktok")
    _REFRESH_DEBOUNCE_MS = 300
    _ANALYTICS_RERUN_DELAY_MS = 1500
    _HOURLY_FLUSH_INTERVAL_MS = 30_000

    def __init__(
        self,
        analytics_provider: Callable[[], dict],
        parent: QObject | None = None,
        hourly_sink: Callable[[dict], None] | None = None,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        super().__init__(parent)
        self._analytics_provider = analytics_provider
        self._hourly_sink = hourly_sink
        self._clock = clock
        self._hourly_buffer: dict[tuple[str, int, str], int] = {}
        self._hourly_lock = threading.Lock()
        self._hourly_timer = QTimer(self)
        self._hourly_timer.setInterval(self._HOURLY_FLUSH_INTERVAL_MS)
        self._hourly_timer.timeout.connect(self.flush_hourly_counts)
        if hourly_sink is not None:
            self._hourly_timer.start()
        self._messages_processed = 0
        self._spam_blocked = 0
        self._platform_messages = dict.fromkeys(self.PLATFORMS, 0)
        self._total_usages: int | None = None
        self._active_timers: int | None = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(self._REFRESH_DEBOUNCE_MS)
        self._refresh_timer.timeout.connect(self.refresh_requested.emit)
        self._analytics_inflight = False
        self._analytics_pending = False
        self._stopped = False
        self._analytics_ready.connect(self._on_analytics_ready)

    @property
    def messages_processed(self) -> int:
        return self._messages_processed

    @property
    def spam_blocked(self) -> int:
        return self._spam_blocked

    @property
    def total_usages(self) -> int:
        return self._total_usages or 0

    @property
    def active_timers(self) -> int:
        return self._active_timers or 0

    def platform_messages(self, platform: str) -> int:
        return self._platform_messages.get(platform, 0)

    def record_message(self, platform: str) -> None:
        self._messages_processed += 1
        if platform in self._platform_messages:
            self._platform_messages[platform] += 1
        if self._hourly_sink is not None:
            now = self._clock()
            key = (now.strftime("%Y-%m-%d"), now.hour, platform)
            with self._hourly_lock:
                self._hourly_buffer[key] = self._hourly_buffer.get(key, 0) + 1
        self._schedule_refresh()

    def flush_hourly_counts(self, *, sync: bool = False) -> None:
        """Envía a la base de datos los mensajes por hora acumulados; si falla, los conserva."""
        if self._hourly_sink is None:
            return
        with self._hourly_lock:
            if not self._hourly_buffer:
                return
            batch, self._hourly_buffer = self._hourly_buffer, {}
        if sync:
            self._write_hourly_batch(batch)
        else:
            submit_db_write(self._write_hourly_batch, batch)

    def _write_hourly_batch(self, batch: dict) -> None:
        try:
            self._hourly_sink(batch)
        except Exception:
            with self._hourly_lock:
                for key, count in batch.items():
                    self._hourly_buffer[key] = self._hourly_buffer.get(key, 0) + count

    def record_spam_blocked(self) -> None:
        self._spam_blocked += 1
        self._schedule_refresh()

    def refresh_analytics(self, *, force: bool = False) -> bool:
        if not force and self._total_usages is not None and self._active_timers is not None:
            return True
        try:
            analytics = self._analytics_provider()
        except Exception:
            logger.exception("[Metrics] Error reading analytics.")
            return False
        self._total_usages = analytics.get("total_command_usages", 0)
        self._active_timers = analytics.get("active_timers", 0)
        self.analytics_loaded.emit(analytics)
        return True

    def request_analytics_refresh(self) -> None:
        """Reload analytics off the UI thread; bursts are coalesced into one rerun."""
        if self._stopped:
            return
        if self._analytics_inflight:
            self._analytics_pending = True
            return
        self._analytics_inflight = True
        self._analytics_pending = False
        submit_db_write(self._load_analytics_in_background)

    def _load_analytics_in_background(self) -> None:
        try:
            analytics = self._analytics_provider()
        except Exception:
            logger.exception("[Metrics] Error reading analytics.")
            analytics = None
        self._analytics_ready.emit(analytics)

    @Slot(object)
    def _on_analytics_ready(self, analytics) -> None:
        self._analytics_inflight = False
        if self._stopped:
            return
        if isinstance(analytics, dict):
            self._total_usages = analytics.get("total_command_usages", 0)
            self._active_timers = analytics.get("active_timers", 0)
            self.analytics_loaded.emit(analytics)
            self.refresh_requested.emit()
        if self._analytics_pending:
            self._analytics_pending = False
            QTimer.singleShot(self._ANALYTICS_RERUN_DELAY_MS, self.request_analytics_refresh)

    def stop(self) -> None:
        self._stopped = True
        self._refresh_timer.stop()
        self._hourly_timer.stop()
        self.flush_hourly_counts(sync=True)

    def _schedule_refresh(self) -> None:
        if not self._refresh_timer.isActive():
            self._refresh_timer.start()
