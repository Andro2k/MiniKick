# tests/test_timer_service.py

import os
import pytest
from backend.database.manager import DatabaseManager
from backend.database.timers_storage import SQLiteTimersStorage
from backend.services.chat.timer_service import TimerService

@pytest.fixture
def db_manager(tmp_path):
    db_file = os.path.join(tmp_path, "test_minikick.db")
    db = DatabaseManager(db_name=db_file)
    yield db

@pytest.fixture
def timer_service(db_manager):
    storage = SQLiteTimersStorage(db_manager)
    return TimerService(storage)

def test_save_and_load_timer_platforms(timer_service):
    timer_service.save_timer(
        name="Socials",
        messages=["Follow my twitter!"],
        is_active=True,
        interval_online=5,
        interval_offline=30,
        chat_lines=2,
        keywords=[],
        categories=[],
        apply_kick=True,
        apply_twitch=False
    )

    timers = timer_service.get_all_timers()
    assert len(timers) == 1
    t = timers[0]
    assert t["name"] == "Socials"
    assert t["apply_kick"] is True
    assert t["apply_twitch"] is False

def test_check_timers_returns_platform_tuple(timer_service):
    timer_service.save_timer(
        name="Discord",
        messages=["Join Discord!"],
        is_active=True,
        interval_online=1,
        interval_offline=1,
        chat_lines=0,
        keywords=[],
        categories=[],
        apply_kick=False,
        apply_twitch=True
    )

    timers = timer_service.get_all_timers()
    timer_id = timers[0]["id"]
    timer_service.tracking_state[timer_id] = {
        "last_posted_time": 0,
        "chat_lines": 0,
        "message_index": 0
    }

    res = timer_service.check_timers({"is_live": True, "title": "", "category": ""})
    assert len(res) == 1
    msg, apply_kick, apply_twitch = res[0]
    assert msg == "Join Discord!"
    assert apply_kick is False
    assert apply_twitch is True
