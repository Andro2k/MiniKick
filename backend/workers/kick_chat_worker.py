# backend\workers\kick_chat_worker.py

import logging
import datetime
from PySide6.QtCore import QThread, Signal
from backend.providers.chat import KickAPIClient, KickWebSocketManager
from backend.services.chat import ChatMessageDTO

logger = logging.getLogger("minikick.workers.kick_chat")

class KickPollSyncWorker(QThread):
    poll_updated = Signal(object)
    poll_deleted = Signal()

    def __init__(self, api_client: KickAPIClient, channel_slug: str, interval_ms: int = 2000, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Kick_Poll_Sync")
        self.api_client = api_client
        self.channel_slug = channel_slug
        self.interval_ms = interval_ms
        self._is_stopped = False
        self._last_votes_tuple = None

    def stop(self):
        self._is_stopped = True

    def run(self):
        logger.info("[KickPollSyncWorker] Started poll reconciliation worker for '%s'", self.channel_slug)
        while not self._is_stopped:
            self.msleep(self.interval_ms)
            if self._is_stopped:
                break

            try:
                poll = self.api_client.fetch_active_poll(self.channel_slug)
                if self._is_stopped:
                    break

                if not poll:
                    logger.info("[KickPollSyncWorker] Active poll ended or not found on Kick API. Emitting poll_deleted.")
                    self.poll_deleted.emit()
                    break

                options = poll.get("options") or []
                votes_tuple = tuple((opt.get("id"), opt.get("votes", 0)) for opt in options)
                remaining = poll.get("remaining", 0)

                if votes_tuple != self._last_votes_tuple or remaining == 0:
                    self._last_votes_tuple = votes_tuple
                    self.poll_updated.emit(poll)

                if remaining == 0:
                    break

            except Exception as e:
                logger.debug("[KickPollSyncWorker] Error during poll reconciliation: %s", e)

class KickChatWorker(QThread):
    message_received = Signal(object) 
    error_occurred = Signal(str)        
    connection_success = Signal(object)
    poll_updated = Signal(object)
    poll_deleted = Signal()
    pinned_created = Signal(object)
    pinned_deleted = Signal()
    reward_redeemed = Signal(str, str, str)
    
    def __init__(self, i18n, api_client: KickAPIClient, cluster: str, key: str, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setObjectName("Worker_Kick_Chat_Socket")
        self.api_client = api_client 
        self.cluster = cluster
        self.key = key
        self.channel_slug = ""
        self.chat_manager = KickWebSocketManager(cluster, key)
        self._is_stopped = False
        self._poll_sync_worker: KickPollSyncWorker | None = None

    def run(self):
        logger.info("[KickChatWorker] Starting Kick chat worker thread...")
        try:
            user_data = self.api_client.fetch_user_data()
            if self._is_stopped:
                return 

            self.channel_slug = user_data.get("slug") or user_data.get("username") or ""
            room_id = user_data.get("room_id")
            channel_id = int(user_data.get("channel_id") or user_data.get("broadcaster_id") or 0)
            followers_count = int(user_data.get("followers") or 0)
            if not room_id:
                raise ValueError(self.i18n.get("main.workers.chat.error_room_id"))

            logger.info("[KickChatWorker] User data fetched successfully. Room ID: %s, Channel ID: %s, Followers: %s, Slug: %s", room_id, channel_id, followers_count, self.channel_slug)
            self.connection_success.emit(user_data)

            if self.channel_slug and not self._is_stopped:
                try:
                    initial_poll = self.api_client.fetch_active_poll(self.channel_slug)
                    if initial_poll:
                        logger.info("[KickChatWorker] Found active poll on Kick at startup: '%s'", initial_poll.get("title"))
                        self._dispatch_poll_update(initial_poll)
                except Exception as e:
                    logger.debug("[KickChatWorker] Error checking initial poll on startup: %s", e)

            while not self._is_stopped:
                self.chat_manager.start_socket(
                    room_id,
                    channel_id=channel_id,
                    initial_followers=followers_count,
                    on_message=self._dispatch_message,
                    on_poll_update=self._dispatch_poll_update,
                    on_poll_delete=self._dispatch_poll_delete,
                    on_pinned_created=self._dispatch_pinned_created,
                    on_pinned_deleted=self._dispatch_pinned_deleted,
                    on_reward_redeemed=self._dispatch_reward,
                )
                if not self._is_stopped:
                    logger.debug("[KickChatWorker] Socket disconnected. Reconnecting in 5s...")
                    self.msleep(5000)

        except Exception as e:
            logger.error("[KickChatWorker] Unhandled error (%s) in worker thread: %s", type(e).__name__, e, exc_info=True)
            if not self._is_stopped:
                self.error_occurred.emit(str(e))

    def _dispatch_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int):
        if not self._is_stopped:
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            logger.info("[KickChatWorker] [%s] Message dispatched from '%s': %s (id=%s)", now_str, user, msg, msg_id[:8] if msg_id else "n/a")
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
            self._ensure_poll_sync_worker()

    def _ensure_poll_sync_worker(self):
        if not self.channel_slug or self._is_stopped:
            return
        if self._poll_sync_worker and self._poll_sync_worker.isRunning():
            return
        self._poll_sync_worker = KickPollSyncWorker(self.api_client, self.channel_slug, parent=None)
        self._poll_sync_worker.poll_updated.connect(self._on_sync_poll_updated)
        self._poll_sync_worker.poll_deleted.connect(self._on_sync_poll_deleted)
        self._poll_sync_worker.start()

    def _on_sync_poll_updated(self, poll_data: dict):
        if not self._is_stopped:
            self.poll_updated.emit(poll_data)

    def _on_sync_poll_deleted(self):
        if not self._is_stopped:
            self.poll_deleted.emit()
            self._stop_poll_sync_worker()

    def _stop_poll_sync_worker(self):
        if self._poll_sync_worker:
            self._poll_sync_worker.stop()
            self._poll_sync_worker.wait(1000)
            self._poll_sync_worker = None

    def _dispatch_poll_delete(self):
        self._stop_poll_sync_worker()
        if not self._is_stopped:
            self.poll_deleted.emit()

    def _dispatch_pinned_created(self, pinned_data: dict):
        if not self._is_stopped:
            self.pinned_created.emit(pinned_data)

    def _dispatch_pinned_deleted(self):
        if not self._is_stopped:
            self.pinned_deleted.emit()

    def _dispatch_reward(self, username: str, reward_title: str, user_input: str):
        if not self._is_stopped:
            self.reward_redeemed.emit(username, reward_title, user_input)

    def stop(self):
        logger.info("[KickChatWorker] Stopping Kick chat worker...")
        self._is_stopped = True
        self._stop_poll_sync_worker()
        self.chat_manager.stop_socket()
