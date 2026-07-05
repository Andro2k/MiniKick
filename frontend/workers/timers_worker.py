# frontend/workers/timers_worker.py

import logging
import time
from PySide6.QtCore import QThread, Signal
from backend.providers.kick.kick_client import KickAPIClient

class TimerWorker(QThread):
    post_message_requested = Signal(str)

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
                logging.error("[TimerWorker] Initial stream status fetch failed: %s", e)

        while self._running:
            try:
                now = time.time()
                if now - last_status_fetch_time >= 60:
                    if self.api_client and self.channel_slug:
                        stream_status = self.api_client.fetch_stream_status(self.channel_slug)
                        last_status_fetch_time = now
                messages_to_send = self.timer_service.check_timers(stream_status)
                for msg in messages_to_send:
                    self.post_message_requested.emit(msg)

            except Exception as e:
                logging.error("[TimerWorker] Error in run loop: %s", e)

            for _ in range(self.check_interval * 2):
                if not self._running:
                    break
                self.msleep(500)

    def stop(self):
        self._running = False
