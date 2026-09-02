# backend\workers\kick_chat_worker.py

import logging
import datetime
from PySide6.QtCore import QThread, Signal
from backend.providers.chat.kick_client import KickAPIClient
from backend.providers.chat.kick_websocket import ChatSocketManager
from backend.services.chat.pipeline import ChatMessageDTO

logger = logging.getLogger("minikick.workers.kick_chat")

class KickChatWorker(QThread):
    message_received = Signal(object) 
    error_occurred = Signal(str)        
    connection_success = Signal(object)
    poll_updated = Signal(object)
    poll_deleted = Signal()
    pinned_created = Signal(object)
    pinned_deleted = Signal()
    
    def __init__(self, i18n, api_client: KickAPIClient, cluster: str, key: str, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setObjectName("Worker_Chat_Socket")
        self.api_client = api_client 
        self.cluster = cluster
        self.key = key
        self.chat_manager = ChatSocketManager(cluster, key)
        self._is_stopped = False

    def run(self):
        logger.info("[KickChatWorker] Starting Kick chat worker thread...")
        try:
            user_data = self.api_client.fetch_user_data()
            if self._is_stopped:
                return 

            room_id = user_data.get("room_id")
            if not room_id:
                raise ValueError(self.i18n.get("main.workers.chat.error_room_id"))

            logger.info("[KickChatWorker] User data fetched successfully. Room ID: %s", room_id)
            self.connection_success.emit(user_data)

            while not self._is_stopped:
                self.chat_manager.start_socket(
                    room_id,
                    on_message=self._dispatch_message,
                    on_poll_update=self._dispatch_poll_update,
                    on_poll_delete=self._dispatch_poll_delete,
                    on_pinned_created=self._dispatch_pinned_created,
                    on_pinned_deleted=self._dispatch_pinned_deleted,
                )
                if not self._is_stopped:
                    logger.debug("[KickChatWorker] Socket disconnected. Reconnecting in 5s...")
                    self.msleep(5000)

        except Exception as e:
            logger.error("[KickChatWorker] Unhandled error in worker thread: %s", e)
            if not self._is_stopped:
                self.error_occurred.emit(str(e))

    def _dispatch_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int):
        if not self._is_stopped:
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            dto = ChatMessageDTO(
                user=user,
                content=msg,
                badges=badges,
                color=color,
                msg_id=msg_id,
                sender_id=sender_id,
                timestamp=now_str,
                platform="kick"
            )
            self.message_received.emit(dto)

    def _dispatch_poll_update(self, poll_data: dict):
        if not self._is_stopped:
            self.poll_updated.emit(poll_data)

    def _dispatch_poll_delete(self):
        if not self._is_stopped:
            self.poll_deleted.emit()

    def _dispatch_pinned_created(self, pinned_data: dict):
        if not self._is_stopped:
            self.pinned_created.emit(pinned_data)

    def _dispatch_pinned_deleted(self):
        if not self._is_stopped:
            self.pinned_deleted.emit()

    def stop(self):
        logger.info("[KickChatWorker] Stopping Kick chat worker...")
        self._is_stopped = True
        self.chat_manager.stop_socket()
