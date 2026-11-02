# backend\utils\emote_parser.py

import re

from backend.utils.json_utils import fast_loads

_KICK_EMOTE_REGEX = re.compile(r"\[emote:(?:(\d+):)?([^\]]+)\]")
_EMOJI_REGEX = re.compile(r"[\U00010000-\U0010ffff\u2600-\u27bf]")

_KICK_EMOTE_URL = "https://files.kick.com/emotes/{id}/fullsize"
_TWITCH_EMOTE_URL = "https://static-cdn.jtvnw.net/emoticons/v2/{id}/default/dark/2.0"


def _emote(kind: str, src: str, name: str) -> dict:
    return {"type": kind, "src": src, "name": name}


def extract_emotes(content: str, platform: str = "kick", emotes_tag: str = "") -> list[dict]:
    emotes: list[dict] = []

    for e_id, e_name in _KICK_EMOTE_REGEX.findall(content):
        if e_id:
            emotes.append(_emote("image", _KICK_EMOTE_URL.format(id=e_id), e_name))
        else:
            emotes.append(_emote("text", e_name, e_name))

    if emotes_tag:
        if platform in ("youtube", "tiktok"):
            emotes.extend(_parse_json_emotes(emotes_tag, platform))
        elif platform == "twitch" and not emotes_tag.startswith("["):
            emotes.extend(_parse_twitch_emotes(emotes_tag))

    for emoji_char in _EMOJI_REGEX.findall(content):
        emotes.append(_emote("text", emoji_char, emoji_char))

    return emotes


def _parse_json_emotes(emotes_tag: str, platform: str) -> list[dict]:
    if not (isinstance(emotes_tag, str) and emotes_tag.startswith("[")):
        return []
    try:
        custom_emotes = fast_loads(emotes_tag)
    except Exception:
        return []
    return [
        _emote("image", em["url"], em.get("name", f"{platform}_emote"))
        for em in custom_emotes
        if isinstance(em, dict) and em.get("url")
    ]


def _parse_twitch_emotes(emotes_tag: str) -> list[dict]:
    result: list[dict] = []
    for group in emotes_tag.split("/"):
        if ":" not in group:
            continue
        e_id = group.split(":")[0]
        if e_id:
            result.append(_emote("image", _TWITCH_EMOTE_URL.format(id=e_id), f"twitch_{e_id}"))
    return result
