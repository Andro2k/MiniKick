# backend/kick_websocket.py

import json
import re
import time
from typing import Callable
import websocket

class ChatFormatter:
    @staticmethod
    def clean(text: str) -> str:
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        text = re.sub(r"\[emote:[^\]]*\]", "", text)
        return text.strip()

class ChatSocketManager:
    def __init__(self, cluster: str, key: str) -> None:
        self.cluster = cluster
        self.key = key
        self._running = False
        self.ws = None

    def start_socket(self, room_id: int, on_message: Callable[[str, str, list, str], None]) -> None:
        url = (
            f"wss://ws-{self.cluster}.pusher.com/app/{self.key}"
            f"?protocol=7&client=js&version=7.6.0"
        )
        self._running = True

        def _on_message(ws: websocket.WebSocketApp, raw: str) -> None:
            data = json.loads(raw)
            event = data.get("event")

            if event == "pusher:connection_established":
                ws.send(json.dumps({
                    "event": "pusher:subscribe",
                    "data": {"channel": f"chatrooms.{room_id}.v2"},
                }))

            elif event == "App\\Events\\ChatMessageEvent":
                payload = json.loads(data.get("data", "{}"))
                sender = payload.get("sender", {})
                msg_id = payload.get("id", "")
                sender_id = sender.get("id", 0)
                
                user = sender.get("username", "")
                msg = payload.get("content", "")
                
                identity = sender.get("identity", {})
                badges_raw = identity.get("badges", [])
                badges = [b.get("type") for b in badges_raw if isinstance(b, dict)]
                color = identity.get("color", "") or "#53FC18"
                
                if user and msg:
                    on_message(user, msg, badges, color, msg_id, sender_id)

            elif event == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong"}))

        while self._running:
            try:
                self.ws = websocket.WebSocketApp(url, on_message=_on_message)
                self.ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                print(f"[Chat] Socket interrupted: {e}")

            if self._running:
                print("[Chat] Reconnecting in 5 seconds...")
                time.sleep(5) 

    def stop_socket(self) -> None:
        self._running = False
        if hasattr(self, 'ws') and self.ws:
            self.ws.keep_running = False
            if hasattr(self.ws, 'sock') and self.ws.sock:
                self.ws.sock.close() 
            self.ws.close()