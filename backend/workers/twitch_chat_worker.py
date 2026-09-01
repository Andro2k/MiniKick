# backend\workers\twitch_chat_worker.py

import logging
import datetime
from PySide6.QtCore import QThread, Signal
from backend.providers.chat.twitch_websocket import TwitchSocketManager
from backend.services.chat.pipeline import ChatMessageDTO
from backend.services.system.translation_service import TranslationService

logger = logging.getLogger("minikick.workers.twitch_chat")

class TwitchChatWorker(QThread):
    message_received = Signal(object)
    error_occurred = Signal(str)
    connection_success = Signal(object)
    connection_lost = Signal()
    connection_restored = Signal()

    def __init__(self, channel_name: str = "", oauth_token: str = "", bot_nick: str = "", api_client=None, i18n=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Twitch_Chat_Socket")
        self.channel_name = channel_name
        self.oauth_token = oauth_token
        self.bot_nick = bot_nick
        self.api_client = api_client
        self.i18n = i18n or TranslationService()
        self.socket_manager = TwitchSocketManager(token=oauth_token, nick=self.bot_nick, i18n=self.i18n)
        self._is_stopped = False

    def run(self):
        logger.info("[TwitchChatWorker] Starting Twitch chat worker thread...")
        try:
            user_data = {}
            if self.api_client:
                try:
                    if hasattr(self.api_client, "fetch_full_channel_info"):
                        user_data = self.api_client.fetch_full_channel_info()
                    else:
                        user_data = self.api_client.fetch_user_data()
                    fetched_username = user_data.get("username")
                    if fetched_username:
                        self.channel_name = fetched_username
                except Exception as api_err:
                    logger.debug("[TwitchChatWorker] Notice fetching initial user data: %s", api_err)

                if hasattr(self.api_client, "auth_provider") and self.api_client.auth_provider:
                    fresh_tokens = self.api_client.auth_provider.get_tokens() if hasattr(self.api_client.auth_provider, "get_tokens") else {}
                    if fresh_tokens and fresh_tokens.get("access_token"):
                        self.oauth_token = fresh_tokens.get("access_token")

            if not self.channel_name:
                err_msg = self.i18n.get("logs.twitch.channel_empty")
                raise ValueError(err_msg)

            if not self.bot_nick:
                self.bot_nick = self.channel_name

            self.socket_manager.nick = self.bot_nick.lower()
            self.socket_manager.token = self.oauth_token

            user_data["username"] = self.channel_name
            user_data["platform"] = "twitch"
            
            initial_notified = False

            def _on_connected():
                nonlocal initial_notified
                if not initial_notified:
                    initial_notified = True
                    logger.info("[TwitchChatWorker] Connected to Twitch IRC channel: #%s", self.channel_name)
                    self.connection_success.emit(user_data)
                else:
                    logger.info("[TwitchChatWorker] Reconnected to Twitch IRC channel: #%s", self.channel_name)
                    self.connection_restored.emit()

            def _on_disconnected():
                if not self._is_stopped:
                    logger.warning("[TwitchChatWorker] Connection lost with Twitch IRC.")
                    self.connection_lost.emit()

            while not self._is_stopped:
                self.socket_manager.start_socket(
                    channel_name=self.channel_name,
                    on_message=self._dispatch_message,
                    on_connected=_on_connected,
                    on_disconnected=_on_disconnected
                )
                if not self._is_stopped:
                    logger.debug("[TwitchChatWorker] Socket loop finished. Retrying in 5s...")
                    self.msleep(5000)

        except Exception as e:
            logger.error("[TwitchChatWorker] Unhandled error in Twitch chat worker: %s", e)
            if not self._is_stopped:
                self.error_occurred.emit(str(e))

    def _dispatch_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int, emotes_tag: str = ""):
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
            platform="twitch",
            emotes_tag=emotes_tag
        )
        self.message_received.emit(dto)

    def send_bot_message(self, text: str, is_announcement: bool = False) -> bool:
        if is_announcement or text.startswith("/announce"):
            if not text.startswith("/announce"):
                text = f"/announce {text}"
        return self.socket_manager.send_privmsg(text)

    def stop(self):
        logger.info("[TwitchChatWorker] Stopping Twitch chat worker...")
        self._is_stopped = True
        self.socket_manager.stop_socket()
        self.quit()
