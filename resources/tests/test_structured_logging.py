# resources\tests\test_structured_logging.py

import os
import re
import tempfile
import logging
import pytest
from backend.handlers.logs_handler import StructuredLogFormatter
from backend.services.system.logs_service import _LOG_FILE_LINE_RE
from backend.controllers.logs_controller import _LOG_LINE_RE
from backend.database.database_manager import DatabaseManager
from backend.database.logs_storage import SQLiteSystemLogStorage


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

def test_structured_log_formatter_format():
    formatter = StructuredLogFormatter()
    logger = logging.getLogger("MiniKick.Workers.KickChat")
    
    record_info = logger.makeRecord(
        name="MiniKick.Workers.KickChat",
        level=logging.INFO,
        fn="kick_chat_worker.py",
        lno=42,
        msg="Connected to WebSocket channel %s",
        args=("streamer_123",),
        exc_info=None
    )
    formatted_info = formatter.format(record_info)
    
    pattern = r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} [+-]\d{2}:\d{2}\] \[INF\] \[[^\]]+\] MiniKick\.Workers\.KickChat: Connected to WebSocket channel streamer_123$"
    assert re.match(pattern, formatted_info) is not None, f"Mismatch: {formatted_info}"

def test_structured_log_formatter_levels():
    formatter = StructuredLogFormatter()
    logger = logging.getLogger("MiniKick.Test")
    
    level_mappings = [
        (logging.DEBUG, "DBG"),
        (logging.INFO, "INF"),
        (logging.WARNING, "WRN"),
        (logging.ERROR, "ERR"),
        (logging.CRITICAL, "CRI"),
    ]
    
    for py_level, tag in level_mappings:
        rec = logger.makeRecord(
            name="MiniKick.Test",
            level=py_level,
            fn="test.py",
            lno=10,
            msg=f"Message for {tag}",
            args=(),
            exc_info=None
        )
        output = formatter.format(rec)
        assert f"[{tag}]" in output, f"Expected [{tag}] in '{output}'"

def test_structured_log_formatter_exception():
    formatter = StructuredLogFormatter()
    logger = logging.getLogger("MiniKick.Test")
    
    try:
        raise ValueError("Simulated network exception")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
    
    rec = logger.makeRecord(
        name="MiniKick.Test",
        level=logging.ERROR,
        fn="test.py",
        lno=99,
        msg="Operation failed",
        args=(),
        exc_info=exc_info
    )
    output = formatter.format(rec)
    assert "[ERR]" in output
    assert "Operation failed" in output
    assert "ValueError: Simulated network exception" in output

def test_log_file_line_re_retrocompatibility():
    new_log = "[2026-09-25 17:36:03.942 -05:00] [INF] [MainThread] MiniKick.Workers.KickChat: Connection established"
    match_new = _LOG_FILE_LINE_RE.match(new_log)
    assert match_new is not None
    assert match_new.group("time") == "2026-09-25 17:36:03.942 -05:00"
    assert match_new.group("level") == "INF"
    assert match_new.group("msg") == "[MainThread] MiniKick.Workers.KickChat: Connection established"

    legacy_log = "[2026-09-25 15:30:00] [INFO] Connected to channel"
    match_legacy = _LOG_FILE_LINE_RE.match(legacy_log)
    assert match_legacy is not None
    assert match_legacy.group("time") == "2026-09-25 15:30:00"
    assert match_legacy.group("level") == "INFO"
    assert match_legacy.group("msg") == "Connected to channel"

    crash_log = "[2026-09-25 15:30:00] [CRASH] Fatal exception in worker thread"
    match_crash = _LOG_FILE_LINE_RE.match(crash_log)
    assert match_crash is not None
    assert match_crash.group("time") == "2026-09-25 15:30:00"
    assert match_crash.group("level") == "CRASH"
    assert match_crash.group("msg") == "Fatal exception in worker thread"

def test_log_line_re_controller():
    new_log = "[2026-09-25 17:36:03.942 -05:00] [DBG] [Worker-1] MiniKick.Services.Audio: Playing sound"
    match_new = _LOG_LINE_RE.match(new_log)
    assert match_new is not None
    assert match_new.group("time") == "2026-09-25 17:36:03.942 -05:00"
    assert match_new.group("level") == "DBG"
    assert match_new.group("msg") == "[Worker-1] MiniKick.Services.Audio: Playing sound"

    legacy_log = "[2026-09-25 15:30:00] [WARNING] Low memory condition"
    match_legacy = _LOG_LINE_RE.match(legacy_log)
    assert match_legacy is not None
    assert match_legacy.group("time") == "2026-09-25 15:30:00"
    assert match_legacy.group("level") == "WARNING"
    assert match_legacy.group("msg") == "Low memory condition"

def test_sqlite_logs_storage_level_aliases(temp_db):
    storage = SQLiteSystemLogStorage(temp_db)
    
    storage.append_log("INF", "2026-09-25 10:00:00.123 -05:00", "Info log via 3-letter")
    storage.append_log("INFO", "2026-09-25 10:01:00", "Info log via full name")
    storage.append_log("WRN", "2026-09-25 10:02:00.456 -05:00", "Warning log via 3-letter")
    storage.append_log("WARNING", "2026-09-25 10:03:00", "Warning log via full name")
    storage.append_log("ERR", "2026-09-25 10:04:00.789 -05:00", "Error log via 3-letter")
    
    info_logs = storage.get_filtered_logs("INFO", "ALL", "")
    assert len(info_logs) == 2
    
    inf_logs = storage.get_filtered_logs("INF", "ALL", "")
    assert len(inf_logs) == 2
    
    warn_logs = storage.get_filtered_logs("WARNING", "ALL", "")
    assert len(warn_logs) == 2
    
    err_logs = storage.get_filtered_logs("ERR", "ALL", "")
    assert len(err_logs) == 1
    
    all_logs = storage.get_filtered_logs("ALL", "ALL", "")
    assert len(all_logs) == 5

def test_overlay_server_logging_and_broadcast():
    from backend.services.overlay.overlay_manager import OverlayServerManager
    from unittest.mock import MagicMock
    import json

    manager = OverlayServerManager(port=8099)
    assert manager.get_ws_clients_count("chat") == 0

    mock_client = MagicMock()
    mock_client.topic = "chat"
    manager.register_ws_client(mock_client)

    assert manager.get_ws_clients_count("chat") == 1

    payload = {"event": "chat_message", "user": "TestUser", "message": "Hello OBS"}
    manager._broadcast("chat_clients", "chat", payload)

    mock_client.send_text.assert_called_once()
    sent_arg = mock_client.send_text.call_args[0][0]
    parsed = json.loads(sent_arg)
    assert parsed["user"] == "TestUser"
    assert parsed["message"] == "Hello OBS"

    manager.unregister_ws_client(mock_client)
    assert manager.get_ws_clients_count("chat") == 0
