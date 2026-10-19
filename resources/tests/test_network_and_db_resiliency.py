# resources\tests\test_network_and_db_resiliency.py

from unittest.mock import MagicMock, patch
import requests
from backend.providers.chat.kick_provider import KickAPIClient, ScraperFactory
from backend.services.schedule.schedule_service import ScheduleService
from backend.database.database_manager import DatabaseManager


def test_kick_api_client_reconnects_on_connection_reset_10054():
    mock_auth = MagicMock()
    mock_auth.get_tokens.return_value = {"access_token": "valid_token"}

    client = KickAPIClient(mock_auth)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": {"id": "msg_123", "content": "Hola mundo"}}

    conn_error = requests.exceptions.ConnectionError(
        ConnectionResetError(10054, "Se ha forzado la interrupcion de una conexion existente por el host remoto")
    )

    client.scraper.request = MagicMock(side_effect=conn_error)

    mock_new_scraper = MagicMock()
    mock_new_scraper.request.return_value = mock_resp

    with patch.object(ScraperFactory, "create", return_value=mock_new_scraper) as mock_create:
        res = client.post_chat_message("Hola mundo")

        assert res == {"data": {"id": "msg_123", "content": "Hola mundo"}}
        mock_create.assert_called_once()
        mock_new_scraper.request.assert_called_once()

def test_kick_api_client_handles_persistent_network_error():
    mock_auth = MagicMock()
    mock_auth.get_tokens.return_value = {"access_token": "valid_token"}

    client = KickAPIClient(mock_auth)
    conn_error = requests.exceptions.ConnectionError(
        ConnectionResetError(10054, "Remote host closed connection")
    )

    client.scraper.request = MagicMock(side_effect=conn_error)

    with patch.object(ScraperFactory, "create", return_value=MagicMock(request=MagicMock(side_effect=conn_error))):
        res = client.post_chat_message("Hola mundo")
        assert res == {}

def test_schedule_service_in_memory_caching_and_invalidation():
    mock_storage = MagicMock()
    mock_storage.load_all.return_value = [
        {"id": 1, "name": "Morning Stream", "time_str": "09:00", "is_active": True}
    ]

    service = ScheduleService(schedule_storage=mock_storage)

    schedules1 = service.get_all_schedules()
    assert len(schedules1) == 1
    assert schedules1[0]["name"] == "Morning Stream"
    assert mock_storage.load_all.call_count == 1

    schedules2 = service.get_all_schedules()
    assert len(schedules2) == 1
    assert mock_storage.load_all.call_count == 1

    schedules2[0]["name"] = "Mutated"
    schedules3 = service.get_all_schedules()
    assert schedules3[0]["name"] == "Morning Stream"

    mock_storage.save.return_value = 2
    service.save_schedule(
        name="Night Stream", date_str="", time_str="21:00", target_platform="all",
        title="Gaming", kick_category_id=None, kick_category_name="",
        twitch_category_id=None, twitch_category_name="", is_active=True
    )
    assert service._schedules_cache is None

    service.get_all_schedules()
    assert mock_storage.load_all.call_count == 2

    service.delete_schedule(2)
    assert service._schedules_cache is None

    service.mark_schedule_executed(1, "2026-09-18")
    mock_storage.update_last_executed.assert_called_once_with(1, "2026-09-18")
    mock_storage.toggle_active.assert_called_once_with(1, False)
    assert service._schedules_cache is None

def test_database_manager_busy_timeout_setting(tmp_path):
    db_file = str(tmp_path / "test_busy.db")
    with patch.object(DatabaseManager, "__init__", lambda self: None):
        db_mgr = DatabaseManager()
        db_mgr.db_name = db_file

        conn = db_mgr.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA busy_timeout")
            timeout_val = cursor.fetchone()[0]
            assert timeout_val == 30000
        finally:
            conn.close()
