# tests\conftest.py

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import pytest
from backend.database.manager import DatabaseManager
from backend.database.settings_storage import SQLiteSettingsStorage
from backend.database.spam_storage import SQLiteSpamStorage

class DummyI18n:
    def get(self, key: str, default: str = "") -> str:
        return default or key

@pytest.fixture
def temp_db():
    db = DatabaseManager(db_name="test_temp_minikick.db")
    yield db
    if hasattr(db, "close"):
        try:
            db.close()
        except Exception:
            pass
    if os.path.exists(db.db_name):
        try:
            os.remove(db.db_name)
        except Exception:
            pass

@pytest.fixture
def storage(temp_db):
    return SQLiteSettingsStorage(db_manager=temp_db)

@pytest.fixture
def spam_storage(temp_db):
    return SQLiteSpamStorage(db_manager=temp_db)

@pytest.fixture
def i18n():
    return DummyI18n()
