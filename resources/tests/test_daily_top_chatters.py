# resources\tests\test_daily_top_chatters.py

import datetime
import os
import tempfile
import pytest
from unittest.mock import MagicMock
from backend.database.database_manager import DatabaseManager
from backend.database.widgets_storage import SQLiteWidgetsStorage
from backend.services.system.widgets_service import WidgetService
from backend.controllers.widgets_controller import WidgetsController


@pytest.fixture
def temp_db():
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

def test_sqlite_widgets_storage_daily_chatters(temp_db):
    storage = SQLiteWidgetsStorage(temp_db)
    date_str = "2026-09-25"

    initial = storage.load_daily_chatters(date_str)
    assert initial == {}

    chatters_data = {
        "user1": {
            "user": "User1",
            "count": 15,
            "color": "#FF0000",
            "badges": ["moderator"],
            "platform": "kick"
        },
        "user2": {
            "user": "User2",
            "count": 30,
            "color": "#00FF00",
            "badges": ["vip"],
            "platform": "kick"
        }
    }
    storage.save_daily_chatters_batch(date_str, chatters_data)

    loaded = storage.load_daily_chatters(date_str)
    assert len(loaded) == 2
    assert loaded["user2"]["count"] == 30
    assert loaded["user1"]["count"] == 15
    assert loaded["user2"]["user"] == "User2"
    assert loaded["user1"]["badges"] == ["moderator"]

    chatters_data["user1"]["count"] = 50
    storage.save_daily_chatters_batch(date_str, chatters_data)
    reloaded = storage.load_daily_chatters(date_str)
    assert reloaded["user1"]["count"] == 50

    storage.clear_daily_chatters(date_str)
    cleared = storage.load_daily_chatters(date_str)
    assert cleared == {}

def test_sqlite_widgets_storage_pruning(temp_db):
    storage = SQLiteWidgetsStorage(temp_db)
    today = datetime.date.today()
    old_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    recent_date = today.strftime("%Y-%m-%d")

    storage.save_daily_chatters_batch(old_date, {
        "olduser": {"user": "OldUser", "count": 5, "color": "", "badges": [], "platform": "kick"}
    })
    storage.save_daily_chatters_batch(recent_date, {
        "newuser": {"user": "NewUser", "count": 10, "color": "", "badges": [], "platform": "kick"}
    })

    storage.prune_old_chatters(keep_days=7)

    assert storage.load_daily_chatters(old_date) == {}
    assert len(storage.load_daily_chatters(recent_date)) == 1

def test_widgets_controller_restores_daily_chatters_on_startup(temp_db):
    storage = SQLiteWidgetsStorage(temp_db)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    storage.save_daily_chatters_batch(today, {
        "streamerfan": {"user": "StreamerFan", "count": 42, "color": "#2ECD70", "badges": [], "platform": "kick"},
        "viewer99": {"user": "Viewer99", "count": 10, "color": "#123456", "badges": ["vip"], "platform": "twitch"}
    })

    service = WidgetService(storage)
    cmd_service = MagicMock()
    cmd_service.get_all_commands.return_value = []
    overlay_server = MagicMock()

    controller = WidgetsController(
        view=None,
        widget_service=service,
        command_service=cmd_service,
        overlay_server=overlay_server
    )
    controller.load_initial_data()

    assert "streamerfan" in controller._chatters_counts
    assert controller._chatters_counts["streamerfan"]["count"] == 42
    assert len(controller._last_emitted_top_chatters) == 2
    assert controller._last_emitted_top_chatters[0]["user"] == "StreamerFan"
    assert controller._last_emitted_top_chatters[0]["count"] == 42

    overlay_server.trigger_widget_event.assert_any_call("top_chatters_update", {
        "top": controller._last_emitted_top_chatters,
        "total_messages": 52,
        "is_active": True
    })

def test_widgets_controller_chat_recording_and_flushing(temp_db):
    storage = SQLiteWidgetsStorage(temp_db)
    service = WidgetService(storage)
    cmd_service = MagicMock()
    cmd_service.get_all_commands.return_value = []
    overlay_server = MagicMock()

    controller = WidgetsController(
        view=None,
        widget_service=service,
        command_service=cmd_service,
        overlay_server=overlay_server
    )
    controller.load_initial_data()

    controller.handle_chat_message(
        user="AwesomeChatter",
        content="Hello world!",
        color="#336699",
        badges=["vip"],
        platform="kick"
    )

    assert "awesomechatter" in controller._chatters_counts
    assert controller._chatters_counts["awesomechatter"]["count"] == 1
    assert controller._chatters_dirty is True

    controller._flush_top_chatters_update(force=True)
    assert controller._chatters_dirty is False

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    persisted = storage.load_daily_chatters(today)
    assert "awesomechatter" in persisted
    assert persisted["awesomechatter"]["count"] == 1
    assert persisted["awesomechatter"]["user"] == "AwesomeChatter"

    controller.reset_chatters_counts()
    assert controller._chatters_counts == {}
    cleared = storage.load_daily_chatters(today)
    assert cleared == {}

def test_widgets_controller_include_commands_toggle(temp_db):
    storage = SQLiteWidgetsStorage(temp_db)
    service = WidgetService(storage)
    cmd_service = MagicMock()
    cmd_service.get_all_commands.return_value = []
    overlay_server = MagicMock()

    controller = WidgetsController(
        view=None,
        widget_service=service,
        command_service=cmd_service,
        overlay_server=overlay_server
    )
    controller.load_initial_data()

    controller.handle_chat_message(
        user="CommandSpammer",
        content="!points 100",
        platform="kick"
    )
    assert "commandspammer" not in controller._chatters_counts

    service.save_widget("chatters", True, "!topchatters", 3, "everyone", {"include_commands": True})

    controller.handle_chat_message(
        user="CommandSpammer",
        content="!points 100",
        platform="kick"
    )
    assert "commandspammer" in controller._chatters_counts
    assert controller._chatters_counts["commandspammer"]["count"] == 1


def test_handle_chat_message_skips_emote_parsing_when_widgets_inactive(monkeypatch):
    from unittest.mock import MagicMock
    from backend.controllers import widgets_controller as wc

    parse = MagicMock(side_effect=AssertionError("emote parsing should be skipped"))
    monkeypatch.setattr(wc, "extract_emotes", parse)

    widget_svc = MagicMock()
    widget_svc.get_widget.return_value = {"is_active": False, "config": {}}
    overlay = MagicMock()
    controller = wc.WidgetsController(
        view=None, widget_service=widget_svc, command_service=MagicMock(), overlay_server=overlay
    )
    monkeypatch.setattr(controller, "_record_chatter_message", MagicMock())

    controller.handle_chat_message("viewer", "[emote:1:KEKW] 🔥", platform="kick")

    parse.assert_not_called()
    overlay.trigger_widget_event.assert_not_called()
