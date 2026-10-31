# backend\services\system\identity.py

from pathlib import Path
from typing import Mapping

from backend.config.toml_config_provider import CONFIG_FILE_NAME, TomlConfigProvider
from backend.interfaces import IConfigProvider

_PROFILE_PLATFORMS = ("kick", "twitch", "tiktok", "youtube")


def pick_primary_identity(profiles: Mapping[str, dict], config: IConfigProvider | None = None) -> str:
    for platform in _PROFILE_PLATFORMS:
        profile = profiles.get(platform) or {}
        name = (profile.get("username") or profile.get("login") or "").strip()
        if name:
            return name.lstrip("@")

    if config is not None:
        tiktok_target = (config.load_string("tiktok_target_channel", "") or "").strip()
        if tiktok_target:
            return tiktok_target.lstrip("@")
        youtube_target = (config.load_string("youtube_target_channel", "") or "").strip()
        if youtube_target:
            return youtube_target
    return ""


def resolve_primary_identity() -> str:
    try:
        from backend.database import DatabaseManager
        db = DatabaseManager()
        config = TomlConfigProvider(Path(db.db_name).with_name(CONFIG_FILE_NAME))
        return pick_primary_identity(db.load_all_channel_profiles(), config)
    except Exception:
        return ""
