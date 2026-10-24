# resources\tests\test_db_migrations.py

import sqlite3
import pytest
from backend.database.database_manager import DatabaseManager, CURRENT_SCHEMA_VERSION
from backend.database.migrations import MIGRATIONS, _migration_001_add_missing_columns_and_constraints


@pytest.fixture
def isolated_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    DatabaseManager._initialized_dbs.clear()
    yield tmp_path
    DatabaseManager._initialized_dbs.clear()

def test_migrations_are_ordered_and_versioned():
    versions = [version for version, _ in MIGRATIONS]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))
    assert MIGRATIONS and MIGRATIONS[0][0] == 1
    assert CURRENT_SCHEMA_VERSION == max(versions)

def test_fresh_database_reaches_current_schema_version(isolated_localappdata):
    db = DatabaseManager(db_name="test_migrate.db")
    with db.get_connection() as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == CURRENT_SCHEMA_VERSION

def test_migration_001_is_idempotent(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "mig.db"))
    try:
        conn.execute("CREATE TABLE chat_commands (id INTEGER PRIMARY KEY)")
        _migration_001_add_missing_columns_and_constraints(conn)
        _migration_001_add_missing_columns_and_constraints(conn)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(chat_commands)")}
        assert "cooldown" in columns
        assert "apply_tiktok" in columns
    finally:
        conn.close()
