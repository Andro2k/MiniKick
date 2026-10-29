# resources\tests\test_settings_storage_cache.py

import pytest

from backend.database.database_manager import DatabaseManager
from backend.database.settings_storage import SQLiteSettingsStorage


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    manager = DatabaseManager("settings_cache.db")
    SQLiteSettingsStorage._snapshots.clear()
    yield manager
    SQLiteSettingsStorage._snapshots.clear()


def _count_connections(manager, monkeypatch):
    opened = {"n": 0}
    original = manager._open_connection

    def counting():
        opened["n"] += 1
        return original()

    monkeypatch.setattr(manager, "_open_connection", counting)
    return opened


def test_repeated_reads_open_a_single_connection(db, monkeypatch):
    storage = SQLiteSettingsStorage(db)
    storage.save_string("tts_provider", "web")
    opened = _count_connections(db, monkeypatch)

    for _ in range(50):
        assert storage.load_string("tts_provider", "piper") == "web"
        assert storage.load_string("missing", "fallback") == "fallback"

    assert opened["n"] == 1


def test_write_is_visible_immediately_to_the_same_and_other_instances(db):
    first = SQLiteSettingsStorage(db)
    second = SQLiteSettingsStorage(db)
    assert first.load_string("music_loudness_normalization", "0") == "0"

    second.save_bool("music_loudness_normalization", True)

    assert first.load_bool("music_loudness_normalization") is True
    assert second.load_string("music_loudness_normalization") == "1"


def test_save_all_and_get_all_keep_bool_conversion(db):
    storage = SQLiteSettingsStorage(db)
    storage.save_all({"a": True, "b": False, "c": 42, "d": "texto"})

    assert storage.get_all() == {"a": True, "b": False, "c": "42", "d": "texto"}
    assert storage.load_string("c") == "42"


def test_delete_key_prefix_invalidates_cached_values(db):
    storage = SQLiteSettingsStorage(db)
    storage.save_all({"alert_a": "1", "alert_b": "x", "keep": "y"})
    assert storage.load_string("alert_b") == "x"

    storage.delete_key_prefix("alert_")

    assert storage.load_string("alert_a", "gone") == "gone"
    assert storage.load_string("alert_b", "gone") == "gone"
    assert storage.load_string("keep") == "y"


def test_load_bool_uses_default_only_when_key_is_missing(db):
    storage = SQLiteSettingsStorage(db)
    assert storage.load_bool("flag", True) is True
    storage.save_bool("flag", False)
    assert storage.load_bool("flag", True) is False
