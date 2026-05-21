# backend/chat.py

import json
import re
import time
from typing import Callable

import cloudscraper
import requests
import websocket

from backend.interfaces.auth_interfaces import TokenProvider

KICK_API_URL = "https://api.kick.com/public/v1/users"
KICK_CHANNEL_URL = "https://kick.com/api/v1/channels/{username}"

# --- Utilidades Comunes ---
class ChatFormatter:
    @staticmethod
    def clean(text: str) -> str:
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        text = re.sub(r"\[emote:[^\]]*\]", "", text)
        return text.strip()

# --- Capa de Acceso a Datos (API externa) ---
class KickAPIClient:
    def __init__(self, auth_provider: TokenProvider):
        self.auth_provider = auth_provider

    def fetch_user_data(self) -> dict:
        try:
            return self._execute_fetch()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                self.auth_provider.refresh_token()
                return self._execute_fetch()
            raise e

    def _execute_fetch(self) -> dict:
        tokens = self.auth_provider.get_tokens()
        access_token = tokens.get("access_token", "")       
        username = self._fetch_username(access_token)
        channel_data = self._fetch_channel_data(username)       
        avatar_url = channel_data.get("user", {}).get("profile_pic", "")
        
        return {
            "username": username,
            "room_id": channel_data.get("chatroom", {}).get("id"),
            "followers": channel_data.get("followersCount", 0),
            "is_verified": channel_data.get("user", {}).get("is_verified", False),
            "playback_url": channel_data.get("playback_url", ""),
            "avatar_url": avatar_url
        }

    def _fetch_username(self, token: str) -> str:
        resp = requests.get(
            KICK_API_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        data = resp.json().get("data", [resp.json()])
        return data[0].get("name")

    def _fetch_channel_data(self, username: str) -> dict:
        scraper = cloudscraper.create_scraper()
        url_slug = username.replace("_", "-").replace(" ", "")        
        resp = scraper.get(KICK_CHANNEL_URL.format(username=url_slug))
        
        if resp.status_code != 200:
            raise ValueError(f"No se pudo localizar el canal usando el slug: {url_slug}")
            
        return resp.json()

    def fetch_pending_redemptions(self, cursor: str = "") -> dict:
        """Obtiene las recompensas pendientes usando el token OAuth."""
        tokens = self.auth_provider.get_tokens()
        access_token = tokens.get("access_token", "")
        
        url = "https://api.kick.com/public/v1/channels/rewards/redemptions?status=pending"
        if cursor:
            url += f"&cursor={cursor}"
            
        try:
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                self.auth_provider.refresh_token()
                # Reintento recursivo simple (YAGNI)
                tokens = self.auth_provider.get_tokens()
                access_token = tokens.get("access_token", "")
                resp = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10
                )
                resp.raise_for_status()
                return resp.json()
            raise e

    def fetch_channel_rewards(self) -> dict:
        """Obtiene la lista de recompensas de puntos de canal creadas por el streamer."""
        tokens = self.auth_provider.get_tokens()
        access_token = tokens.get("access_token", "")
        
        url = "https://api.kick.com/public/v1/channels/rewards"
        
        try:
            resp = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                self.auth_provider.refresh_token()
                tokens = self.auth_provider.get_tokens()
                access_token = tokens.get("access_token", "")
                resp = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
                resp.raise_for_status()
                return resp.json()
            raise e

    def accept_redemptions(self, redemption_ids: list[str]) -> dict:
        """Marca una lista de redemptions como aceptadas en Kick para removerlas de pendientes.
        
        Requiere el scope: channel:rewards:write
        """
        if not redemption_ids:
            return {}
            
        tokens = self.auth_provider.get_tokens()
        access_token = tokens.get("access_token", "")
        
        url = "https://api.kick.com/public/v1/channels/rewards/redemptions/accept"
        payload = {"ids": redemption_ids}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                # Si el token expiró, refrescamos y reintentamos una vez
                self.auth_provider.refresh_token()
                tokens = self.auth_provider.get_tokens()
                access_token = tokens.get("access_token", "")
                headers["Authorization"] = f"Bearer {access_token}"
                
                resp = requests.post(url, json=payload, headers=headers, timeout=10)
                resp.raise_for_status()
                return resp.json()
            raise e
# --- Lógica de Negocio / Infraestructura ---
class ChatSocketManager:
    def __init__(self, cluster: str, key: str) -> None:
        self.cluster = cluster
        self.key = key
        self._running = False # Bandera de control

    def start_socket(self, room_id: int, on_message: Callable[[str, str], None]) -> None:
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
                user = payload.get("sender", {}).get("username", "")
                
                msg = ChatFormatter.clean(payload.get("content", ""))
                
                if user and msg:
                    on_message(user, msg)

            elif event == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong"}))

        # Bucle de Resiliencia: Si el socket muere, se reinicia.
        while self._running:
            try:
                ws = websocket.WebSocketApp(url, on_message=_on_message)
                # Añadimos ping_interval para mantener viva la conexión
                ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                print(f"[Chat] Socket interrumpido: {e}")

            if self._running:
                print("[Chat] Reconectando en 5 segundos...")
                time.sleep(5) # Evita saturar el servidor si falla inmediatamente

    def stop_socket(self) -> None:
        """Permite detener el bucle de reconexión limpiamente."""
        self._running = False