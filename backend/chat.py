# backend/chat.py

import json
import re
from typing import Callable

import cloudscraper
import requests
import websocket

KICK_API_URL = "https://api.kick.com/public/v1/users"
KICK_CHANNEL_URL = "https://kick.com/api/v1/channels/{username}"

# --- Utilidades Comunes ---
class ChatFormatter:
    @staticmethod
    def clean(text: str) -> str:
        text = re.sub(r"https?://\S+|www\.\S+", "", text)   # URLs
        text = re.sub(r"\[emote:[^\]]*\]", "", text)         # Emotes
        return text.strip()

# --- Capa de Acceso a Datos (API externa) ---
class KickAPIClient:
    @staticmethod
    def fetch_user_data(token: str) -> tuple[str, int]:
        username = KickAPIClient._fetch_username(token)
        room_id = KickAPIClient._fetch_room_id(username)
        return username, room_id

    @staticmethod
    def _fetch_username(token: str) -> str:
        resp = requests.get(
            KICK_API_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        data = resp.json().get("data", [resp.json()])
        return data[0].get("name")

    @staticmethod
    def _fetch_room_id(username: str) -> int:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(KICK_CHANNEL_URL.format(username=username))
        return resp.json().get("chatroom", {}).get("id")

# --- Lógica de Negocio / Infraestructura ---
class ChatSocketManager:
    def __init__(self, cluster: str, key: str) -> None:
        self.cluster = cluster
        self.key = key

    def start_socket(self, room_id: int, on_message: Callable[[str, str], None]) -> None:
        url = (
            f"wss://ws-{self.cluster}.pusher.com/app/{self.key}"
            f"?protocol=7&client=js&version=7.6.0"
        )

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
                user = payload.get("sender", {}).get("username", "")
                
                # Usamos la utilidad centralizada
                msg = ChatFormatter.clean(payload.get("content", ""))
                
                if user and msg:
                    on_message(user, msg)

            elif event == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong"}))

        ws = websocket.WebSocketApp(url, on_message=_on_message)
        ws.run_forever()