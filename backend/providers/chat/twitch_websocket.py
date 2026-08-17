# backend\providers\chat\twitch_websocket.py

import logging
import websocket
from typing import Callable

TWITCH_WS_URL = "wss://irc-ws.chat.twitch.tv:443"
DEFAULT_TWITCH_COLOR = "#9146FF"

class TwitchSocketManager:
    @staticmethod
    def count_twitch_emotes(emotes_tag: str) -> int:
        if not emotes_tag:
            return 0
        total = 0
        for emote_group in emotes_tag.split("/"):
            if ":" in emote_group:
                _, ranges = emote_group.split(":", 1)
                total += len([r for r in ranges.split(",") if "-" in r])
        return total

    @staticmethod
    def strip_twitch_emotes(text: str, emotes_tag: str) -> str:
        if not emotes_tag or not text:
            return text
        ranges = []
        for emote_group in emotes_tag.split("/"):
            if ":" in emote_group:
                _, range_str = emote_group.split(":", 1)
                for r in range_str.split(","):
                    if "-" in r:
                        try:
                            start, end = map(int, r.split("-"))
                            ranges.append((start, end))
                        except ValueError:
                            pass
        if not ranges:
            return text

        ranges.sort(key=lambda x: x[0], reverse=True)
        text_chars = list(text)
        for start, end in ranges:
            if 0 <= start <= end < len(text_chars):
                del text_chars[start:end + 1]

        cleaned = "".join(text_chars)
        return " ".join(cleaned.split())

    def __init__(self, token: str = "", nick: str = "justinfan12345", i18n=None) -> None:
        self.token = token.replace("oauth:", "").strip() if token else ""
        self.nick = nick.lower().strip() if nick else "justinfan12345"
        self.i18n = i18n
        self._running = False
        self.ws: websocket.WebSocketApp | None = None
        self._channel = ""
        self._callback: Callable[[str, str, list, str, str, int], None] | None = None
        self._on_connected: Callable[[], None] | None = None
        self._on_disconnected: Callable[[], None] | None = None

    def start_socket(
        self,
        channel_name: str,
        on_message: Callable[[str, str, list, str, str, int], None],
        on_connected: Callable[[], None] | None = None,
        on_disconnected: Callable[[], None] | None = None
    ) -> None:
        self._channel = channel_name.lower().lstrip("#")
        self._callback = on_message
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._running = True

        self.ws = websocket.WebSocketApp(
            TWITCH_WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever(ping_interval=0)

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        logging.info("[TwitchWS] Connecting to Twitch channel: #%s", self._channel)
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands\r\n")
        
        pass_str = f"oauth:{self.token}" if self.token else "SCHMOOPIIE"
        ws.send(f"PASS {pass_str}\r\n")
        ws.send(f"NICK {self.nick}\r\n")
        ws.send(f"JOIN #{self._channel}\r\n")
        if self._on_connected:
            try:
                self._on_connected()
            except Exception:
                pass

    def _on_message(self, ws: websocket.WebSocketApp, raw_data: str) -> None:
        if not self._running:
            return

        lines = raw_data.split("\r\n")
        for line in lines:
            if not line:
                continue

            if line.startswith("PING"):
                ws.send("PONG :tmi.twitch.tv\r\n")
                continue

            if "PRIVMSG" in line:
                self._parse_privmsg(line)

    def _parse_privmsg(self, line: str) -> None:
        try:
            tags = {}
            raw_tags = ""
            rest = line

            if line.startswith("@"):
                parts = line.split(" ", 1)
                raw_tags = parts[0][1:]
                rest = parts[1] if len(parts) > 1 else ""

                for tag in raw_tags.split(";"):
                    if "=" in tag:
                        k, v = tag.split("=", 1)
                        tags[k] = v

            if " PRIVMSG " not in rest:
                return

            prefix_and_cmd, content = rest.split(" PRIVMSG ", 1)
            if " :" in content:
                _, msg_text = content.split(" :", 1)
            else:
                msg_text = content

            user = tags.get("display-name")
            if not user:
                if prefix_and_cmd.startswith(":"):
                    user = prefix_and_cmd[1:].split("!", 1)[0]
                else:
                    user = self.i18n.get("common.anonymous") if self.i18n else ""


            msg_id = tags.get("id", "")
            try:
                sender_id = int(tags.get("user-id", 0))
            except ValueError:
                sender_id = 0

            color = tags.get("color") or DEFAULT_TWITCH_COLOR
            emotes_tag = tags.get("emotes", "")

            raw_badges_str = tags.get("badges", "")
            badges = []
            if raw_badges_str:
                for badge_item in raw_badges_str.split(","):
                    b_name = badge_item.split("/", 1)[0]
                    if b_name:
                        badges.append(b_name)

            if self._callback and user and msg_text:
                try:
                    self._callback(user, msg_text, badges, color, msg_id, sender_id, emotes_tag)
                except TypeError:
                    self._callback(user, msg_text, badges, color, msg_id, sender_id)

        except Exception as e:
            logging.debug("[TwitchWS] Error parsing PRIVMSG line: %s", e)

    def send_privmsg(self, text: str) -> bool:
        if self.ws and self.ws.sock and self.ws.sock.connected and self._channel:
            try:
                self.ws.send(f"PRIVMSG #{self._channel} :{text}\r\n")
                return True
            except Exception as e:
                logging.error("[TwitchWS] Error sending IRC message: %s", e)
        return False

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logging.warning("[TwitchWS] Error in WebSocket connection: %s", error)

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code, close_msg) -> None:
        logging.info("[TwitchWS] Connection closed. Status: %s Msg: %s", close_status_code, close_msg)
        if self._on_disconnected:
            try:
                self._on_disconnected()
            except Exception:
                pass

    def stop_socket(self) -> None:
        self._running = False
        if self.ws:
            self.ws.keep_running = False
            if self.ws.sock and self.ws.sock.connected:
                self.ws.sock.close()

