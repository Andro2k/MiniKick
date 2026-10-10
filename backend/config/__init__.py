# backend\config\__init__.py

import logging

from .version import APP_VERSION
from .locale_defaults import DEFAULT_DICTIONARY
from .pusher_config import KICK_PUSHER, PusherConfig

logger = logging.getLogger("minikick.config")

try:
    from .api_keys import (
        KICK_CLIENT_ID,
        KICK_CLIENT_SECRET,
        KICK_REDIRECT_URI,
        DISCORD_WEBHOOK_URL,
        TWITCH_CLIENT_ID,
        TWITCH_CLIENT_SECRET,
        SIGN_API_KEY,
    )
except ImportError:
    logger.warning("backend/config/api_keys.py not found; using empty credentials.")
    KICK_CLIENT_ID = ""
    KICK_CLIENT_SECRET = ""
    KICK_REDIRECT_URI = ""
    DISCORD_WEBHOOK_URL = ""
    TWITCH_CLIENT_ID = ""
    TWITCH_CLIENT_SECRET = ""
    SIGN_API_KEY = ""

__all__ = [
    "APP_VERSION",
    "KICK_CLIENT_ID",
    "KICK_CLIENT_SECRET",
    "KICK_REDIRECT_URI",
    "KICK_PUSHER",
    "PusherConfig",
    "DISCORD_WEBHOOK_URL",
    "TWITCH_CLIENT_ID",
    "TWITCH_CLIENT_SECRET",
    "SIGN_API_KEY",
    "DEFAULT_DICTIONARY",
]
