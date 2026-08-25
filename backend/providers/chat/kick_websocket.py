# backend\providers\chat\kick_websocket.py

from backend.utils.json_utils import fast_loads, fast_dumps
import websocket
from typing import Callable
from frontend.common.theme import COLOR_GREEN

class ChatSocketManager:
    def __init__(self, cluster: str, key: str) -> None:
        self.cluster = cluster
        self.key = key
        self._running = False
        self.ws: websocket.WebSocketApp | None = None
        self._room_id = 0
        self._callback: Callable | None = None
        self._on_poll_update: Callable[[dict], None] | None = None
        self._on_poll_delete: Callable[[], None] | None = None
        self._on_pinned_created: Callable[[dict], None] | None = None
        self._on_pinned_deleted: Callable[[], None] | None = None
        self._dispatch_table: dict[str, Callable[[dict, websocket.WebSocketApp], None]] = {
            "App\\Events\\ChatMessageEvent": self._handle_chat_message,
            "App\\Events\\PollUpdateEvent": self._handle_poll_update,
            "App\\Events\\PollDeleteEvent": self._handle_poll_delete,
            "App\\Events\\PinnedMessageCreatedEvent": self._handle_pinned_created,
            "App\\Events\\PinnedMessageDeletedEvent": self._handle_pinned_deleted,
            "pusher:connection_established": self._handle_connection_established,
            "pusher:ping": self._handle_ping,
        }

    def start_socket(
        self,
        room_id: int,
        on_message: Callable[[str, str, list, str, str, int], None],
        on_poll_update: Callable[[dict], None] | None = None,
        on_poll_delete: Callable[[], None] | None = None,
        on_pinned_created: Callable[[dict], None] | None = None,
        on_pinned_deleted: Callable[[], None] | None = None,
    ) -> None:
        self._room_id = room_id
        self._callback = on_message
        self._on_poll_update = on_poll_update
        self._on_poll_delete = on_poll_delete
        self._on_pinned_created = on_pinned_created
        self._on_pinned_deleted = on_pinned_deleted
        self._running = True
        
        url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"
        self.ws = websocket.WebSocketApp(url, on_message=self._on_raw_frame)
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def _parse_inner_data(self, outer: dict) -> dict:
        data_raw = outer.get("data", {})
        if isinstance(data_raw, (str, bytes, bytearray)):
            if not data_raw or data_raw == "{}" or data_raw == "[]":
                return {}
            try:
                res = fast_loads(data_raw)
                return res if isinstance(res, dict) else {}
            except Exception:
                return {}
        elif isinstance(data_raw, dict):
            return data_raw
        return {}

    def _on_raw_frame(self, ws: websocket.WebSocketApp, raw: str) -> None:
        if not self._running:
            return

        try:
            outer = fast_loads(raw)
            if not isinstance(outer, dict):
                return
            event = outer.get("event")
            handler = self._dispatch_table.get(event)
            if handler:
                handler(outer, ws)

        except Exception:
            pass

    def _handle_chat_message(self, outer: dict, ws: websocket.WebSocketApp) -> None:
        inner = self._parse_inner_data(outer)
        sender = inner.get("sender")
        if not isinstance(sender, dict):
            return

        user = sender.get("username", "")
        msg = inner.get("content", "")
        if not user or not msg:
            return

        identity = sender.get("identity")
        badges = []
        color = COLOR_GREEN

        if isinstance(identity, dict):
            color = identity.get("color") or COLOR_GREEN
            raw_badges = identity.get("badges")
            if isinstance(raw_badges, list):
                for b in raw_badges:
                    if isinstance(b, dict) and "type" in b:
                        badges.append(b["type"])

            badges_v2 = identity.get("badges_v2")
            if isinstance(badges_v2, list):
                for b in badges_v2:
                    if isinstance(b, dict) and b.get("name") == "level":
                        meta = b.get("metadata")
                        if isinstance(meta, dict):
                            lvl = meta.get("level")
                            if lvl is not None:
                                badges.append(f"level_{lvl}")

        msg_id = inner.get("id", "")
        sender_id = sender.get("id", 0)

        if self._callback:
            self._callback(user, msg, badges, color, msg_id, sender_id)


    def _handle_poll_update(self, outer: dict, ws: websocket.WebSocketApp) -> None:
        inner = self._parse_inner_data(outer)
        poll_data = inner.get("poll") or inner
        if poll_data and self._on_poll_update:
            self._on_poll_update(poll_data)

    def _handle_poll_delete(self, outer: dict, ws: websocket.WebSocketApp) -> None:
        if self._on_poll_delete:
            self._on_poll_delete()

    def _handle_pinned_created(self, outer: dict, ws: websocket.WebSocketApp) -> None:
        inner = self._parse_inner_data(outer)
        pinned = inner.get("pinned_message") or inner
        if isinstance(pinned, dict):
            msg_obj = pinned.get("message")
            if isinstance(msg_obj, dict):
                content = str(msg_obj.get("content", ""))
                sender = msg_obj.get("sender") or pinned.get("sender") or {}
            elif isinstance(pinned.get("content"), dict):
                content = str(pinned.get("content", {}).get("content", ""))
                sender = pinned.get("content", {}).get("sender") or pinned.get("sender") or {}
            else:
                content = str(pinned.get("content") or pinned.get("message") or "")
                sender = pinned.get("sender") or {}

            normalized = {
                "id": pinned.get("id") or (msg_obj.get("id") if isinstance(msg_obj, dict) else ""),
                "content": content,
                "sender": sender
            }
            if self._on_pinned_created:
                self._on_pinned_created(normalized)

    def _handle_pinned_deleted(self, outer: dict, ws: websocket.WebSocketApp) -> None:
        if self._on_pinned_deleted:
            self._on_pinned_deleted()

    def _handle_connection_established(self, outer: dict, ws: websocket.WebSocketApp) -> None:
        payload = fast_dumps({
            "event": "pusher:subscribe",
            "data": {"channel": f"chatrooms.{self._room_id}.v2"}
        })
        ws.send(payload)

    def _handle_ping(self, outer: dict, ws: websocket.WebSocketApp) -> None:
        ws.send('{"event":"pusher:pong"}')

    def stop_socket(self) -> None:
        self._running = False
        if self.ws:
            self.ws.keep_running = False
            if self.ws.sock and self.ws.sock.connected:
                self.ws.sock.close()

