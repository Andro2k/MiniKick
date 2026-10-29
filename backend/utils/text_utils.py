# backend\utils\text_utils.py

import re

_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")


def is_speakable_text(text: str) -> bool:
    if not text or not text.strip():
        return False
    cleaned = _URL_PATTERN.sub("", text).strip()
    return any(c.isalnum() for c in cleaned)
