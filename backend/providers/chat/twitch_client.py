# backend\providers\chat\twitch_client.py

import logging
import requests
from backend.interfaces import TokenProvider

TWITCH_HELIX_BASE = "https://api.twitch.tv/helix"

class TwitchAPIClient:
    def __init__(self, auth_provider: TokenProvider, client_id: str = "", i18n=None):
        self.auth_provider = auth_provider
        self.client_id = client_id
        self.i18n = i18n
        self.session = requests.Session()

    def _get_headers(self) -> dict:
        tokens = self.auth_provider.get_tokens() if self.auth_provider else {}
        access_token = tokens.get("access_token", "")
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", None)
        if headers is None:
            headers = self._get_headers()

        resp = self.session.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401 and self.auth_provider and hasattr(self.auth_provider, "refresh_token"):
            logging.info("[TwitchAPI] Token 401 recibido, intentando refrescar token...")
            try:
                self.auth_provider.refresh_token()
                headers = self._get_headers()
                resp = self.session.request(method, url, headers=headers, **kwargs)
            except Exception as refresh_err:
                logging.error("[TwitchAPI] Fallo al refrescar token tras 401: %s", refresh_err)

        return resp

    def fetch_user_data(self) -> dict:
        url = f"{TWITCH_HELIX_BASE}/users"
        try:
            resp = self._request("GET", url, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                err_msg = self.i18n.get("logs.twitch.user_not_found") if self.i18n else "User not found"
                raise ValueError(err_msg)
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
            logging.error("[TwitchAPI] Error fetching user data: %s", e)
            raise e

    def post_chat_message(self, broadcaster_id: str, sender_id: str, message: str) -> bool:
        url = f"{TWITCH_HELIX_BASE}/chat/messages"
        payload = {
            "broadcaster_id": broadcaster_id,
            "sender_id": sender_id,
            "message": message
        }
        try:
            resp = self._request("POST", url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            logging.warning("[TwitchAPI] Failed sending Helix message HTTP %s: %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logging.error("[TwitchAPI] Exception sending message to Twitch: %s", e)
            return False

    def delete_chat_message(self, broadcaster_id: str, moderator_id: str, message_id: str) -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/chat?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}&message_id={message_id}"
        try:
            resp = self._request("DELETE", url, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            logging.error("[TwitchAPI] Error deleting message on Twitch: %s", e)
            return False

    def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str = "") -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}"
        default_reason = self.i18n.get("moderation.reasons.timeout") if self.i18n else ""
        payload = {
            "data": {
                "user_id": user_id,
                "duration": duration_seconds,
                "reason": reason or default_reason
            }
        }
        try:
            resp = self._request("POST", url, json=payload, timeout=10)
            return resp.status_code in (200, 202)
        except Exception as e:
            logging.error("[TwitchAPI] Error applying timeout on Twitch: %s", e)
            return False

    def ban_user(self, broadcaster_id: str, moderator_id: str, user_id: str, reason: str = "") -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}"
        default_reason = self.i18n.get("moderation.reasons.ban") if self.i18n else ""
        payload = {
            "data": {
                "user_id": user_id,
                "reason": reason or default_reason
            }
        }
        try:
            resp = self._request("POST", url, json=payload, timeout=10)
            return resp.status_code in (200, 202)
        except Exception as e:
            logging.error("[TwitchAPI] Error applying ban on Twitch: %s", e)
            return False



