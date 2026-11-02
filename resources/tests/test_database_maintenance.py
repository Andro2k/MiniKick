# resources\tests\test_database_maintenance.py

import pytest

from backend.database.database_manager import DatabaseManager
from backend.services.system.db_maintenance_service import DatabaseMaintenance


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return DatabaseManager("maintenance.db")


def _fill_and_empty_avatar_cache(db, rows=120, size=20_000):
    with db.get_connection() as conn:
        conn.executemany(
            "INSERT INTO avatar_cache (url, image_bytes) VALUES (?, ?)",
            [(f"https://x/{n}.png", b"x" * size) for n in range(rows)],
        )
        conn.commit()
        conn.execute("DELETE FROM avatar_cache")
        conn.commit()


def test_collect_stats_reports_sizes_and_row_counts_without_shadow_tables(db):
    with db.get_connection() as conn:
        conn.execute("INSERT INTO chat_commands (trigger, response) VALUES ('!a', 'x'), ('!b', 'y')")
        conn.commit()

    stats = DatabaseMaintenance(db).collect_stats()

    assert stats.file_bytes > 0
    assert stats.table_rows["chat_commands"] == 2
    assert "settings" in stats.table_rows
    assert not any("_fts_" in name for name in stats.table_rows)


def test_run_reclaims_free_pages_when_thresholds_are_exceeded(db):
    _fill_and_empty_avatar_cache(db)
    maintenance = DatabaseMaintenance(db, vacuum_min_free_bytes=1, vacuum_min_free_ratio=0.0)
    assert maintenance.collect_stats().free_bytes > 0

    stats = maintenance.run()

    assert stats.free_bytes == 0
    assert stats.wal_bytes == 0 or stats.wal_bytes < 5_000_000


def test_run_leaves_the_file_alone_when_free_space_is_small(db):
    _fill_and_empty_avatar_cache(db, rows=5, size=2_000)
    before = DatabaseMaintenance(db).collect_stats().free_bytes

    stats = DatabaseMaintenance(db).run()

    assert before > 0
    assert stats.free_bytes == before


def test_fresh_database_has_no_obsolete_objects(db):
    assert DatabaseMaintenance(db).find_obsolete_objects() == []


def test_objects_not_declared_by_the_schema_are_reported(db):
    with db.get_connection() as conn:
        conn.execute("CREATE TABLE legacy_stats (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("CREATE INDEX idx_legacy_stats_value ON legacy_stats(value)")
        conn.commit()

    assert DatabaseMaintenance(db).find_obsolete_objects() == [
        "index:idx_legacy_stats_value",
        "table:legacy_stats",
    ]


def test_run_never_raises_even_if_the_database_is_unusable(db, monkeypatch):
    def broken():
        raise RuntimeError("base de datos bloqueada")

    monkeypatch.setattr(db, "get_connection", broken)
    assert DatabaseMaintenance(db).run() is None
