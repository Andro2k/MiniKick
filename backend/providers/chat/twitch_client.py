# backend\providers\chat\twitch_client.py

import logging
import requests
from backend.interfaces import TokenProvider

TWITCH_HELIX_BASE = "https://api.twitch.tv/helix"

class TwitchAPIClient:
    def __init__(self, auth_provider: TokenProvider, client_id: str = ""):
        self.auth_provider = auth_provider
        self.client_id = client_id
        self.session = requests.Session()

    def _get_headers(self) -> dict:
        tokens = self.auth_provider.get_tokens() if self.auth_provider else {}
        access_token = tokens.get("access_token", "")
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def fetch_user_data(self) -> dict:
        url = f"{TWITCH_HELIX_BASE}/users"
        headers = self._get_headers()
        try:
            resp = self.session.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                raise ValueError("No se encontraron datos de usuario en Twitch Helix API.")
            user_info = data[0]
            created_at_raw = user_info.get("created_at", "")
            created_at = created_at_raw[:10] if created_at_raw and len(created_at_raw) >= 10 else "-"
            return {
                "broadcaster_id": user_info.get("id", ""),
                "username": user_info.get("login", ""),
                "display_name": user_info.get("display_name", ""),
                "bio": user_info.get("description", ""),
                "avatar_url": user_info.get("profile_image_url", ""),
                "created_at": created_at,
                "platform": "twitch"
            }
        except Exception as e:
            logging.error("[TwitchAPI] Error en fetch_user_data: %s", e)
            raise e

    def post_chat_message(self, broadcaster_id: str, sender_id: str, message: str) -> bool:
        url = f"{TWITCH_HELIX_BASE}/chat/messages"
        headers = self._get_headers()
        payload = {
            "broadcaster_id": broadcaster_id,
            "sender_id": sender_id,
            "message": message
        }
        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True
            logging.warning("[TwitchAPI] Fallo enviando mensaje Helix HTTP %s: %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logging.error("[TwitchAPI] Excepción al enviar mensaje a Twitch: %s", e)
            return False

    def delete_chat_message(self, broadcaster_id: str, moderator_id: str, message_id: str) -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/chat?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}&message_id={message_id}"
        headers = self._get_headers()
        try:
            resp = self.session.delete(url, headers=headers, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            logging.error("[TwitchAPI] Error eliminando mensaje en Twitch: %s", e)
            return False

    def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str = "") -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}"
        headers = self._get_headers()
        payload = {
            "data": {
                "user_id": user_id,
                "duration": duration_seconds,
                "reason": reason or "Timeout aplicado por MiniKick AutoMod"
            }
        }
        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=10)
            return resp.status_code in (200, 202)
        except Exception as e:
            logging.error("[TwitchAPI] Error aplicando timeout en Twitch: %s", e)
            return False

    def ban_user(self, broadcaster_id: str, moderator_id: str, user_id: str, reason: str = "") -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}"
        headers = self._get_headers()
        payload = {
            "data": {
                "user_id": user_id,
                "reason": reason or "Ban aplicado por MiniKick AutoMod"
            }
        }
        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=10)
            return resp.status_code in (200, 202)
        except Exception as e:
            logging.error("[TwitchAPI] Error aplicando ban permanente en Twitch: %s", e)
            return False
