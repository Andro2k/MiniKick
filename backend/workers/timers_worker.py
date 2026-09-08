# backend\workers\timers_worker.py

import logging
import time
from PySide6.QtCore import QThread, Signal
from backend.providers.chat import KickAPIClient

logger = logging.getLogger("minikick.workers.timers")

class TimerWorker(QThread):
    post_message_requested = Signal(str, bool, bool)

    def __init__(self, timer_service, api_client: KickAPIClient, channel_slug: str, check_interval_seconds: int = 10, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Timers")
        self.timer_service = timer_service
        self.api_client = api_client
        self.channel_slug = channel_slug
        self.check_interval = check_interval_seconds
        self._running = False

    def run(self):
        self._running = True
        last_status_fetch_time = 0
        stream_status = {"is_live": False, "title": "", "category": ""}

        if self.api_client and self.channel_slug:
            try:
                stream_status = self.api_client.fetch_stream_status(self.channel_slug)
                last_status_fetch_time = time.time()
            except Exception as e:
                logger.error("[TimerWorker] Initial stream status fetch failed: %s", e)

        while self._running:
            try:
                now = time.time()
                if now - last_status_fetch_time >= 60:
                    if self.api_client and self.channel_slug:
                        stream_status = self.api_client.fetch_stream_status(self.channel_slug)
                        last_status_fetch_time = now
                messages_to_send = self.timer_service.check_timers(stream_status)
                for item in messages_to_send:
                    if isinstance(item, tuple) and len(item) == 3:
                        msg, apply_kick, apply_twitch = item
                        self.post_message_requested.emit(msg, apply_kick, apply_twitch)
                    else:
                        self.post_message_requested.emit(str(item), True, True)

            except Exception as e:
                logger.error("[TimerWorker] Error in run loop: %s", e)

            for _ in range(self.check_interval * 20):
                if not self._running or self.isInterruptionRequested():
                    break
                self.msleep(50)

    def stop(self):
        self._running = False
        self.requestInterruption()
        self.quit()
