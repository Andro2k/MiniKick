# tests\conftest.py

import os
import sys
import tempfile
from datetime import datetime
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.database.manager import DatabaseManager
from backend.database.settings_storage import SQLiteSettingsStorage
from backend.database.spam_storage import SQLiteSpamStorage
from backend.services.system.translation_service import TranslationService

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "logs", "pytest_last_run.log")

@pytest.fixture
def storage():
    tmpdir_ctx = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    tmpdir = tmpdir_ctx.name
    db_mgr = DatabaseManager(db_name=os.path.join(tmpdir, "test.db"))
    yield SQLiteSettingsStorage(db_manager=db_mgr)
    db_mgr.cleanup()
    tmpdir_ctx.cleanup()

@pytest.fixture
def spam_storage():
    tmpdir_ctx = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    tmpdir = tmpdir_ctx.name
    db_mgr = DatabaseManager(db_name=os.path.join(tmpdir, "test_spam.db"))
    yield SQLiteSpamStorage(db_manager=db_mgr)
    db_mgr.cleanup()
    tmpdir_ctx.cleanup()

@pytest.fixture
def i18n():
    return TranslationService(default_lang="es")

_log_file_handle = None

def pytest_sessionstart(session):
    global _log_file_handle
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    _log_file_handle = open(LOG_FILE_PATH, "w", encoding="utf-8")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"=========================================================================\n" \
             f"  MINIKICK TEST SUITE LOG - {now_str}\n" \
             f"=========================================================================\n\n"
    _log_file_handle.write(header)
    _log_file_handle.flush()

def pytest_runtest_logreport(report):
    global _log_file_handle
    if _log_file_handle and not _log_file_handle.closed:
        if report.when == "call":
            now_str = datetime.now().strftime("%H:%M:%S")
            status = report.outcome.upper()
            duration = f"{report.duration:.3f}s"
            _log_file_handle.write(f"[{now_str}] {status:<6} {report.nodeid} ({duration})\n")
            if report.failed and report.longreprtext:
                _log_file_handle.write(f"  Detalles del error:\n{report.longreprtext}\n")
            _log_file_handle.flush()

def pytest_sessionfinish(session, exitstatus):
    global _log_file_handle
    if _log_file_handle and not _log_file_handle.closed:
        _log_file_handle.write(f"\n=========================================================================\n")
        _log_file_handle.write(f"  RESULTADO FINAL: EXIT CODE {exitstatus}\n")
        _log_file_handle.write(f"=========================================================================\n")
        _log_file_handle.close()
        _log_file_handle = None
