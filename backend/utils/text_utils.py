# backend\utils\text_utils.py

import re

_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")

_EMOJI_CORE = (
    "[0-9#*]\uFE0F?\u20E3"
    "|[\U0001F000-\U0001FAFF]"
    "|[\U000E0020-\U000E007F]"
    "|[\u2600-\u27BF]"
    "|[\u2B00-\u2BFF]"
    "|[\u231A\u231B\u2328\u23CF\u23E9-\u23F3\u23F8-\u23FA]"
    "|[\u24C2\u25AA\u25AB\u25B6\u25C0\u25FB-\u25FE\u2934\u2935\u3030\u303D\u3297\u3299]"
)
_EMOJI_PATTERN = re.compile(rf"\u200D?(?:{_EMOJI_CORE})\u200D?|[\uFE0E\uFE0F]")
_MULTI_SPACE_PATTERN = re.compile(r" {2,}")


def strip_emojis(text: str) -> str:
    if not text:
        return ""
    without_emojis = _EMOJI_PATTERN.sub(" ", text)
    return _MULTI_SPACE_PATTERN.sub(" ", without_emojis).strip()


def is_speakable_text(text: str) -> bool:
    if not text or not text.strip():
        return False
    cleaned = _URL_PATTERN.sub("", text).strip()
    return any(c.isalnum() for c in cleaned)
