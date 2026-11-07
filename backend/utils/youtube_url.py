# backend\\utils\\youtube_url.py

import re
from typing import NamedTuple
from urllib.parse import parse_qs, urlparse

_YT_HOSTS = frozenset({
    "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
    "youtube-nocookie.com", "www.youtube-nocookie.com", "youtu.be", "www.youtu.be",
})
_BARE_YT_LINK_RE = re.compile(r"^(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com)/", re.IGNORECASE)
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_ID_PATH_PREFIXES = frozenset({"shorts", "embed", "live", "v"})

KIND_SEARCH = "search"
KIND_YOUTUBE_VIDEO = "youtube_video"
KIND_LINK = "link"


class MusicQuery(NamedTuple):
    kind: str
    value: str


def _as_url(token: str) -> str | None:
    token = token.strip("<>()[]\"'")
    lowered = token.lower()
    if lowered.startswith(("http://", "https://")):
        return token
    if lowered.startswith("www.") or _BARE_YT_LINK_RE.match(token):
        return f"https://{token}"
    return None


def _youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in _YT_HOSTS:
        return None
    segments = [s for s in parsed.path.split("/") if s]
    candidate = None
    if host.endswith("youtu.be"):
        candidate = segments[0] if segments else None
    elif segments and segments[0] == "watch":
        candidate = (parse_qs(parsed.query).get("v") or [None])[0]
    elif len(segments) >= 2 and segments[0] in _ID_PATH_PREFIXES:
        candidate = segments[1]
    return candidate if candidate and _VIDEO_ID_RE.match(candidate) else None


def is_youtube_link(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in _YT_HOSTS


def classify_music_query(text: str) -> MusicQuery:
    text = (text or "").strip()
    first_token = text.split(maxsplit=1)[0] if text else ""
    url = _as_url(first_token) if first_token else None
    if url is None:
        return MusicQuery(KIND_SEARCH, text)

    video_id = _youtube_video_id(url)
    if video_id:
        return MusicQuery(KIND_YOUTUBE_VIDEO, f"https://www.youtube.com/watch?v={video_id}")
    return MusicQuery(KIND_LINK, url)
