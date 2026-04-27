import json
import re
from typing import Callable

import cloudscraper
import requests
import websocket

KICK_API_URL = "https://api.kick.com/public/v1/users"
KICK_CHANNEL_URL = "https://kick.com/api/v1/channels/{username}"


class ChatManager:
    def __init__(self, token: str, cluster: str, key: str) -> None:
        self.token = token
        self.cluster = cluster
        self.key = key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_user_data(self) -> tuple[str, int]:
        """Return (username, chatroom_id) for the authenticated user."""
        username = self._fetch_username()
        room_id = self._fetch_room_id(username)
        return username, room_id

    def start_socket(self, room_id: int, on_message: Callable[[str, str], None]) -> None:
        """Connect to Kick's Pusher WebSocket and forward chat messages."""
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
                msg = self._clean_text(payload.get("content", ""))
                if user and msg:
                    on_message(user, msg)

            elif event == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong"}))

        ws = websocket.WebSocketApp(url, on_message=_on_message)
        ws.run_forever()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_username(self) -> str:
        resp = requests.get(
            KICK_API_URL,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        resp.raise_for_status()
        data = resp.json().get("data", [resp.json()])
        return data[0].get("name")

    def _fetch_room_id(self, username: str) -> int:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(KICK_CHANNEL_URL.format(username=username))
        return resp.json().get("chatroom", {}).get("id")

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"https?://\S+|www\.\S+", "", text)   # URLs
        text = re.sub(r"\[emote:[^\]]*\]", "", text)         # Emotes
        return text.strip()