# frontend\common\linkify.py

import re

_URL_RE = re.compile(r"(?:https?://|www\.)(?:(?!&(?:quot|#x27|lt|gt);)[^\s<>\"'])+", re.IGNORECASE)
_TAG_SPLIT_RE = re.compile(r"(<[^>]*>)")
_TRAILING_PUNCT = ".,;:!?)]}"


def _wrap_url(match: re.Match) -> str:
    raw = match.group(0)
    url = raw.rstrip(_TRAILING_PUNCT)
    trailing = raw[len(url):]
    href = url if url.lower().startswith("http") else f"https://{url}"
    return f'<a href="{href}">{url}</a>{trailing}'


def linkify_html(escaped_html: str) -> str:
    parts = _TAG_SPLIT_RE.split(escaped_html)
    return "".join(
        part if part.startswith("<") else _URL_RE.sub(_wrap_url, part)
        for part in parts
    )
