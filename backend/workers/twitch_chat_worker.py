# backend\workers\twitch_chat_worker.py

from PySide6.QtCore import QThread, Signal
from backend.providers.chat.twitch_websocket import TwitchSocketManager
from backend.services.chat.pipeline import ChatMessageDTO
import datetime

try:
    from backend.config.api_keys import TWITCH_BOT_USERNAME
except ImportError:
    TWITCH_BOT_USERNAME = "Minikick"

class TwitchChatWorker(QThread):
    message_received = Signal(object)
    error_occurred = Signal(str)
    connection_success = Signal(dict)

    def __init__(self, channel_name: str = "", oauth_token: str = "", bot_nick: str = "", api_client=None, i18n=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Twitch_Chat_Socket")
        self.channel_name = channel_name
        self.oauth_token = oauth_token
        self.bot_nick = bot_nick or TWITCH_BOT_USERNAME
        self.api_client = api_client
        self.i18n = i18n
        self.socket_manager = TwitchSocketManager(token=oauth_token, nick=self.bot_nick, i18n=self.i18n)
        self._is_stopped = False

    def run(self):
        try:
            user_data = {}
            if self.api_client:
                try:
                    user_data = self.api_client.fetch_user_data()
                    fetched_username = user_data.get("username")
                    if fetched_username:
                        self.channel_name = fetched_username
                except Exception as api_err:
                    pass

            if not self.channel_name:
                err_msg = self.i18n.get("logs.twitch.channel_empty") if self.i18n else ""
                raise ValueError(err_msg)


            if not self.bot_nick:
                self.bot_nick = TWITCH_BOT_USERNAME or self.channel_name

            self.socket_manager.nick = self.bot_nick.lower()
            self.socket_manager.token = self.oauth_token

            user_data["username"] = self.channel_name
            user_data["platform"] = "twitch"
            self.connection_success.emit(user_data)

            while not self._is_stopped:
                self.socket_manager.start_socket(
                    channel_name=self.channel_name,
                    on_message=self._dispatch_message
                )
                if not self._is_stopped:
                    self.msleep(5000)

        except Exception as e:
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
        self._is_stopped = True
        self.socket_manager.stop_socket()
        self.quit()
        self.wait(1500)
