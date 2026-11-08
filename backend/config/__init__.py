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

PUSHER_WS_URL_TEMPLATE = "wss://ws-{cluster}.pusher.com/app/{key}?protocol=7&client=js&version=7.6.0"

KICK_API_BASE = "https://api.kick.com/public/v1"
KICK_API_URL = f"{KICK_API_BASE}/users"
KICK_CHANNELS_URL = f"{KICK_API_BASE}/channels"
KICK_REWARDS_URL = f"{KICK_API_BASE}/channels/rewards"
KICK_CHAT_URL = f"{KICK_API_BASE}/chat"
KICK_BANS_URL = f"{KICK_API_BASE}/moderation/bans"
KICK_CATEGORIES_URL = f"{KICK_API_BASE}/categories"
KICK_CATEGORIES_V2_URL = "https://api.kick.com/public/v2/categories"
KICK_CHANNEL_URL = "https://kick.com/api/v1/channels/{slug}"
KICK_POLLS_URL = "https://kick.com/api/v2/channels/{slug}/polls"
KICK_SUBCATEGORIES_URL = "https://kick.com/api/v1/subcategories"
KICK_AUTH_URL = "https://id.kick.com/oauth/authorize"
KICK_TOKEN_URL = "https://id.kick.com/oauth/token"

TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_HELIX_BASE = "https://api.twitch.tv/helix"
TWITCH_EVENTSUB_API_URL = f"{TWITCH_HELIX_BASE}/eventsub/subscriptions"

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
    "PUSHER_WS_URL_TEMPLATE",
    "KICK_API_BASE",
    "KICK_API_URL",
    "KICK_CHANNELS_URL",
    "KICK_REWARDS_URL",
    "KICK_CHAT_URL",
    "KICK_BANS_URL",
    "KICK_CATEGORIES_URL",
    "KICK_CATEGORIES_V2_URL",
    "KICK_CHANNEL_URL",
    "KICK_POLLS_URL",
    "KICK_SUBCATEGORIES_URL",
    "KICK_AUTH_URL",
    "KICK_TOKEN_URL",
    "TWITCH_AUTH_URL",
    "TWITCH_TOKEN_URL",
    "TWITCH_HELIX_BASE",
    "TWITCH_EVENTSUB_API_URL",
]