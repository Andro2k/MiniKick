# backend\workers\tiktok_chat_worker.py

import datetime
import logging
from PySide6.QtCore import QThread, Signal
from backend.providers.chat import TikTokChatProvider
from backend.services.chat import ChatMessageDTO
from backend.services.system import TranslationService
from backend.utils.json_utils import fast_dumps

logger = logging.getLogger("minikick.workers.tiktok_chat")

class TikTokChatWorker(QThread):
    message_received = Signal(object)
    error_occurred = Signal(str)
    connection_success = Signal(object)
    connection_lost = Signal()
    connection_restored = Signal()

    def __init__(self, target_channel: str = "", provider=None, i18n=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_TikTok_Chat_Socket")
        self.target_channel = target_channel.strip().lstrip("@")
        self.i18n = i18n or TranslationService()
        self.provider = provider or TikTokChatProvider(i18n=self.i18n)
        self._is_stopped = False
        self._has_connected_once = False

    def run(self):
        logger.info("[TikTokChatWorker] Starting TikTok chat worker for channel: '@%s'...", self.target_channel)
        try:
            if not self.target_channel:
                err_msg = self.i18n.get("logs.tiktok.empty_user")
                logger.error("[TikTokChatWorker] Cannot start: target channel is empty.")
                self.error_occurred.emit(err_msg)
                return

            def _on_connected(conn_data: dict):
                if not self._has_connected_once:
                    self._has_connected_once = True
                    logger.info("[TikTokChatWorker] Connected to TikTok Live: '@%s'.", self.target_channel)
                    self.connection_success.emit(conn_data)
                else:
                    logger.info("[TikTokChatWorker] Reconnected to TikTok Live: '@%s'.", self.target_channel)
                    self.connection_restored.emit()

            def _on_disconnected():
                if not self._is_stopped:
                    logger.warning("[TikTokChatWorker] Connection lost with TikTok Live '@%s'.", self.target_channel)
                    self.connection_lost.emit()

            def _on_error(err_str: str):
                if not self._is_stopped:
                    self.error_occurred.emit(err_str)
                    if not self._has_connected_once:
                        self._is_stopped = True

            while not self._is_stopped and not self.isInterruptionRequested():
                self.provider.start_chat(
                    unique_id=self.target_channel,
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
                logger.error("[TikTokChatWorker] Error no controlado (%s): %s", type(e).__name__, e, exc_info=True)
                self.error_occurred.emit(str(e))

    def _dispatch_message(self, user: str, msg: str, badges: list, color: str, timestamp: str, msg_id: int, extra_data: dict):
        if self._is_stopped or self.isInterruptionRequested():
            return

        now_str = timestamp or datetime.datetime.now().strftime("%H:%M:%S")
        emotes_tag = ""
        if extra_data and isinstance(extra_data, dict):
            emotes_list = extra_data.get("emotes")
            if emotes_list and isinstance(emotes_list, list):
                try:
                    emotes_tag = fast_dumps(emotes_list)
                except Exception:
                    emotes_tag = ""

        dto = ChatMessageDTO(
            user=user,
            content=msg,
            badges=badges,
            color=color,
            msg_id=str(msg_id),
            sender_id=0,
            timestamp=now_str,
            platform="tiktok",
            emotes_tag=emotes_tag
        )
        self.message_received.emit(dto)

    def stop(self):
        logger.info("[TikTokChatWorker] Stopping TikTok chat worker for '@%s'...", self.target_channel)
        self._is_stopped = True
        self.requestInterruption()
        self.provider.stop_chat()
        self.quit()
