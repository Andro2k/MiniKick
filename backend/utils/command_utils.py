# backend\utils\command_utils.py

import re

_VALID_TRIGGER_RE = re.compile(r"^![a-z0-9_-]*$")
_COMPLETE_TRIGGER_RE = re.compile(r"^![a-z0-9_-]+$")

def sanitize_command_trigger(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = raw_text.strip().lower()
    if not text:
        return ""

    has_exclamation = text.startswith("!")
    body = text[1:] if has_exclamation else text
    body = re.sub(r"\s+", "_", body)
    body = re.sub(r"[^a-z0-9_-]", "", body)
    body = re.sub(r"_+", "_", body)

    return f"!{body}"


def validate_trigger_prefix(text: str) -> bool:
    if not text or not text.strip():
        return True
    return bool(_VALID_TRIGGER_RE.match(text))


def is_complete_valid_trigger(text: str) -> bool:
    if not text:
        return False
    return bool(_COMPLETE_TRIGGER_RE.match(text))
