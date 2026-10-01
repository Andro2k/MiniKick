# backend\providers\chat\twitch_ws_provider.py

import inspect
import logging
import threading
import time
from collections import deque
from typing import Callable
import websocket

from backend.services.system import TranslationService
from .base_chat_provider import BaseChatSocketProvider

logger = logging.getLogger("minikick.providers.twitch_ws_provider")

TWITCH_WS_URL = "wss://irc-ws.chat.twitch.tv:443"
DEFAULT_TWITCH_COLOR = "#9146FF"

RFC_6455_CLOSE_CODES: dict[int, str] = {
    1000: "Normal Closure",
    1001: "Going Away",
    1002: "Protocol Error",
    1003: "Unsupported Data",
    1005: "No Status Received",
    1006: "Abnormal Closure",
    1007: "Invalid frame payload data",
    1008: "Policy Violation",
    1009: "Message Too Big",
    1011: "Internal Server Error",
    1012: "Service Restart",
    1013: "Try Again Later",
    1015: "TLS Handshake Failure",
}

class TwitchSocketManager(BaseChatSocketProvider):
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

        ranges.sort(key=lambda x: x[0])

        merged = []
        for s, e in ranges:
            if not merged or s > merged[-1][1] + 1:
                merged.append([s, e])
            else:
                merged[-1][1] = max(merged[-1][1], e)

        pieces = []
        idx = 0
        text_len = len(text)
        for s, e in merged:
            if s > idx:
                pieces.append(text[idx:min(s, text_len)])
            idx = max(idx, e + 1)
        if idx < text_len:
            pieces.append(text[idx:])

        cleaned = "".join(pieces)
        return " ".join(cleaned.split())

    def __init__(self, token: str = "", nick: str = "", i18n=None) -> None:
        self.token = token.replace("oauth:", "").strip() if token else ""
        self.nick = nick.strip() if nick else ""
        self.i18n = i18n or TranslationService()
        self._running = False
        self.ws: websocket.WebSocketApp | None = None
        self._channel = ""

        self._seen_message_ids = deque(maxlen=1000)
        self._seen_message_ids_set: set[str] = set()

        self._callback: Callable[..., None] | None = None
        self._callback_arity: int = 8
        self._on_connected: Callable[[], None] | None = None
        self._on_disconnected: Callable[[], None] | None = None

        self._last_activity_time: float = 0.0
        self._pending_ping_time: float = 0.0
        self._heartbeat_thread: threading.Thread | None = None
        self._stop_heartbeat_event: threading.Event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    def start_socket(
        self,
        channel_name: str,
        on_message: Callable[..., None],
        on_connected: Callable[[], None] | None = None,
        on_disconnected: Callable[[], None] | None = None
    ) -> None:
        self._channel = channel_name.lower().lstrip("#")
        self._callback = on_message
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._running = True

        try:
            sig = inspect.signature(on_message)
            params = list(sig.parameters.values())
            has_varargs = any(p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD) for p in params)
            if has_varargs:
                self._callback_arity = 999
            else:
                self._callback_arity = len([
                    p for p in params
                    if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                ])
        except Exception:
            self._callback_arity = 8

        self._last_activity_time = time.time()
        self._pending_ping_time = 0.0

        self.ws = websocket.WebSocketApp(
            TWITCH_WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever(ping_interval=30, ping_timeout=20)

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        logger.info("[TwitchWS] Connecting to Twitch channel: #%s", self._channel)
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands\r\n")
        
        pass_str = f"oauth:{self.token}" if self.token else "SCHMOOPIIE"
        nick_str = self.nick.lower().strip() if self.token and self.nick else "justinfan12345"

        ws.send(f"PASS {pass_str}\r\n")
        ws.send(f"NICK {nick_str}\r\n")
        ws.send(f"JOIN #{self._channel}\r\n")

        self._start_heartbeat_watchdog(ws)

        if self._on_connected:
            try:
                self._on_connected()
            except Exception:
                pass

    def _on_message(self, ws: websocket.WebSocketApp, raw_data: str) -> None:
        if not self._running:
            return

        self._last_activity_time = time.time()
        self._pending_ping_time = 0.0

        lines = raw_data.split("\r\n")
        for line in lines:
            if not line:
                continue

            if line.startswith("PING"):
                ping_arg = line.split("PING", 1)[1].strip()
                pong_payload = ping_arg if ping_arg else ":tmi.twitch.tv"
                ws.send(f"PONG {pong_payload}\r\n")
                continue

            if "NOTICE" in line and "authentication failed" in line.lower():
                logger.error("[TwitchWS] Twitch IRC login failed: %s", line)

            if "PRIVMSG" in line:
                self._parse_privmsg(line)

    def _parse_privmsg(self, line: str) -> None:
        try:
            line = line.rstrip("\r\n")
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
                    user = self.i18n.get("common.anonymous") if hasattr(self.i18n, "get") else "Anonymous"

            msg_id = tags.get("id", "")

            if msg_id:
                if msg_id in self._seen_message_ids_set:
                    return
                if len(self._seen_message_ids) == self._seen_message_ids.maxlen:
                    oldest = self._seen_message_ids.popleft()
                    self._seen_message_ids_set.discard(oldest)
                self._seen_message_ids.append(msg_id)
                self._seen_message_ids_set.add(msg_id)

            try:
                sender_id = int(tags.get("user-id", 0))
            except ValueError:
                sender_id = 0

            color = tags.get("color") or DEFAULT_TWITCH_COLOR
            emotes_tag = tags.get("emotes", "")
            gifs_tag = tags.get("gifs", "")
            gif_url = ""
            if gifs_tag:
                parts = gifs_tag.split("|")
                if len(parts) >= 3 and parts[2].startswith("http"):
                    gif_url = parts[2]

            raw_badges_str = tags.get("badges", "")
            badges = []
            if raw_badges_str:
                for badge_item in raw_badges_str.split(","):
                    b_name = badge_item.split("/", 1)[0]
                    if b_name:
                        badges.append(b_name)

            if self._callback and user and msg_text:
                if self._callback_arity >= 8:
                    self._callback(user, msg_text, badges, color, msg_id, sender_id, emotes_tag, gif_url)
                elif self._callback_arity == 7:
                    self._callback(user, msg_text, badges, color, msg_id, sender_id, emotes_tag)
                else:
                    self._callback(user, msg_text, badges, color, msg_id, sender_id)

        except Exception as e:
            logger.debug("[TwitchWS] Error parsing PRIVMSG line: %s", e)

    def _start_heartbeat_watchdog(self, ws: websocket.WebSocketApp) -> None:
        self._stop_heartbeat_watchdog()
        self._stop_heartbeat_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_watchdog_loop,
            args=(ws,),
            name="TwitchIRCHeartbeatWatchdog",
            daemon=True
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat_watchdog(self) -> None:
        self._stop_heartbeat_event.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            if threading.current_thread() != self._heartbeat_thread:
                self._heartbeat_thread.join(timeout=1.0)
        self._heartbeat_thread = None

    def _heartbeat_watchdog_loop(self, ws: websocket.WebSocketApp) -> None:
        ping_interval = 60.0
        pong_timeout = 25.0

        while not self._stop_heartbeat_event.is_set() and self._running:
            if self._stop_heartbeat_event.wait(timeout=5.0):
                break
            if not self._running or not ws:
                break

            now = time.time()

            if self._pending_ping_time > 0.0 and (now - self._pending_ping_time) > pong_timeout:
                logger.warning(
                    "[TwitchWS] Twitch IRC heartbeat timeout! No response to PING after %.1fs. Forcing reconnect.",
                    now - self._pending_ping_time
                )
                try:
                    if ws.sock and ws.sock.connected:
                        ws.sock.close()
                    ws.close()
                except Exception:
                    pass
                break

            if self._pending_ping_time == 0.0 and (now - self._last_activity_time) >= ping_interval:
                try:
                    self._pending_ping_time = now
                    ws.send("PING :minikick_keepalive\r\n")
                    logger.debug("[TwitchWS] Dispatched proactive keepalive PING")
                except Exception as e:
                    logger.debug("[TwitchWS] Error sending proactive PING: %s", e)

    def send_privmsg(self, text: str) -> bool:
        if self.ws and self.ws.sock and self.ws.sock.connected and self._channel:
            try:
                self.ws.send(f"PRIVMSG #{self._channel} :{text}\r\n")
                return True
            except Exception as e:
                logger.error("[TwitchWS] Error sending IRC message: %s", e)
        return False

    def _on_error(self, _ws: websocket.WebSocketApp, error: Exception) -> None:
        is_routine_network_drop = isinstance(
            error,
            (websocket.WebSocketTimeoutException, TimeoutError, ConnectionResetError, BrokenPipeError)
        )
        log_func = logger.warning if is_routine_network_drop else logger.error
        log_func(
            "[TwitchWS] WebSocket error (%s): %s",
            type(error).__name__,
            error,
            exc_info=not is_routine_network_drop and not isinstance(error, (KeyboardInterrupt, SystemExit))
        )

    def _on_close(self, _ws: websocket.WebSocketApp, close_status_code, close_msg) -> None:
        self._stop_heartbeat_watchdog()
        meaning = RFC_6455_CLOSE_CODES.get(close_status_code, "Unknown/Unregistered") if close_status_code is not None else "Clean/No Code"
        logger.info("[TwitchWS] Connection closed: code=%s (%s), reason=%s", close_status_code, meaning, close_msg or "N/A")
        if self._on_disconnected:
            try:
                self._on_disconnected()
            except Exception:
                pass

    def stop_socket(self) -> None:
        self._running = False
        self._stop_heartbeat_watchdog()
        if self.ws:
            self.ws.keep_running = False
            if self.ws.sock and self.ws.sock.connected:
                self.ws.sock.close()
