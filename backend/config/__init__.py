# backend\config\__init__.py

import logging

from .version import APP_VERSION
from .locale_defaults import DEFAULT_DICTIONARY

logger = logging.getLogger("minikick.config")

try:
    from .api_keys import (
        KICK_CLIENT_ID,
        KICK_CLIENT_SECRET,
        KICK_REDIRECT_URI,
        KICK_PUSHER_CLUSTER,
        KICK_PUSHER_KEY,
        DISCORD_WEBHOOK_URL,
        TWITCH_CLIENT_ID,
        TWITCH_CLIENT_SECRET,
        SIGN_API_KEY,
    )
except ImportError:
    # api_keys.py está en .gitignore: un clon limpio (o CI) no lo tiene.
    # Se usan valores vacíos para que el backend pueda importarse; los logins no funcionarán.
    logger.warning("backend/config/api_keys.py not found; using empty credentials.")
    KICK_CLIENT_ID = ""
    KICK_CLIENT_SECRET = ""
    KICK_REDIRECT_URI = ""
    DISCORD_WEBHOOK_URL = ""
    TWITCH_CLIENT_ID = ""
    TWITCH_CLIENT_SECRET = ""
    SIGN_API_KEY = ""
    # Mismos valores que el fallback de main_window_core (se centralizarán en el Plan 2).
    KICK_PUSHER_CLUSTER = "us2"
    KICK_PUSHER_KEY = "32cbd69e4b950bf97679"

__all__ = [
    "APP_VERSION",
    "KICK_CLIENT_ID",
    "KICK_CLIENT_SECRET",
    "KICK_REDIRECT_URI",
    "KICK_PUSHER_CLUSTER",
    "KICK_PUSHER_KEY",
    "DISCORD_WEBHOOK_URL",
    "TWITCH_CLIENT_ID",
    "TWITCH_CLIENT_SECRET",
    "SIGN_API_KEY",
    "DEFAULT_DICTIONARY",
]
