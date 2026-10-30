# resources\tests\test_log_service_async.py

import time

import pytest

from backend.database.database_manager import DatabaseManager
from backend.database.logs_storage import SQLiteSystemLogStorage
from backend.services.system.logs_service import LogService


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return SQLiteSystemLogStorage(DatabaseManager("log_service_async.db"))


def test_append_record_returns_immediately_and_persists_after_flush(storage):
    service = LogService(log_storage=storage)
    started = time.perf_counter()
    for n in range(100):
        assert service.append_record("12:00:00", "INF", f"evento {n}") is False
    assert time.perf_counter() - started < 0.2

    service.flush_pending()
    stored = storage.get_all_logs()
    assert [row[2] for row in stored] == [f"evento {n}" for n in range(100)]
    service.close()


def test_history_reads_include_records_not_yet_flushed(storage):
    service = LogService(log_storage=storage)
    service.append_record("12:00:00", "INF", "reciente")

    assert [row[2] for row in service.get_history()] == ["reciente"]
    assert [row[2] for row in service.get_filtered_history("ALL", "ALL", "recien")] == ["reciente"]
    service.close()


def test_clear_history_removes_pending_and_stored_records(storage):
    service = LogService(log_storage=storage)
    service.append_record("12:00:00", "INF", "viejo")
    service.clear_history()
    service.flush_pending()

    assert storage.get_all_logs() == []
    service.close()


def test_close_persists_what_is_pending(storage):
    service = LogService(log_storage=storage)
    service.append_record("12:00:00", "INF", "ultimo")
    service.close()

    assert [row[2] for row in storage.get_all_logs()] == ["ultimo"]


def test_service_without_storage_keeps_working_in_memory():
    service = LogService()
    assert service.append_record("12:00:00", "INF", "memoria") is False
    service.flush_pending()
    service.close()
    assert [row[2] for row in service.get_history()] == ["memoria"]
