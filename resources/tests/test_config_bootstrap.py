# resources\tests\test_config_bootstrap.py

import pytest

from backend.database.database_manager import DatabaseManager
from bootstrap.config import CONFIG_FILE_NAME, create_config_provider


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return DatabaseManager("config_bootstrap.db")


def _seed(db, rows):
    with db.get_connection() as conn:
        conn.executemany("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", rows)
        conn.commit()


def _legacy_rows(db):
    with db.get_connection() as conn:
        return dict(conn.execute("SELECT key, value FROM settings").fetchall())


def test_existing_sqlite_settings_are_imported_once(db):
    _seed(db, [("app_language", "en"), ("tts_enabled", "1"), ("music_volume", "65")])

    config = create_config_provider(db)

    assert config.load_string("app_language") == "en"
    assert config.load_bool("tts_enabled") is True
    assert config.load_string("music_volume") == "65"
    assert (db.db_name and (__import__("pathlib").Path(db.db_name).with_name(CONFIG_FILE_NAME)).exists())
    assert _legacy_rows(db)["settings_migrated_to_toml"] == "1"


def test_second_start_uses_the_toml_file_and_ignores_sqlite(db):
    _seed(db, [("app_language", "en")])
    create_config_provider(db).save_string("app_language", "es")
    _seed(db, [("app_language", "fr")])

    assert create_config_provider(db).load_string("app_language") == "es"


def test_deleted_toml_is_not_reimported_after_the_marker_exists(db):
    from pathlib import Path
    _seed(db, [("app_language", "en")])
    create_config_provider(db)
    Path(db.db_name).with_name(CONFIG_FILE_NAME).unlink()

    assert create_config_provider(db).load_string("app_language", "es") == "es"


def test_fresh_install_creates_no_file_and_no_marker(db):
    from pathlib import Path
    config = create_config_provider(db)

    assert config.get_all() == {}
    assert not Path(db.db_name).with_name(CONFIG_FILE_NAME).exists()
    assert "settings_migrated_to_toml" not in _legacy_rows(db)
