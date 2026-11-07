# resources\tests\test_log_flush_throttle.py

import logging
from unittest.mock import patch
from backend.core.app_logger_core import AutoFlushTimedRotatingFileHandler


def _record(level, msg="x"):
    return logging.LogRecord("t", level, __file__, 1, msg, None, None)


def test_info_records_do_not_flush_every_time_but_warnings_do(tmp_path):
    handler = AutoFlushTimedRotatingFileHandler(str(tmp_path / "app.log"), when="midnight", encoding="utf-8")
    try:
        with patch.object(logging.FileHandler, "flush") as base_flush:
            for _ in range(50):
                handler.emit(_record(logging.INFO))
            assert base_flush.call_count <= 1
            handler.emit(_record(logging.WARNING))
            assert base_flush.call_count >= 1
            before = base_flush.call_count
            handler.emit(_record(logging.ERROR))
            assert base_flush.call_count == before + 1
    finally:
        handler.close()


def test_explicit_flush_is_always_honoured_and_data_reaches_disk(tmp_path):
    path = tmp_path / "app.log"
    handler = AutoFlushTimedRotatingFileHandler(str(path), when="midnight", encoding="utf-8")
    try:
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.emit(_record(logging.INFO, "first"))
        handler.emit(_record(logging.INFO, "second"))
        handler.flush()
        assert path.read_text(encoding="utf-8").splitlines() == ["first", "second"]
    finally:
        handler.close()
