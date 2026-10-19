# resources\tests\test_db_corruption_recovery.py

import os
import pytest
from backend.database.database_manager import DatabaseManager


@pytest.fixture
def isolated_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    DatabaseManager._initialized_dbs.clear()
    yield tmp_path
    DatabaseManager._initialized_dbs.clear()

def _backup_files(db_path: str) -> list[str]:
    parent = os.path.dirname(db_path)
    return [name for name in os.listdir(parent) if ".corrupt-" in name]

def test_corrupt_database_is_backed_up_not_deleted(isolated_localappdata):
    db = DatabaseManager(db_name="test_corrupt.db")
    db_path = db.db_name
    DatabaseManager._initialized_dbs.clear()

    with open(db_path, "wb") as handle:
        handle.write(b"this is not a sqlite database at all " * 32)

    recovered = DatabaseManager(db_name="test_corrupt.db")

    with recovered.get_connection() as conn:
        assert conn.execute("SELECT 1").fetchone()[0] == 1

    backups = _backup_files(db_path)
    assert backups, "corrupt database must be preserved as a .corrupt-* backup"

def test_healthy_database_creates_no_backup(isolated_localappdata):
    db = DatabaseManager(db_name="test_healthy.db")
    with db.get_connection() as conn:
        assert conn.execute("SELECT 1").fetchone()[0] == 1
    assert _backup_files(db.db_name) == []
