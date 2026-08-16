# tests\unit\test_schedule_service.py

import pytest
from unittest.mock import MagicMock
from backend.database.manager import DatabaseManager
from backend.database.schedule_storage import SQLiteScheduleStorage
from backend.services.schedule.schedule_service import ScheduleService
from backend.providers.chat.kick_client import KickAPIClient
from backend.providers.chat.twitch_client import TwitchAPIClient

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_minikick.db"
    db_manager = DatabaseManager(db_name=str(db_file))
    return db_manager

def test_schedule_storage_crud(temp_db):
    storage = SQLiteScheduleStorage(temp_db)
    
    sched_id = storage.save(
        name="Friday Gaming",
        date_str="2026-08-20",
        time_str="19:00",
        target_platform="all",
        title="Playing horror games!",
        kick_category_id=45,
        kick_category_name="Horror",
        twitch_category_id="12345",
        twitch_category_name="Horror Games",
        is_active=True
    )
    assert sched_id is not None and sched_id > 0

    item = storage.get_by_id(sched_id)
    assert item is not None
    assert item["name"] == "Friday Gaming"
    assert item["date_str"] == "2026-08-20"
    assert item["time_str"] == "19:00"
    assert item["target_platform"] == "all"
    assert item["title"] == "Playing horror games!"
    assert item["is_active"] is True

    all_items = storage.load_all()
    assert len(all_items) == 1
    assert all_items[0]["id"] == sched_id
    storage.toggle_active(sched_id, False)
    item_updated = storage.get_by_id(sched_id)
    assert item_updated["is_active"] is False

    storage.update_last_executed(sched_id, "2026-08-20")
    item_updated = storage.get_by_id(sched_id)
    assert item_updated["last_executed_date"] == "2026-08-20"
    deleted = storage.delete(sched_id)
    assert deleted is True
    assert storage.get_by_id(sched_id) is None
    assert len(storage.load_all()) == 0

def test_schedule_service_category_cache(temp_db):
    storage = SQLiteScheduleStorage(temp_db)
    mock_kick = MagicMock()
    mock_kick.search_categories.return_value = [{"id": 1, "name": "Just Chatting"}]
    mock_twitch = MagicMock()
    mock_twitch.search_categories.return_value = [{"id": "509658", "name": "Just Chatting"}]

    service = ScheduleService(
        schedule_storage=storage,
        kick_client=mock_kick,
        twitch_client=mock_twitch,
        twitch_broadcaster_id="123456"
    )

    res1 = service.search_categories("Just Chatting", platform="both")
    assert len(res1["kick"]) == 1
    assert len(res1["twitch"]) == 1
    assert mock_kick.search_categories.call_count == 1
    assert mock_twitch.search_categories.call_count == 1

    res2 = service.search_categories("Just Chatting", platform="both")
    assert res2 == res1
    assert mock_kick.search_categories.call_count == 1
    assert mock_twitch.search_categories.call_count == 1

def test_schedule_service_update_platforms(temp_db):
    storage = SQLiteScheduleStorage(temp_db)
    mock_kick = MagicMock()
    mock_kick.update_channel_metadata.return_value = True
    mock_twitch = MagicMock()
    mock_twitch.update_channel_metadata.return_value = True

    service = ScheduleService(
        schedule_storage=storage,
        kick_client=mock_kick,
        twitch_client=mock_twitch,
        twitch_broadcaster_id="999888"
    )

    outcome = service.update_stream_info("New Title", kick_category_id=10, twitch_category_id="20", platform="both")
    assert outcome["kick"]["success"] is True
    assert outcome["twitch"]["success"] is True
    mock_kick.update_channel_metadata.assert_called_once_with(category_id=10, stream_title="New Title")
    mock_twitch.update_channel_metadata.assert_called_once_with(broadcaster_id="999888", title="New Title", game_id="20")

def test_schedule_service_update_only_title_or_only_category(temp_db):
    storage = SQLiteScheduleStorage(temp_db)
    mock_kick = MagicMock()
    mock_kick.update_channel_metadata.return_value = True
    mock_twitch = MagicMock()
    mock_twitch.update_channel_metadata.return_value = True

    service = ScheduleService(
        schedule_storage=storage,
        kick_client=mock_kick,
        twitch_client=mock_twitch,
        twitch_broadcaster_id="999888"
    )

    out1 = service.update_stream_info("Only Title", kick_category_id=None, twitch_category_id=None, platform="both")
    assert out1["kick"]["success"] is True
    assert out1["twitch"]["success"] is True
    mock_kick.update_channel_metadata.assert_called_with(category_id=None, stream_title="Only Title")
    mock_twitch.update_channel_metadata.assert_called_with(broadcaster_id="999888", title="Only Title", game_id=None)

    out2 = service.update_stream_info("", kick_category_id=55, twitch_category_id="1122", platform="both")
    assert out2["kick"]["success"] is True
    assert out2["twitch"]["success"] is True
    mock_kick.update_channel_metadata.assert_called_with(category_id=55, stream_title=None)
    mock_twitch.update_channel_metadata.assert_called_with(broadcaster_id="999888", title=None, game_id="1122")

def test_schedule_service_auto_resolve_category(temp_db):
    storage = SQLiteScheduleStorage(temp_db)
    mock_kick = MagicMock()
    mock_kick.search_categories.return_value = [{"id": 99, "name": "Minecraft"}]
    mock_kick.update_channel_metadata.return_value = True

    mock_twitch = MagicMock()
    mock_twitch.search_categories.return_value = [{"id": "27471", "name": "Minecraft"}]
    mock_twitch.update_channel_metadata.return_value = True

    service = ScheduleService(
        schedule_storage=storage,
        kick_client=mock_kick,
        twitch_client=mock_twitch,
        twitch_broadcaster_id="999888"
    )

    outcome = service.update_stream_info(
        title="Playing Minecraft",
        kick_category_id=None,
        twitch_category_id=None,
        platform="both",
        category_query="Minecraft"
    )
    assert outcome["kick"]["success"] is True
    assert outcome["twitch"]["success"] is True
    mock_kick.search_categories.assert_called_once_with("Minecraft")
    mock_kick.update_channel_metadata.assert_called_once_with(category_id=99, stream_title="Playing Minecraft")
    mock_twitch.update_channel_metadata.assert_called_once_with(broadcaster_id="999888", title="Playing Minecraft", game_id="27471")

def test_schedule_worker_execution(temp_db):
    from datetime import datetime
    from backend.workers.schedule_worker import ScheduleWorker

    storage = SQLiteScheduleStorage(temp_db)
    mock_kick = MagicMock()
    mock_kick.update_channel_metadata.return_value = True

    service = ScheduleService(
        schedule_storage=storage,
        kick_client=mock_kick
    )

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M")

    sched_id = storage.save(
        name="Trigger Test",
        date_str=today_str,
        time_str=current_time_str,
        target_platform="kick",
        title="Triggered Title",
        kick_category_id=10,
        kick_category_name="Games",
        twitch_category_id=None,
        twitch_category_name="",
        is_active=True
    )

    worker = ScheduleWorker(service)
    triggered_records = []
    worker.schedule_triggered.connect(lambda s, r: triggered_records.append((s, r)))

    worker._check_and_execute_schedules()

    assert len(triggered_records) == 1
    sched_executed, res = triggered_records[0]
    assert sched_executed["name"] == "Trigger Test"
    mock_kick.update_channel_metadata.assert_called_once_with(category_id=10, stream_title="Triggered Title")

    saved_sched = storage.get_by_id(sched_id)
    assert saved_sched["is_active"] is False
    assert saved_sched["last_executed_date"] == today_str

