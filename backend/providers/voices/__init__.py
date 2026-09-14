# backend\providers\voices\__init__.py

from .local_provider import LocalTTSProvider
from .online_provider import WebTTSProvider
from .piper_provider import PiperTTSProvider

__all__ = [
    "LocalTTSProvider",
    "WebTTSProvider",
    "PiperTTSProvider",
]
