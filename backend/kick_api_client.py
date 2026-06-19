# backend/kick_api_client.py

import sys
import time
import cloudscraper
import requests
from backend.interfaces.auth_interfaces import TokenProvider

KICK_API_URL = "https://api.kick.com/public/v1/users"
KICK_CHANNEL_URL = "https://kick.com/api/v1/channels/{slug}"
KICK_REWARDS_URL = "https://api.kick.com/public/v1/channels/rewards"
KICK_REDEMPTIONS_URL = "https://api.kick.com/public/v1/channels/rewards/redemptions"

class ScraperFactory:
    @staticmethod
    def create() -> cloudscraper.CloudScraper:
        scraper = cloudscraper.create_scraper()
        
        if sys.platform.startswith("linux"):
            ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        elif sys.platform == "darwin":
            ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        else:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
        scraper.headers.update({'User-Agent': ua})
        return scraper

class KickAPIClient:
    def __init__(self, auth_provider: TokenProvider):
        self.auth_provider = auth_provider
        self.scraper = ScraperFactory.create()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        tokens = self.auth_provider.get_tokens()
        access_token = tokens.get("access_token", "")
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {access_token}"
        
        try:
            response = self.scraper.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                self.auth_provider.refresh_token()
                tokens = self.auth_provider.get_tokens()
                headers["Authorization"] = f"Bearer {tokens.get('access_token', '')}"

                retry_response = self.scraper.request(method, url, headers=headers, **kwargs)
                retry_response.raise_for_status()
                return retry_response
            raise e

    def fetch_user_data(self) -> dict:
        username = self._fetch_authenticated_username()
        channel_slug = self._generate_channel_slug(username)
        channel_data = self._fetch_channel_details(channel_slug)
        return self._map_channel_data(username, channel_data)

    def _fetch_authenticated_username(self) -> str:
        resp = self._request("GET", KICK_API_URL, timeout=10)
        data = resp.json().get("data", [resp.json()])
        return data[0].get("name")

    def _generate_channel_slug(self, username: str) -> str:
        return username.replace("_", "-").replace(" ", "")

    def _fetch_channel_details(self, slug: str, max_retries: int = 3) -> dict:
        url = KICK_CHANNEL_URL.format(slug=slug)
        last_status_code = None
        
        for attempt in range(max_retries):
            channel_resp = self.scraper.get(url)
            last_status_code = channel_resp.status_code
            
            if last_status_code == 200:
                return channel_resp.json()
                
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                
        raise ValueError(f"Channel not found: '{slug}'. Retries exhausted ({max_retries}). HTTP Status: {last_status_code}")

    def _map_channel_data(self, username: str, channel_data: dict) -> dict:
        user_data = channel_data.get("user", {})
        chatroom_data = channel_data.get("chatroom", {})
        categories = channel_data.get("recent_categories", [])
        last_category = categories[0].get("name", "") if categories else ""     
        is_verified = channel_data.get("verified") is not None
        raw_bio = user_data.get("bio", "")
        clean_bio = " ".join(str(raw_bio).splitlines()) if raw_bio else ""

        return {
            "broadcaster_id": user_data.get("id", 0),
            "username": user_data.get("username", username),
            "bio": clean_bio,
            "room_id": chatroom_data.get("id", "-"),
            "followers": channel_data.get("followersCount", 0),
            "is_verified": is_verified,
            "is_affiliate": channel_data.get("is_affiliate", False),
            "vod_enabled": channel_data.get("vod_enabled", False),
            "last_category": last_category,
            "playback_url": channel_data.get("playback_url", ""),
            "avatar_url": user_data.get("profile_pic", "")
        }

    def fetch_pending_redemptions(self, cursor: str = "") -> dict:
        url = f"{KICK_REDEMPTIONS_URL}?status=pending"
        if cursor:
            url += f"&cursor={cursor}"         
        return self._request("GET", url, timeout=10).json()

    def fetch_channel_rewards(self) -> dict:
        return self._request("GET", KICK_REWARDS_URL, timeout=10).json()

    def accept_redemptions(self, redemption_ids: list[str]) -> dict:
        if not redemption_ids:
            return {}    
        url = f"{KICK_REDEMPTIONS_URL}/accept"
        payload = {"ids": redemption_ids}
        return self._request("POST", url, json=payload, timeout=10).json()
    
    def post_chat_message(self, content: str, msg_type: str = "bot", broadcaster_id: int = None) -> dict:
        url = "https://api.kick.com/public/v1/chat"
        payload = {"content": content, "type": msg_type}
        
        if msg_type == "user" and broadcaster_id is not None:
            payload["broadcaster_user_id"] = broadcaster_id
            
        return self._request("POST", url, json=payload, timeout=10).json()
    
    def delete_chat_message(self, message_id: str) -> bool:
        url = f"https://api.kick.com/public/v1/chat/{message_id}"
        try:
            resp = self._request("DELETE", url, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            print(f"[KickAPI] Error deleting message: {e}")
            return False

    def timeout_user(self, broadcaster_id: int, user_id: int, duration_seconds: int) -> bool:
        duration_minutes = max(1, duration_seconds // 60) 
        url = "https://api.kick.com/public/v1/moderation/bans"
        payload = {
            "broadcaster_user_id": broadcaster_id,
            "user_id": user_id,
            "duration": duration_minutes
        }
        try:
            resp = self._request("POST", url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"[KickAPI] Error applying timeout: {e}")
            return False