# backend\providers\chat\kick_websocket.py

import json
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

    def start_socket(self, room_id: int, on_message: Callable[[str, str, list, str, str, int], None]) -> None:
        self._room_id = room_id
        self._callback = on_message
        self._running = True
        
        url = f"wss://ws-{self.cluster}.pusher.com/app/{self.key}?protocol=7&client=js&version=7.6.0"
        self.ws = websocket.WebSocketApp(url, on_message=self._on_raw_frame)
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def _on_raw_frame(self, ws: websocket.WebSocketApp, raw: str) -> None:
        if not self._running:
            return

        try:
            outer = json.loads(raw)
            event = outer.get("event")

            if event == "App\\Events\\ChatMessageEvent":
                inner = json.loads(outer.get("data", "{}"))
                sender = inner.get("sender", {})
                
                user = sender.get("username", "")
                msg = inner.get("content", "")
                if not user or not msg:
                    return

                identity = sender.get("identity", {})
                raw_badges = identity.get("badges", [])
                badges = [b["type"] for b in raw_badges if isinstance(b, dict) and "type" in b]
                
                color = identity.get("color", "") or COLOR_GREEN
                msg_id = inner.get("id", "")
                sender_id = sender.get("id", 0)

                if self._callback:
                    self._callback(user, msg, badges, color, msg_id, sender_id)

            elif event == "pusher:connection_established":
                payload = json.dumps({
                    "event": "pusher:subscribe",
                    "data": {"channel": f"chatrooms.{self._room_id}.v2"}
                })
                ws.send(payload)

            elif event == "pusher:ping":
                ws.send('{"event":"pusher:pong"}')

        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            pass

    def stop_socket(self) -> None:
        self._running = False
        if self.ws:
            self.ws.keep_running = False
            if self.ws.sock and self.ws.sock.connected:
                self.ws.sock.close()
