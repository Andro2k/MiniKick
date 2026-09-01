# backend\providers\chat\twitch_client.py

import logging
import requests
from backend.interfaces import TokenProvider
from backend.services.system.translation_service import TranslationService

logger = logging.getLogger("minikick.providers.twitch_client")

TWITCH_HELIX_BASE = "https://api.twitch.tv/helix"

class TwitchAPIClient:
    def __init__(self, auth_provider: TokenProvider, client_id: str = "", i18n=None):
        self.auth_provider = auth_provider
        self.client_id = client_id
        self.i18n = i18n or TranslationService()
        self.session = requests.Session()

    def is_authenticated(self) -> bool:
        if not self.auth_provider:
            return False
        tokens = self.auth_provider.get_tokens() if hasattr(self.auth_provider, "get_tokens") else {}
        return bool(tokens and tokens.get("access_token"))

    def _get_headers(self) -> dict:
        if not self.auth_provider:
            return {}
        if hasattr(self.auth_provider, "get_tokens"):
            tokens = self.auth_provider.get_tokens()
        elif hasattr(self.auth_provider, "load"):
            tokens = self.auth_provider.load()
        else:
            tokens = {}
        tokens = tokens or {}
        access_token = tokens.get("access_token", "")
        if not access_token:
            return {}
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", None)
        if headers is None:
            headers = self._get_headers()

        if not headers or "Authorization" not in headers:
            resp = requests.Response()
            resp.status_code = 401
            resp._content = b'{"error":"Unauthorized","status":401,"message":"Missing or invalid access token"}'
            return resp

        resp = self.session.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401 and self.auth_provider and hasattr(self.auth_provider, "refresh_token"):
            logger.info("[TwitchAPI] Token 401 recibido, intentando refrescar token...")
            try:
                new_tokens = self.auth_provider.refresh_token()
                if new_tokens and new_tokens.get("access_token"):
                    headers = self._get_headers()
                    resp = self.session.request(method, url, headers=headers, **kwargs)
            except Exception as refresh_err:
                logger.error("[TwitchAPI] Fallo al refrescar token tras 401: %s", refresh_err)

        return resp

    def fetch_user_data(self) -> dict:
        url = f"{TWITCH_HELIX_BASE}/users"
        try:
            resp = self._request("GET", url, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                err_msg = self.i18n.get("logs.twitch.user_not_found")
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
                "broadcaster_type": user_info.get("broadcaster_type", ""),
                "platform": "twitch"
            }
        except Exception as e:
            logger.error("[TwitchAPI] Error fetching user data: %s", e)
            raise e

    def fetch_channel_followers(self, broadcaster_id: str) -> int:
        if not broadcaster_id:
            return 0
        url = f"{TWITCH_HELIX_BASE}/channels/followers?broadcaster_id={broadcaster_id}&moderator_id={broadcaster_id}"
        try:
            resp = self._request("GET", url, timeout=8)
            if resp.status_code == 200:
                return resp.json().get("total", 0)
            logger.warning("[TwitchAPI] Failed fetching followers HTTP %s: %s", resp.status_code, resp.text)
            return 0
        except Exception as e:
            logger.error("[TwitchAPI] Error fetching channel followers: %s", e)
            return 0

    def fetch_full_channel_info(self, broadcaster_id: str = "") -> dict:
        try:
            user_info = self.fetch_user_data()
        except Exception as e:
            logger.warning("[TwitchAPI] Could not fetch user data: %s", e)
            return {}

        b_id = broadcaster_id or user_info.get("broadcaster_id", "")
        
        followers = 0
        category = "-"
        if b_id:
            try:
                followers = self.fetch_channel_followers(b_id)
            except Exception as e:
                logger.warning("[TwitchAPI] Could not fetch followers: %s", e)
            try:
                meta = self.get_channel_metadata(b_id)
                if meta and meta.get("game_name"):
                    category = meta.get("game_name", "-")
            except Exception as e:
                logger.warning("[TwitchAPI] Could not fetch metadata: %s", e)

        user_info["followers"] = followers
        user_info["category"] = category
        user_info["last_category"] = category
        return user_info

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
            logger.warning("[TwitchAPI] Failed sending Helix message HTTP %s: %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logger.error("[TwitchAPI] Exception sending message to Twitch: %s", e)
            return False

    def delete_chat_message(self, broadcaster_id: str, moderator_id: str, message_id: str) -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/chat?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}&message_id={message_id}"
        try:
            resp = self._request("DELETE", url, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            logger.error("[TwitchAPI] Error deleting message on Twitch: %s", e)
            return False

    def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str = "") -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}"
        default_reason = self.i18n.get("moderation.reasons.timeout")
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
            logger.error("[TwitchAPI] Error applying timeout on Twitch: %s", e)
            return False

    def ban_user(self, broadcaster_id: str, moderator_id: str, user_id: str, reason: str = "") -> bool:
        url = f"{TWITCH_HELIX_BASE}/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}"
        default_reason = self.i18n.get("moderation.reasons.ban")
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
            logger.error("[TwitchAPI] Error applying ban on Twitch: %s", e)
            return False

    def update_channel_metadata(self, broadcaster_id: str, title: str | None = None, game_id: str | None = None, broadcaster_language: str | None = None) -> bool:
        if not broadcaster_id:
            return False
        url = f"{TWITCH_HELIX_BASE}/channels?broadcaster_id={broadcaster_id}"
        payload = {}
        if title is not None and str(title).strip():
            payload["title"] = str(title).strip()
        if game_id is not None and str(game_id).strip():
            payload["game_id"] = str(game_id).strip()
        if broadcaster_language is not None and str(broadcaster_language).strip():
            payload["broadcaster_language"] = str(broadcaster_language).strip()

        if not payload:
            return False

        try:
            resp = self._request("PATCH", url, json=payload, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            logger.error("[TwitchAPI] Error updating channel metadata on Twitch: %s", e)
            return False

    def get_channel_metadata(self, broadcaster_id: str) -> dict:
        if not broadcaster_id:
            return {}
        url = f"{TWITCH_HELIX_BASE}/channels?broadcaster_id={broadcaster_id}"
        try:
            resp = self._request("GET", url, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data and isinstance(data, list):
                    item = data[0]
                    return {
                        "broadcaster_id": item.get("broadcaster_id", ""),
                        "broadcaster_name": item.get("broadcaster_name", ""),
                        "title": item.get("title", ""),
                        "game_id": item.get("game_id", ""),
                        "game_name": item.get("game_name", ""),
                        "broadcaster_language": item.get("broadcaster_language", "")
                    }
            return {}
        except Exception as e:
            logger.error("[TwitchAPI] Error fetching channel metadata on Twitch: %s", e)
            return {}

    def search_categories(self, query: str) -> list[dict]:
        if not query or not query.strip():
            return []
        url = f"{TWITCH_HELIX_BASE}/search/categories?query={requests.utils.quote(query.strip())}&first=50"
        try:
            resp = self._request("GET", url, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                return [
                    {
                        "id": item.get("id", ""),
                        "name": item.get("name", ""),
                        "thumbnail": item.get("box_art_url", "").replace("{width}", "52").replace("{height}", "72") if item.get("box_art_url") else ""
                    }
                    for item in data if item.get("name")
                ]
            return []
        except Exception as e:
            logger.error("[TwitchAPI] Error searching categories on Twitch: %s", e)
            return []

    def fetch_channel_rewards(self, broadcaster_id: str) -> dict:
        if not broadcaster_id:
            return {"data": []}
        url = f"{TWITCH_HELIX_BASE}/channel_points/custom_rewards?broadcaster_id={broadcaster_id}&only_manageable_rewards=false"
        try:
            resp = self._request("GET", url, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                normalized = []
                for item in data:
                    img = item.get("image", {}) or item.get("default_image", {})
                    img_url = img.get("url_4x") or img.get("url_2x") or img.get("url_1x") or ""
                    normalized.append({
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "cost": item.get("cost", 100),
                        "description": item.get("prompt", ""),
                        "background_color": item.get("background_color", "#9146FF"),
                        "is_user_input_required": item.get("is_user_input_required", False),
                        "is_enabled": item.get("is_enabled", True),
                        "image_url": img_url,
                        "platform": "twitch"
                    })
                return {"data": normalized}
            logger.warning("[TwitchAPI] Failed fetching channel points rewards HTTP %s: %s", resp.status_code, resp.text)
            return {"data": []}
        except Exception as e:
            logger.error("[TwitchAPI] Error fetching channel points rewards: %s", e)
            return {"data": []}

    def create_channel_reward(self, broadcaster_id: str, title: str, cost: int, description: str = "", background_color: str = "#9146FF", is_user_input_required: bool = False) -> dict:
        if not broadcaster_id:
            raise ValueError("Broadcaster ID es requerido para crear recompensas en Twitch")
        url = f"{TWITCH_HELIX_BASE}/channel_points/custom_rewards?broadcaster_id={broadcaster_id}"
        payload = {
            "title": title,
            "cost": int(cost),
            "prompt": description or "",
            "background_color": background_color if background_color.startswith("#") else f"#{background_color}",
            "is_user_input_required": bool(is_user_input_required),
            "is_enabled": True
        }
        try:
            resp = self._request("POST", url, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json().get("data", [])
                item = data[0] if data else {}
                return {
                    "data": {
                        "id": item.get("id", ""),
                        "title": item.get("title", title),
                        "cost": item.get("cost", cost),
                        "description": item.get("prompt", description),
                        "background_color": item.get("background_color", background_color),
                        "is_user_input_required": item.get("is_user_input_required", is_user_input_required),
                        "platform": "twitch"
                    }
                }
            err_msg = resp.json().get("message", resp.text) if resp.text else f"HTTP {resp.status_code}"
            raise ValueError(f"Error Twitch Helix ({resp.status_code}): {err_msg}")
        except Exception as e:
            logger.error("[TwitchAPI] Error creating reward on Twitch: %s", e)
            raise e

    def update_channel_reward(self, broadcaster_id: str, reward_id: str, payload: dict) -> dict:
        if not broadcaster_id or not reward_id:
            raise ValueError("Broadcaster ID y Reward ID son requeridos para actualizar recompensa")
        url = f"{TWITCH_HELIX_BASE}/channel_points/custom_rewards?broadcaster_id={broadcaster_id}&id={reward_id}"
        
        helix_payload = {}
        if "title" in payload:
            helix_payload["title"] = payload["title"]
        if "cost" in payload:
            helix_payload["cost"] = int(payload["cost"])
        if "description" in payload:
            helix_payload["prompt"] = payload["description"]
        elif "prompt" in payload:
            helix_payload["prompt"] = payload["prompt"]
        if "background_color" in payload:
            bg = payload["background_color"]
            helix_payload["background_color"] = bg if bg.startswith("#") else f"#{bg}"
        if "is_user_input_required" in payload:
            helix_payload["is_user_input_required"] = bool(payload["is_user_input_required"])
        if "is_enabled" in payload:
            helix_payload["is_enabled"] = bool(payload["is_enabled"])

        try:
            resp = self._request("PATCH", url, json=helix_payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                item = data[0] if data else {}
                return {
                    "data": {
                        "id": item.get("id", reward_id),
                        "title": item.get("title", payload.get("title", "")),
                        "cost": item.get("cost", payload.get("cost", 100)),
                        "description": item.get("prompt", payload.get("description", "")),
                        "background_color": item.get("background_color", payload.get("background_color", "#9146FF")),
                        "is_user_input_required": item.get("is_user_input_required", payload.get("is_user_input_required", False)),
                        "platform": "twitch"
                    }
                }
            err_msg = resp.json().get("message", resp.text) if resp.text else f"HTTP {resp.status_code}"
            raise ValueError(f"Error Twitch Helix ({resp.status_code}): {err_msg}")
        except Exception as e:
            logger.error("[TwitchAPI] Error updating reward on Twitch: %s", e)
            raise e

    def delete_channel_reward(self, broadcaster_id: str, reward_id: str) -> bool:
        if not broadcaster_id or not reward_id:
            return False
        url = f"{TWITCH_HELIX_BASE}/channel_points/custom_rewards?broadcaster_id={broadcaster_id}&id={reward_id}"
        try:
            resp = self._request("DELETE", url, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            logger.error("[TwitchAPI] Error deleting reward on Twitch: %s", e)
            return False
