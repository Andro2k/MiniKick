# backend\handlers\log_handler.py

import logging
import sys
from PySide6.QtCore import QObject, Signal

class LogEmitter(QObject):
    log_received = Signal(str, str)

class QLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            if hasattr(self, "emitter") and self.emitter is not None:
                self.emitter.log_received.emit(record.levelname, msg)
        except Exception:
            pass

class StreamToLogger:
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self._in_write = False

    def write(self, buf):
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
                if line.strip():
                    self.logger.log(self.log_level, line.rstrip())
        finally:
            self._in_write = False

    def flush(self):
        pass
