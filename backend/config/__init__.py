# backend\config\__init__.py

import logging

from .version import APP_VERSION
from .locale_defaults import DEFAULT_DICTIONARY
from .pusher_config import KICK_PUSHER, PusherConfig

logger = logging.getLogger("minikick.config")

DEFAULT_REDIRECT_URI = "http://localhost:8080/auth/callback"

try:
    from . import api_keys as _keys
except ImportError:
    _keys = None
    logger.warning("backend/config/api_keys.py not found; using empty credentials.")

API_KEYS_MISSING = _keys is None


def _key(name: str, default: str = "") -> str:
    return getattr(_keys, name, default)


KICK_CLIENT_ID = _key("KICK_CLIENT_ID")
KICK_CLIENT_SECRET = _key("KICK_CLIENT_SECRET")
KICK_REDIRECT_URI = _key("KICK_REDIRECT_URI", DEFAULT_REDIRECT_URI)
TWITCH_CLIENT_ID = _key("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = _key("TWITCH_CLIENT_SECRET")
TWITCH_REDIRECT_URI = _key("TWITCH_REDIRECT_URI", DEFAULT_REDIRECT_URI)
DISCORD_WEBHOOK_URL = _key("DISCORD_WEBHOOK_URL")
SIGN_API_KEY = _key("SIGN_API_KEY")

__all__ = [
    "APP_VERSION",
    "API_KEYS_MISSING",
    "KICK_CLIENT_ID",
    "KICK_CLIENT_SECRET",
    "KICK_REDIRECT_URI",
    "KICK_PUSHER",
    "PusherConfig",
    "DISCORD_WEBHOOK_URL",
    "TWITCH_CLIENT_ID",
    "TWITCH_CLIENT_SECRET",
    "TWITCH_REDIRECT_URI",
    "SIGN_API_KEY",
    "DEFAULT_DICTIONARY",
]