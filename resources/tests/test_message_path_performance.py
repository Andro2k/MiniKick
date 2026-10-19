# resources\tests\test_message_path_performance.py

import logging
import pytest
from unittest.mock import MagicMock
from backend.core.app_logger_core import _resolve_log_level, _DEFAULT_LOG_LEVEL
from backend.services.schedule.schedule_service import ScheduleService
from backend.services.chat.spam_service import SpamService
from backend.database.database_manager import DatabaseManager
from backend.database.widgets_storage import SQLiteWidgetsStorage
from backend.services.system.widgets_service import WidgetService
from backend.controllers.widgets_controller import WidgetsController


def test_log_level_defaults_to_info(monkeypatch):
    monkeypatch.delenv("MINIKICK_LOG_LEVEL", raising=False)
    assert _resolve_log_level() == logging.INFO
    assert _DEFAULT_LOG_LEVEL == logging.INFO

def test_log_level_env_override_and_fallback(monkeypatch):
    monkeypatch.setenv("MINIKICK_LOG_LEVEL", "debug")
    assert _resolve_log_level() == logging.DEBUG
    monkeypatch.setenv("MINIKICK_LOG_LEVEL", "GARBAGE")
    assert _resolve_log_level() == logging.INFO

class _FakeScheduleStorage:
    def __init__(self, schedules):
        self._schedules = list(schedules)
        self.load_calls = 0

    def load_all(self, force_reload: bool = False):
        self.load_calls += 1
        return [dict(s) for s in self._schedules]

def test_next_schedule_text_is_memoized_but_self_expires():
    storage = _FakeScheduleStorage([{"name": "Stream", "time_str": "20:00", "is_active": True}])
    service = ScheduleService(schedule_storage=storage, i18n=None)

    assert service.get_next_schedule_text() == "Stream (20:00)"
    loads_after_first = storage.load_calls

    assert service.get_next_schedule_text() == "Stream (20:00)"
    assert storage.load_calls == loads_after_first

    service._cached_next_schedule_text_time = 0.0
    service._schedules_cache = [{"name": "Later", "time_str": "22:30", "is_active": True}]
    assert service.get_next_schedule_text() == "Later (22:30)"

def test_next_schedule_text_invalidation_clears_memo():
    storage = _FakeScheduleStorage([{"name": "A", "time_str": "10:00", "is_active": True}])
    service = ScheduleService(schedule_storage=storage, i18n=None)

    assert service.get_next_schedule_text() == "A (10:00)"
    service.invalidate_schedules_cache()
    assert service._cached_next_schedule_text is None
    assert service._cached_next_schedule_text_time == 0.0

class _FakeSpamStorage:
    def load_all(self):
        return {}

def test_spam_service_memoizes_clean_text_per_message(monkeypatch):
    service = SpamService(storage=_FakeSpamStorage(), i18n=None)
    service.filters = {
        "caps_protection": {"is_active": True, "apply_kick": True, "max_amount": 3, "exclude_group": "none", "penalty": "none"},
        "symbol_protection": {"is_active": True, "apply_kick": True, "max_amount": 99, "exclude_group": "none", "penalty": "none"},
        "paragraph_protection": {"is_active": True, "apply_kick": True, "max_amount": 300, "exclude_group": "none", "penalty": "none"},
        "repetition_protection": {"is_active": True, "apply_kick": True, "max_amount": 3, "exclude_group": "none", "penalty": "none"},
    }

    clean_calls: list[bool] = []
    original = service._get_clean_text

    def spy(message, emotes_tag="", strip_urls=False):
        clean_calls.append(strip_urls)
        return original(message, emotes_tag=emotes_tag, strip_urls=strip_urls)

    monkeypatch.setattr(service, "_get_clean_text", spy)

    is_repeated = service.is_spam("viewer", "hola hola hola hola", ["x"], "m1", 1, platform="kick")
    assert is_repeated is True
    assert len(clean_calls) <= 2

def test_spam_service_still_flags_caps(monkeypatch):
    service = SpamService(storage=_FakeSpamStorage(), i18n=None)
    service.filters = {
        "caps_protection": {"is_active": True, "apply_kick": True, "max_amount": 3, "exclude_group": "none", "penalty": "none"},
    }
    assert service.is_spam("viewer", "ESTO ES SPAM", ["x"], "m1", 1, platform="kick") is True
    assert service.is_spam("viewer", "mensaje normal", ["x"], "m2", 1, platform="kick") is False

@pytest.fixture
def temp_db():
    import os
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_name=path)
    yield db
    try:
        db.close_all_connections()
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def test_widgets_controller_caches_ignored_bots(temp_db, qapp):
    storage = SQLiteWidgetsStorage(temp_db)
    service = WidgetService(storage)
    cmd_service = MagicMock()
    cmd_service.get_all_commands.return_value = []

    load_calls = {"n": 0}

    class _FakeSettingsStorage:
        def load_string(self, key, default=""):
            load_calls["n"] += 1
            return "Nightbot,@StreamElements"

    class _FakeSpamService:
        def __init__(self):
            self.storage = _FakeSettingsStorage()

    controller = WidgetsController(
        view=None,
        widget_service=service,
        command_service=cmd_service,
        overlay_server=MagicMock(),
        spam_service=_FakeSpamService()
    )

    first = controller._get_ignored_bots()
    assert first == {"nightbot", "streamelements"}

    second = controller._get_ignored_bots()
    assert second == first
    assert load_calls["n"] == 1

    controller.invalidate_ignored_bots_cache()
    controller._get_ignored_bots()
    assert load_calls["n"] == 2
