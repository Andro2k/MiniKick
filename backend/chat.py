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
    def fetch_user_data(token: str) -> dict:
        username = KickAPIClient._fetch_username(token)
        channel_data = KickAPIClient._fetch_channel_data(username)
        
        # Obtenemos la URL de la imagen, manejando nulos por seguridad
        avatar_url = channel_data.get("user", {}).get("profile_pic", "")
        
        # Extraemos los datos interesantes (Alta Cohesión de lectura de datos)
        return {
            "username": username,
            "room_id": channel_data.get("chatroom", {}).get("id"),
            "followers": channel_data.get("followersCount", 0),
            "is_verified": channel_data.get("user", {}).get("is_verified", False),
            "playback_url": channel_data.get("playback_url", ""),
            "avatar_url": avatar_url # NUEVO DATO
        }

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
    def _fetch_channel_data(username: str) -> dict:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(KICK_CHANNEL_URL.format(username=username))
        return resp.json()

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