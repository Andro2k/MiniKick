# backend\providers\chat\kick_client.py

import logging
import time
import cloudscraper
import requests
from backend.interfaces import TokenProvider

logger = logging.getLogger("minikick.providers.kick_client")

KICK_API_URL = "https://api.kick.com/public/v1/users"
KICK_CHANNEL_URL = "https://kick.com/api/v1/channels/{slug}"
KICK_REWARDS_URL = "https://api.kick.com/public/v1/channels/rewards"

class ScraperFactory:
    @staticmethod
    def create() -> cloudscraper.CloudScraper:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
        scraper.headers.update({
            'User-Agent': ua,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Sec-Ch-Ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        return scraper

class KickAPIClient:
    def __init__(self, auth_provider: TokenProvider):
        self.auth_provider = auth_provider
        self.scraper = ScraperFactory.create()
        self._cached_subcategories = []

    def is_authenticated(self) -> bool:
        tokens = self._get_tokens()
        return bool(tokens and tokens.get("access_token"))

    def _get_tokens(self) -> dict:
        if not self.auth_provider:
            return {}
        if hasattr(self.auth_provider, "get_tokens"):
            tokens = self.auth_provider.get_tokens()
        elif hasattr(self.auth_provider, "load"):
            tokens = self.auth_provider.load()
        else:
            tokens = {}
        return tokens or {}

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        tokens = self._get_tokens()
        access_token = tokens.get("access_token", "")
        
        headers = kwargs.pop("headers", {})
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        try:
            response = self.scraper.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401 and hasattr(self.auth_provider, "refresh_token"):
                self.auth_provider.refresh_token()
                tokens = self._get_tokens()
                if tokens.get("access_token"):
                    headers["Authorization"] = f"Bearer {tokens.get('access_token', '')}"
                    response = self.scraper.request(method, url, headers=headers, **kwargs)
                    response.raise_for_status()
                    return response
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
        created_at_raw = chatroom_data.get("created_at", "")
        created_at = created_at_raw[:10] if created_at_raw and len(created_at_raw) >= 10 else "-"

        return {
            "broadcaster_id": user_data.get("id", 0),
            "channel_id": channel_data.get("id") or chatroom_data.get("channel_id") or user_data.get("id", 0),
            "username": user_data.get("username", username),
            "bio": clean_bio,
            "room_id": chatroom_data.get("id", "-"),
            "followers": channel_data.get("followersCount", 0),
            "is_verified": is_verified,
            "is_affiliate": channel_data.get("is_affiliate", False),
            "vod_enabled": channel_data.get("vod_enabled", False),
            "last_category": last_category,
            "playback_url": channel_data.get("playback_url", ""),
            "avatar_url": user_data.get("profile_pic", ""),
            "created_at": created_at
        }

    def fetch_channel_rewards(self) -> dict:
        return self._request("GET", KICK_REWARDS_URL, timeout=10).json()

    def create_channel_reward(
        self,
        title: str,
        cost: int,
        description: str = "",
        background_color: str = "#00e701",
        is_user_input_required: bool = False,
        should_redemptions_skip_request_queue: bool = False,
        is_enabled: bool = True
    ) -> dict:
        payload = {
            "title": title,
            "cost": cost,
            "is_enabled": is_enabled
        }
        if description:
            payload["description"] = description
        if background_color:
            payload["background_color"] = background_color
        if is_user_input_required is not None:
            payload["is_user_input_required"] = is_user_input_required
        if should_redemptions_skip_request_queue is not None:
            payload["should_redemptions_skip_request_queue"] = should_redemptions_skip_request_queue

        return self._request("POST", KICK_REWARDS_URL, json=payload, timeout=10).json()

    def update_channel_reward(self, reward_id: str, payload: dict) -> dict:
        url = f"{KICK_REWARDS_URL}/{reward_id}"
        return self._request("PATCH", url, json=payload, timeout=10).json()

    def delete_channel_reward(self, reward_id: str) -> bool:
        url = f"{KICK_REWARDS_URL}/{reward_id}"
        resp = self._request("DELETE", url, timeout=10)
        return resp.status_code == 204
    
    def post_chat_message(self, content: str, msg_type: str = "bot", broadcaster_id: int | None = None) -> dict:
        url = "https://api.kick.com/public/v1/chat"
        payload = {"content": content, "type": msg_type}
        
        if msg_type == "user" and broadcaster_id is not None:
            payload["broadcaster_user_id"] = broadcaster_id
            
        try:
            return self._request("POST", url, json=payload, timeout=10).json()
        except Exception as e:
            logger.error("[KickAPI] Error posting chat message: %s", e)
            return {}
    
    def delete_chat_message(self, message_id: str) -> bool:
        url = f"https://api.kick.com/public/v1/chat/{message_id}"
        try:
            resp = self._request("DELETE", url, timeout=10)
            return resp.status_code == 204
        except Exception as e:
            logger.error("[KickAPI] Error deleting message: %s", e)
            return False

    def timeout_user(self, broadcaster_id: int, user_id: int, duration_minutes: int) -> bool:
        url = "https://api.kick.com/public/v1/moderation/bans"
        payload = {
            "broadcaster_user_id": broadcaster_id,
            "user_id": user_id,
            "duration": max(1, min(duration_minutes, 10080))
        }
        try:
            resp = self._request("POST", url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error("[KickAPI] Error applying timeout: %s", e)
            return False

    def ban_user(self, broadcaster_id: int, user_id: int) -> bool:
        url = "https://api.kick.com/public/v1/moderation/bans"
        payload = {
            "broadcaster_user_id": broadcaster_id,
            "user_id": user_id
        }
        try:
            resp = self._request("POST", url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error("[KickAPI] Error applying ban: %s", e)
            return False

    def fetch_stream_status(self, slug: str) -> dict:
        try:
            data = self._fetch_channel_details(slug)
            livestream = data.get("livestream")
            is_live = livestream is not None
            title = livestream.get("session_title", "") if is_live else ""
            
            category = ""
            if is_live:
                categories = livestream.get("categories", [])
                if categories:
                    category = categories[0].get("name", "")
            else:
                recent_categories = data.get("recent_categories", [])
                if recent_categories:
                    category = recent_categories[0].get("name", "")
                    
            return {
                "is_live": is_live,
                "title": title,
                "category": category
            }
        except Exception as e:
            logger.error("[KickAPIClient] Error fetching stream status for %s: %s", slug, e)
            return {
                "is_live": False,
                "title": "",
                "category": ""
            }

    def update_channel_metadata(self, category_id: int | None = None, stream_title: str | None = None, custom_tags: list[str] | None = None) -> bool:
        url = "https://api.kick.com/public/v1/channels"
        payload = {}
        if category_id is not None:
            try:
                cid = int(category_id)
                if cid > 0:
                    payload["category_id"] = cid
            except (ValueError, TypeError):
                pass
        if stream_title is not None and str(stream_title).strip():
            payload["stream_title"] = str(stream_title).strip()
        if custom_tags is not None:
            payload["custom_tags"] = custom_tags[:10]

        if not payload:
            return False

        try:
            resp = self._request("PATCH", url, json=payload, timeout=10)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error("[KickAPI] Error updating channel metadata: %s", e)
            return False

    def get_channel_metadata(self) -> dict:
        url = "https://api.kick.com/public/v1/channels"
        try:
            resp = self._request("GET", url, timeout=10)
            if resp.status_code == 200:
                body = resp.json()
                data = body.get("data", [])
                item = None
                if isinstance(data, list) and data:
                    item = data[0]
                elif isinstance(data, dict):
                    item = data
                elif isinstance(body, dict) and "stream_title" in body:
                    item = body

                if item:
                    cat = item.get("category", {}) or {}
                    cat_id = cat.get("id") or item.get("category_id")
                    cat_name = cat.get("name") or item.get("category_name", "")
                    title = item.get("stream_title", "")
                    if title or cat_name:
                        return {
                            "broadcaster_user_id": item.get("broadcaster_user_id"),
                            "slug": item.get("slug", ""),
                            "stream_title": title,
                            "category_id": cat_id,
                            "category_name": cat_name
                        }
        except Exception as e:
            logger.debug("[KickAPI] Official channel metadata failed, trying fallback: %s", e)

        try:
            slug = getattr(self, "_cached_slug", None)
            if not slug:
                username = self._fetch_authenticated_username()
                if username:
                    slug = self._generate_channel_slug(username)
                    self._cached_slug = slug

            if slug:
                channel_data = self._fetch_channel_details(slug)
                livestream = channel_data.get("livestream")
                is_live = livestream is not None
                
                title = ""
                cat_id = None
                cat_name = ""

                if is_live and livestream:
                    title = livestream.get("session_title", "")
                    cats = livestream.get("categories", [])
                    if cats:
                        cat_name = cats[0].get("name", "")
                        cat_id = cats[0].get("id")
                else:
                    prev_streams = channel_data.get("previous_livestreams", [])
                    if prev_streams:
                        title = prev_streams[0].get("session_title", "")
                    recent_cats = channel_data.get("recent_categories", [])
                    if recent_cats:
                        cat_name = recent_cats[0].get("name", "")
                        cat_id = recent_cats[0].get("id")

                user = channel_data.get("user", {})
                return {
                    "broadcaster_user_id": user.get("id"),
                    "slug": channel_data.get("slug", slug),
                    "stream_title": title,
                    "category_id": cat_id,
                    "category_name": cat_name
                }
        except Exception as e:
            logger.error("[KickAPI] Error in fallback channel metadata: %s", e)

        return {}

    def search_categories(self, query: str) -> list[dict]:
        if not query or not query.strip():
            return []
        
        q = query.strip()
        encoded_q = requests.utils.quote(q)
        
        try:
            url = f"https://api.kick.com/public/v1/categories?q={encoded_q}"
            resp = self._request("GET", url, timeout=8)
            if resp.status_code == 200:
                res_data = resp.json()
                items = res_data.get("data", []) if isinstance(res_data, dict) else res_data
                if isinstance(items, list) and items:
                    return [
                        {
                            "id": item.get("id"),
                            "name": item.get("name", ""),
                            "thumbnail": item.get("thumbnail", "") or item.get("banner", "")
                        }
                        for item in items if item.get("name")
                    ]
        except Exception as e:
            logger.debug("[KickAPI] Error in public v1 category search: %s", e)

        try:
            url = f"https://api.kick.com/public/v2/categories?name={encoded_q}&limit=50"
            resp = self._request("GET", url, timeout=8)
            if resp.status_code == 200:
                res_data = resp.json()
                items = res_data.get("data", []) if isinstance(res_data, dict) else res_data
                if isinstance(items, list) and items:
                    return [
                        {
                            "id": item.get("id"),
                            "name": item.get("name", ""),
                            "thumbnail": item.get("thumbnail", "") or item.get("banner", "")
                        }
                        for item in items if item.get("name")
                    ]
        except Exception as e:
            logger.debug("[KickAPI] Error in public v2 category search: %s", e)

        try:
            if not getattr(self, "_cached_subcategories", None):
                self._cached_subcategories = []
                for page in (1, 2, 3):
                    resp = self.scraper.get(f"https://kick.com/api/v1/subcategories?page={page}&limit=100", timeout=5)
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        if isinstance(data, list):
                            self._cached_subcategories.extend(data)
            
            q_lower = q.lower()
            results = []
            for item in self._cached_subcategories:
                name = item.get("name", "")
                if name and q_lower in name.lower():
                    results.append({
                        "id": item.get("id"),
                        "name": name,
                        "thumbnail": item.get("banner", {}).get("url", "") if isinstance(item.get("banner"), dict) else ""
                    })
            if results:
                return results
        except Exception as e:
            logger.debug("[KickAPI] Error in fallback subcategories search: %s", e)

        return []
