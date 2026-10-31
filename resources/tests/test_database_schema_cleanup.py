# resources\tests\test_database_schema_cleanup.py

import pytest

from backend.database.database_manager import CURRENT_SCHEMA_VERSION, DatabaseManager
from backend.database.migrations import MIGRATIONS


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path


def _objects(db):
    with db.get_connection() as conn:
        return {(row[0], row[1]) for row in conn.execute("SELECT type, name FROM sqlite_master")}


def _version(db):
    with db.get_connection() as conn:
        return conn.execute("PRAGMA user_version").fetchone()[0]


def test_fresh_database_has_no_obsolete_timer_log_objects(home):
    db = DatabaseManager("fresh.db")

    names = {name for _kind, name in _objects(db)}
    assert "timer_execution_logs" not in names
    assert "prune_timer_logs" not in names
    assert not any(name.startswith("idx_timer_logs") for name in names)
    assert _version(db) == CURRENT_SCHEMA_VERSION == max(version for version, _ in MIGRATIONS)


def test_legacy_database_is_upgraded_and_loses_only_the_obsolete_log(home):
    db = DatabaseManager("legacy.db")
    with db.get_connection() as conn:
        conn.execute("INSERT INTO chat_timers (name, messages) VALUES ('anuncio', '[\"hola\"]')")
        conn.execute("INSERT INTO chat_commands (trigger, response) VALUES ('!hola', 'Hola!')")
        conn.execute("""CREATE TABLE timer_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timer_id INTEGER NOT NULL, message_sent TEXT NOT NULL,
            platform TEXT DEFAULT 'all', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("CREATE INDEX idx_timer_logs_timer ON timer_execution_logs(timer_id)")
        conn.execute("""CREATE TRIGGER prune_timer_logs AFTER INSERT ON timer_execution_logs
            BEGIN DELETE FROM timer_execution_logs WHERE id <= (NEW.id - 1000); END""")
        conn.execute("INSERT INTO timer_execution_logs (timer_id, message_sent) VALUES (1, 'hola')")
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
    db.cleanup()

    upgraded = DatabaseManager("legacy.db")

    names = {name for _kind, name in _objects(upgraded)}
    assert not {"timer_execution_logs", "prune_timer_logs", "idx_timer_logs_timer"} & names
    assert _version(upgraded) == CURRENT_SCHEMA_VERSION
    with upgraded.get_connection() as conn:
        assert conn.execute("SELECT name FROM chat_timers").fetchall() == [("anuncio",)]
        assert conn.execute("SELECT trigger FROM chat_commands").fetchall() == [("!hola",)]


def test_reopening_an_upgraded_database_is_a_no_op(home):
    db = DatabaseManager("again.db")
    before = _objects(db)
    db.cleanup()

    assert _objects(DatabaseManager("again.db")) == before
