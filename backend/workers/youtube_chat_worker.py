# backend\workers\youtube_chat_worker.py

import datetime
import logging
from PySide6.QtCore import QThread, Signal
from backend.providers.chat.youtube_chat_provider import YouTubeChatProvider
from backend.services.chat.pipeline import ChatMessageDTO

logger = logging.getLogger("minikick.workers.youtube_chat")

class YouTubeChatWorker(QThread):
    message_received = Signal(object)
    error_occurred = Signal(str)
    connection_success = Signal(object)
    connection_lost = Signal()
    connection_restored = Signal()

    def __init__(self, target_channel: str = "", provider=None, i18n=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_YouTube_Chat_Socket")
        self.target_channel = target_channel.strip()
        self.i18n = i18n
        self.provider = provider or YouTubeChatProvider(i18n=self.i18n)
        self._is_stopped = False

    def run(self):
        try:
            if not self.target_channel:
                err_msg = self.i18n.get("logs.youtube.channel_empty") if self.i18n else "YouTube target stream or channel not specified."
                raise ValueError(err_msg)

            initial_notified = False

            def _on_connected(conn_data: dict):
                nonlocal initial_notified
                if not initial_notified:
                    initial_notified = True
                    self.connection_success.emit(conn_data)
                else:
                    self.connection_restored.emit()

            def _on_disconnected():
                if not self._is_stopped:
                    self.connection_lost.emit()

            def _on_error(err_str: str):
                if not self._is_stopped:
                    self.error_occurred.emit(err_str)

            while not self._is_stopped:
                self.provider.start_chat(
                    target=self.target_channel,
                    on_message=self._dispatch_message,
                    on_connected=_on_connected,
                    on_disconnected=_on_disconnected,
                    on_error=_on_error
                )
                if not self._is_stopped:
                    self.msleep(4000)

        except Exception as e:
            if not self._is_stopped:
                logger.error("[YouTubeChatWorker] Unhandled error: %s", e)
                self.error_occurred.emit(str(e))

    def _dispatch_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int, extra_data: dict):
        if self._is_stopped:
            return

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        dto = ChatMessageDTO(
            user=user,
            content=msg,
            badges=badges,
            color=color,
            msg_id=msg_id,
            sender_id=sender_id,
            timestamp=now_str,
            platform="youtube",
            emotes_tag=""
        )
        self.message_received.emit(dto)

    def stop(self):
        self._is_stopped = True
        self.provider.stop_chat()
        self.quit()
