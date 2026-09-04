# backend\providers\voices\__init__.py

from .tts_local import LocalTTSProvider
from .tts_online import WebTTSProvider
from .tts_piper import PiperTTSProvider

__all__ = [
    "LocalTTSProvider",
    "WebTTSProvider",
    "PiperTTSProvider",
]
