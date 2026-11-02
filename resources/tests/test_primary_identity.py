# resources\tests\test_primary_identity.py

from pathlib import Path

from backend.config.toml_config_provider import CONFIG_FILE_NAME, TomlConfigProvider
from backend.database.database_manager import DatabaseManager
from backend.services.system.identity import pick_primary_identity, resolve_primary_identity


class _Config:
    def __init__(self, values):
        self.values = values

    def load_string(self, key, default=""):
        return self.values.get(key, default)


def test_profiles_have_priority_in_platform_order():
    profiles = {"twitch": {"username": "TwitchUser"}, "kick": {"login": "@KickLogin"}}
    assert pick_primary_identity(profiles, _Config({"tiktok_target_channel": "@tt"})) == "KickLogin"


def test_empty_or_blank_profiles_fall_back_to_configured_channels():
    profiles = {"kick": {"username": "   "}, "twitch": {}}
    config = _Config({"tiktok_target_channel": " @tiktoker ", "youtube_target_channel": "ytchannel"})
    assert pick_primary_identity(profiles, config) == "tiktoker"


def test_youtube_target_is_used_when_there_is_no_tiktok_target():
    config = _Config({"youtube_target_channel": " ytchannel "})
    assert pick_primary_identity({}, config) == "ytchannel"


def test_nothing_available_returns_empty_text():
    assert pick_primary_identity({}, None) == ""
    assert pick_primary_identity({}, _Config({})) == ""


def test_resolver_reads_channels_from_the_toml_file_not_from_sqlite(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    db = DatabaseManager()
    with db.get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tiktok_target_channel', 'viejo_sqlite')")
        conn.commit()
    config = TomlConfigProvider(Path(db.db_name).with_name(CONFIG_FILE_NAME))
    config.save_string("tiktok_target_channel", "@actual_toml")

    assert resolve_primary_identity() == "actual_toml"


def test_resolver_prefers_the_cached_channel_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    db = DatabaseManager()
    db.save_channel_profile("kick", {"username": "StreamerKick", "followers": 3})

    assert resolve_primary_identity() == "StreamerKick"


def test_resolver_never_raises(monkeypatch):
    import backend.database as database

    def broken(*_args, **_kwargs):
        raise RuntimeError("sin disco")

    monkeypatch.setattr(database, "DatabaseManager", broken)
    assert resolve_primary_identity() == ""
