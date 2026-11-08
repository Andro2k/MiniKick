# backend\config\__init__.py

import logging
from dataclasses import dataclass

from .version import APP_VERSION
from .locale_defaults import DEFAULT_DICTIONARY
from .toml_config_provider import CONFIG_FILE_NAME, TomlConfigProvider

logger = logging.getLogger("minikick.config")

DEFAULT_REDIRECT_URI = "http://localhost:8080/auth/callback"
_DEFAULT_KICK_PUSHER_CLUSTER = "us2"
_DEFAULT_KICK_PUSHER_KEYS = ("34bf7a0ff419a2a775b9", "32cbd69e4b950bf97679")

try:
    from . import api_keys as _keys
except ImportError:
    _keys = None
    logger.warning("backend/config/api_keys.py not found; using empty credentials.")

API_KEYS_MISSING = _keys is None


def _key(name: str, default: str = "") -> str:
    return getattr(_keys, name, default)


@dataclass(frozen=True)
class PusherConfig:
    cluster: str
    keys: tuple[str, ...]


_pusher_cluster = _key("KICK_PUSHER_CLUSTER", _DEFAULT_KICK_PUSHER_CLUSTER).strip()
_pusher_key = _key("KICK_PUSHER_KEY").strip()
KICK_PUSHER = PusherConfig(
    cluster=_pusher_cluster or _DEFAULT_KICK_PUSHER_CLUSTER,
    keys=(_pusher_key,) if _pusher_key else _DEFAULT_KICK_PUSHER_KEYS,
)

KICK_CLIENT_ID = _key("KICK_CLIENT_ID")
KICK_CLIENT_SECRET = _key("KICK_CLIENT_SECRET")
KICK_REDIRECT_URI = _key("KICK_REDIRECT_URI", DEFAULT_REDIRECT_URI)
TWITCH_CLIENT_ID = _key("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = _key("TWITCH_CLIENT_SECRET")
TWITCH_REDIRECT_URI = _key("TWITCH_REDIRECT_URI", DEFAULT_REDIRECT_URI)
DISCORD_WEBHOOK_URL = _key("DISCORD_WEBHOOK_URL")
SIGN_API_KEY = _key("SIGN_API_KEY")
GIPHY_API_KEY = _key("GIPHY_API_KEY")

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
    "GIPHY_API_KEY",
    "CONFIG_FILE_NAME",
    "TomlConfigProvider",
    "DEFAULT_DICTIONARY",
]