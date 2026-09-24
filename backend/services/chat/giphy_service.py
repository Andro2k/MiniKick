# backend/services/chat/giphy_service.py

import re
import urllib.parse
import urllib.request
import logging
from typing import Optional
from backend.utils.json_utils import fast_loads

try:
    from backend.config.api_keys import GIPHY_API_KEY as DEFAULT_GIPHY_API_KEY
except Exception:
    DEFAULT_GIPHY_API_KEY = ""

logger = logging.getLogger("minikick.services.chat.giphy")

class GiphyService:
    _URL_FINDER_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)
    _DIRECT_GIF_REGEX = re.compile(r"^https?://\S+\.(?:gif|webp)(?:\?\S*)?$", re.IGNORECASE)
    _GIPHY_PAGE_REGEX = re.compile(r"https?://(?:www\.)?giphy\.com/gifs/(?:[\w\-]+-)?([a-zA-Z0-9]+)", re.IGNORECASE)
    _GIPHY_MEDIA_REGEX = re.compile(r"https?://media\d*\.giphy\.com/media/(?:[^/]+/)?([a-zA-Z0-9]+)/", re.IGNORECASE)

    def __init__(self, api_key: str = "", max_cache_size: int = 128):
        self._api_key = api_key
        self._cache: dict[str, str] = {}
        self._max_cache_size = max_cache_size

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        self._api_key = (value or "").strip()

    def has_active_key(self, api_key_override: str = "") -> bool:
        return bool((api_key_override or self._api_key or DEFAULT_GIPHY_API_KEY).strip())

    def extract_gif_url(self, text: str) -> Optional[str]:
        raw = (text or "").strip()
        if not raw:
            return None

        page_match = self._GIPHY_PAGE_REGEX.search(raw)
        if page_match:
            gif_id = page_match.group(1)
            return f"https://media.giphy.com/media/{gif_id}/giphy.gif"

        media_match = self._GIPHY_MEDIA_REGEX.search(raw)
        if media_match:
            gif_id = media_match.group(1)
            return f"https://media.giphy.com/media/{gif_id}/giphy.gif"

        if self._DIRECT_GIF_REGEX.match(raw):
            return raw

        for match in self._URL_FINDER_REGEX.finditer(raw):
            url = match.group(0).rstrip(".,!?:;)'\"")
            if ".gif" in url.lower() or ".webp" in url.lower():
                if self._DIRECT_GIF_REGEX.match(url):
                    return url

        return None

    def resolve_gif(self, arg: str, api_key_override: str = "", allow_search: bool = True) -> Optional[str]:
        raw = (arg or "").strip()
        if not raw:
            return None

        extracted = self.extract_gif_url(raw)
        if extracted:
            return extracted
        if raw.startswith("http://") or raw.startswith("https://") or "http://" in raw or "https://" in raw:
            return None
        if not allow_search:
            return None

        clean_query = raw.strip().replace("\n", " ").replace("\r", " ")
        if not clean_query or len(clean_query) > 80:
            logger.debug("[GiphyService] Query rejected: empty or exceeds 80 characters (len=%d)", len(clean_query))
            return None

        active_key = (api_key_override or self._api_key or DEFAULT_GIPHY_API_KEY).strip()
        if not active_key:
            logger.debug("[GiphyService] Cannot search query '%s': No GIPHY API key configured.", clean_query)
            return None

        cache_key = clean_query.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        return self._search_giphy(clean_query, active_key, cache_key)

    def _search_giphy(self, query: str, api_key: str, cache_key: str) -> Optional[str]:
        if len(query) > 80 or "http" in query.lower():
            return None
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={encoded_query}&limit=1&rating=g"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MiniKick/1.6.0 (Chat Overlay GIF Client)"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status != 200:
                    logger.warning("[GiphyService] Giphy API returned HTTP %s for query '%s'", resp.status, query)
                    return None
                data = fast_loads(resp.read().decode("utf-8"))
                items = data.get("data", [])
                if not items:
                    logger.info("[GiphyService] No GIF results found for query '%s'", query)
                    return None

                first_gif = items[0]
                images = first_gif.get("images", {})
                gif_url = ""
                if "fixed_height" in images and images["fixed_height"].get("url"):
                    gif_url = images["fixed_height"]["url"]
                elif "original" in images and images["original"].get("url"):
                    gif_url = images["original"]["url"]

                if gif_url:
                    if len(self._cache) >= self._max_cache_size:
                        self._cache.pop(next(iter(self._cache)))
                    self._cache[cache_key] = gif_url
                    return gif_url

        except Exception as ex:
            logger.warning("[GiphyService] Error searching Giphy for query '%s': %s", query, ex)

        return None
