# backend\workers\youtube_chat_worker.py

import datetime
import logging
from PySide6.QtCore import QThread, Signal
from backend.providers.chat import YouTubeChatProvider
from backend.services.chat import ChatMessageDTO
from backend.services.system import TranslationService
from backend.utils.json_utils import fast_dumps

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
        self.i18n = i18n or TranslationService()
        self.provider = provider or YouTubeChatProvider(i18n=self.i18n)
        self._is_stopped = False
        self._has_connected_once = False

    def run(self):
        logger.info("[YouTubeChatWorker] Starting YouTube chat worker for channel: '%s'...", self.target_channel)
        try:
            if not self.target_channel:
                err_msg = self.i18n.get("logs.youtube.channel_empty")
                logger.error("[YouTubeChatWorker] Cannot start: target channel is empty.")
                self.error_occurred.emit(err_msg)
                return

            def _on_connected(conn_data: dict):
                if not self._has_connected_once:
                    self._has_connected_once = True
                    logger.info("[YouTubeChatWorker] Connected to YouTube Live: '%s'.", self.target_channel)
                    self.connection_success.emit(conn_data)
                else:
                    logger.info("[YouTubeChatWorker] Reconnected to YouTube Live: '%s'.", self.target_channel)
                    self.connection_restored.emit()

            def _on_disconnected():
                if not self._is_stopped:
                    logger.warning("[YouTubeChatWorker] Connection lost with YouTube Live '%s'.", self.target_channel)
                    self.connection_lost.emit()

            def _on_error(err_str: str):
                if not self._is_stopped:
                    self.error_occurred.emit(err_str)
                    if not self._has_connected_once:
                        self._is_stopped = True

            while not self._is_stopped and not self.isInterruptionRequested():
                self.provider.start_chat(
                    target=self.target_channel,
                    on_message=self._dispatch_message,
                    on_connected=_on_connected,
                    on_disconnected=_on_disconnected,
                    on_error=_on_error
                )
                if not self._has_connected_once or self._is_stopped or self.isInterruptionRequested():
                    break
                for _ in range(100):
                    if self._is_stopped or self.isInterruptionRequested():
                        break
                    self.msleep(100)

        except Exception as e:
            if not self._is_stopped and not self.isInterruptionRequested():
                logger.error("[YouTubeChatWorker] Unhandled error (%s): %s", type(e).__name__, e, exc_info=True)
                self.error_occurred.emit(str(e))

    def _dispatch_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int, extra_data: dict):
        if self._is_stopped or self.isInterruptionRequested():
            return

        if isinstance(extra_data, dict) and "emotes_tag" in extra_data:
            emotes_tag = extra_data.get("emotes_tag", "")
        else:
            emotes = extra_data.get("emotes", []) if isinstance(extra_data, dict) else []
            try:
                emotes_tag = fast_dumps(emotes) if emotes else ""
            except Exception:
                emotes_tag = ""

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
            emotes_tag=emotes_tag
        )
        self.message_received.emit(dto)

    def stop(self):
        logger.info("[YouTubeChatWorker] Stopping YouTube chat worker for '%s'...", self.target_channel)
        self._is_stopped = True
        self.requestInterruption()
        self.provider.stop_chat()
        self.quit()
