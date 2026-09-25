# backend\handlers\logs_handler.py

import logging
import sys
import threading
from datetime import datetime
from PySide6.QtCore import QObject, Signal

_SHORT_LEVELS: dict[str, str] = {
    "DEBUG": "DBG",
    "INFO": "INF",
    "WARNING": "WRN",
    "ERROR": "ERR",
    "CRITICAL": "CRI",
}

_LOGGER_NAME_CACHE: dict[str, str] = {}

def format_logger_name(raw_name: str) -> str:
    cached = _LOGGER_NAME_CACHE.get(raw_name)
    if cached is not None:
        return cached

    if not raw_name or raw_name == "root":
        formatted = "MiniKick.Main"
    else:
        parts = raw_name.split(".")
        clean_parts = []
        for p in parts:
            if p.lower() == "minikick":
                clean_parts.append("MiniKick")
            elif p.lower() == "qt":
                clean_parts.append("Qt")
            else:
                words = p.split("_")
                clean_parts.append("".join(w[0].upper() + w[1:] if w else "" for w in words))
        formatted = ".".join(clean_parts)

    _LOGGER_NAME_CACHE[raw_name] = formatted
    return formatted

class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record_dt = datetime.fromtimestamp(record.created).astimezone()
        base_time = record_dt.strftime("%Y-%m-%d %H:%M:%S")
        msec = f"{record_dt.microsecond // 1000:03d}"
        tz_offset = record_dt.strftime("%z")
        formatted_tz = f"{tz_offset[:3]}:{tz_offset[3:]}" if len(tz_offset) >= 5 else "+00:00"
        timestamp_str = f"{base_time}.{msec} {formatted_tz}"

        short_lvl = _SHORT_LEVELS.get(record.levelname, record.levelname[:3].upper())
        thread_name = record.threadName or getattr(threading.current_thread(), "name", "Thread")
        logger_name = format_logger_name(record.name)

        msg = record.getMessage()
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if msg[-1:] != "\n":
                msg += "\n"
            msg += record.exc_text
        if record.stack_info:
            if msg[-1:] != "\n":
                msg += "\n"
            msg += self.formatStack(record.stack_info)

        return f"[{timestamp_str}] [{short_lvl}] [{thread_name}] {logger_name}: {msg}"

class LogEmitter(QObject):
    log_received = Signal(str, str)

class QLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()
        self.setFormatter(StructuredLogFormatter())

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            if hasattr(self, "emitter") and self.emitter is not None:
                self.emitter.log_received.emit(record.levelname, msg)
        except Exception:
            pass

class StreamToLogger:
    _DEBUG_PREFIXES = ("[download]", "[info]", "[youtube]", "[generic]")

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self._lock = threading.RLock()
        self._in_write = False

    def write(self, buf):
        if not buf:
            return
        with self._lock:
            if self._in_write:
                if sys.__stderr__ is not None:
                    try:
                        sys.__stderr__.write(buf)
                    except Exception:
                        pass
                return
            self._in_write = True
            try:
                for line in buf.rstrip().splitlines():
                    cleaned = line.strip()
                    if cleaned:
                        level = (
                            logging.DEBUG
                            if cleaned.startswith(self._DEBUG_PREFIXES)
                            else self.log_level
                        )
                        self.logger.log(level, line.rstrip())
            finally:
                self._in_write = False

    def flush(self):
        pass
