# backend\utils\speech_text.py

import re

from .text_utils import strip_emojis

SPEECH_REPLACEMENTS: dict[str, str] = {
    "q": "que",
    "xq": "porque",
    "pq": "porque",
    "porq": "porque",
    "xk": "porque",
    "tmb": "también",
    "tbn": "también",
    "xfa": "por favor",
    "xfis": "por favor",
    "dnd": "donde",
    "cmo": "como",
    "grax": "gracias",
    "bn": "bien",
    "msj": "mensaje",
    "ntp": "no te preocupes",
    "salu2": "saludos",
    "pls": "plis",
    "plz": "plis",
    "gg": "yi yi",
    "gl": "yi el",
    "hf": "eich ef",
    "afk": "a efe ka",
    "omg": "o em yi",
    "stream": "estrim",
    "streams": "estrims",
    "streamer": "estrímer",
    "streamers": "estrímers",
    "follow": "fólou",
    "unfollow": "anfólou",
    "follower": "fólouer",
    "followers": "fólouers",
    "raid": "reid",
    "hype": "jaip",
    "noob": "nub",
    "like": "láik",
    "likes": "láiks",
    "hater": "jéiter",
    "haters": "jéiters",
    "build": "bild",
    "loot": "lut",
    "feed": "fid",
    "gameplay": "géimplei",
}

_REPLACEMENT_PATTERN = re.compile(
    r"(?<![\w&/'\-])(?:"
    + "|".join(re.escape(word) for word in sorted(SPEECH_REPLACEMENTS, key=len, reverse=True))
    + r")(?![\w&/'\-])",
    re.IGNORECASE,
)
_MENTION_OR_HASHTAG_PATTERN = re.compile(r"(?<!\w)[@#]+(?=\w)")
_INNER_UNDERSCORE_PATTERN = re.compile(r"(?<=\w)_+(?=\w)")
_NAME_DECORATION_PATTERN = re.compile(r"^[xX]{1,2}[_\-.\s]+|[_\-.\s]+[xX]{1,2}$")
_NAME_SEPARATOR_PATTERN = re.compile(r"[_\-.]+")
_CAMEL_LOWER_UPPER_PATTERN = re.compile(r"(?<=[a-záéíóúüñ])(?=[A-ZÁÉÍÓÚÜÑ])")
_CAMEL_ACRONYM_PATTERN = re.compile(r"(?<=[A-ZÁÉÍÓÚÜÑ])(?=[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ])")
_TRAILING_DIGITS_PATTERN = re.compile(r"\s*\d{3,}$")
_SPACES_PATTERN = re.compile(r"\s+")


def apply_pronunciations(text: str) -> str:
    return _REPLACEMENT_PATTERN.sub(lambda match: SPEECH_REPLACEMENTS[match.group(0).lower()], text)


def normalize_symbols_for_speech(text: str) -> str:
    without_marks = _MENTION_OR_HASHTAG_PATTERN.sub("", text)
    return _INNER_UNDERSCORE_PATTERN.sub(" ", without_marks)


def speakable_username(name: str) -> str:
    base = strip_emojis(name or "")
    cleaned = _NAME_DECORATION_PATTERN.sub("", base)
    cleaned = _NAME_SEPARATOR_PATTERN.sub(" ", cleaned)
    cleaned = _CAMEL_LOWER_UPPER_PATTERN.sub(" ", cleaned)
    cleaned = _CAMEL_ACRONYM_PATTERN.sub(" ", cleaned)
    cleaned = _TRAILING_DIGITS_PATTERN.sub("", cleaned)
    cleaned = _SPACES_PATTERN.sub(" ", cleaned).strip()
    return cleaned or base.strip()
