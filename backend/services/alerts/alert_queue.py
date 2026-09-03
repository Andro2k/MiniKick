# backend\services\alerts\alert_queue.py

import collections
import logging
import threading
import time
from typing import Callable

logger = logging.getLogger("minikick.services.alerts.queue")

class AlertQueue:
    def __init__(
        self,
        on_dispatch: Callable[[dict], None] | None = None,
        gift_batch_window_s: float = 3.0,
        watchdog_min_s: float = 2.0,
        watchdog_buffer_s: float = 1.5
    ):
        self._queue: collections.deque[dict] = collections.deque()
        self._active_alert: dict | None = None
        self._lock = threading.Lock()
        self._on_dispatch = on_dispatch
        self.gift_batch_window_s = gift_batch_window_s
        self.watchdog_min_s = watchdog_min_s
        self.watchdog_buffer_s = watchdog_buffer_s
        self._recent_gifts: dict[tuple[str, str], dict] = {}
        self._watchdog_timer: threading.Timer | None = None

    @property
    def is_busy(self) -> bool:
        with self._lock:
            return self._active_alert is not None

    @property
    def queue_size(self) -> int:
        with self._lock:
            return len(self._queue)

    def enqueue(self, payload: dict) -> None:
        with self._lock:
            alert_type = payload.get("alert_type")
            platform = payload.get("platform", "")
            user = payload.get("username", "")

            if alert_type == "sub_gift" and user:
                gift_key = (platform, user)
                now = time.monotonic()
                if gift_key in self._recent_gifts:
                    recent = self._recent_gifts[gift_key]
                    if (now - recent["timestamp"]) < self.gift_batch_window_s:
                        target_payload = recent.get("payload")
                        if target_payload and target_payload in self._queue:
                            target_payload["amount"] += payload.get("amount", 1)
                            logger.info(
                                "[AlertQueue] Consolidated sub gifts for %s (%s): total %d",
                                user, platform, target_payload["amount"]
                            )
                            recent["timestamp"] = now
                            return

                self._recent_gifts[gift_key] = {
                    "payload": payload,
                    "timestamp": now
                }

            self._queue.append(payload)
            logger.debug("[AlertQueue] Enqueued alert %s. Queue size: %d", payload.get("id"), len(self._queue))

        self._check_and_dispatch_next()

    def finish_active_alert(self, alert_id: str | None = None) -> None:
        with self._lock:
            if self._watchdog_timer is not None:
                self._watchdog_timer.cancel()
                self._watchdog_timer = None
            if self._active_alert is not None:
                current_id = self._active_alert.get("id")
                if alert_id is None or alert_id == current_id:
                    logger.debug("[AlertQueue] Finished active alert: %s", current_id)
                    self._active_alert = None

        self._check_and_dispatch_next()

    def _on_watchdog_timeout(self, alert_id: str | None) -> None:
        with self._lock:
            if self._active_alert is not None:
                current_id = self._active_alert.get("id")
                if alert_id is None or alert_id == current_id:
                    logger.debug("[AlertQueue] Watchdog auto-advanced active alert: %s", current_id)
                    self._active_alert = None
                    self._watchdog_timer = None

        self._check_and_dispatch_next()

    def clear(self) -> None:
        with self._lock:
            if self._watchdog_timer is not None:
                self._watchdog_timer.cancel()
                self._watchdog_timer = None
            self._queue.clear()
            self._active_alert = None
            self._recent_gifts.clear()
            logger.info("[AlertQueue] Queue cleared.")

    def _check_and_dispatch_next(self) -> None:
        to_dispatch = None
        with self._lock:
            if self._active_alert is None and self._queue:
                self._active_alert = self._queue.popleft()
                to_dispatch = dict(self._active_alert)

                duration_ms = to_dispatch.get("duration_ms", 5000)
                timeout_s = max(self.watchdog_min_s, (duration_ms / 1000.0) + self.watchdog_buffer_s)
                active_id = to_dispatch.get("id")

                if self._watchdog_timer is not None:
                    self._watchdog_timer.cancel()
                self._watchdog_timer = threading.Timer(
                    timeout_s, self._on_watchdog_timeout, args=[active_id]
                )
                self._watchdog_timer.daemon = True
                self._watchdog_timer.start()

        if to_dispatch and self._on_dispatch:
            try:
                self._on_dispatch(to_dispatch)
            except Exception as e:
                logger.error("[AlertQueue] Error in on_dispatch callback: %s", e)
