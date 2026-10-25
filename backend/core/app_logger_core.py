# backend\core\app_logger_core.py

import faulthandler
import logging
import os
import sys
import threading
import traceback
from logging.handlers import TimedRotatingFileHandler
from PySide6.QtCore import qInstallMessageHandler, QtMsgType
from backend.handlers import QLogHandler, StreamToLogger, StructuredLogFormatter

_fault_file_handle = None
_q_log_handler_instance = None

_DEFAULT_LOG_LEVEL = logging.INFO

def _resolve_log_level() -> int:
    raw_level = os.environ.get("MINIKICK_LOG_LEVEL", "").strip().upper()
    if not raw_level:
        return _DEFAULT_LOG_LEVEL
    resolved = logging.getLevelName(raw_level)
    return resolved if isinstance(resolved, int) else _DEFAULT_LOG_LEVEL

class AutoFlushTimedRotatingFileHandler(TimedRotatingFileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        if record.levelno >= logging.INFO:
            self.flush()

logger = logging.getLogger("minikick.core.app_logger")


def write_fault_log_record(level: int, logger_name: str, message: str, thread_name: str | None = None) -> None:
    if _fault_file_handle is None:
        return

    record = logging.LogRecord(
        name=logger_name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    if thread_name is not None:
        record.threadName = thread_name

    try:
        _fault_file_handle.write(StructuredLogFormatter().format(record) + "\n")
        _fault_file_handle.flush()
    except (OSError, ValueError):
        logger.exception("[CrashLog] Could not write a structured fault record.")


def _qt_message_handler(mode: QtMsgType, _context, message: str):
    if not message or not message.strip():
        return

    lvl = logging.DEBUG
    if mode == QtMsgType.QtWarningMsg:
        lvl = logging.WARNING
    elif mode == QtMsgType.QtCriticalMsg:
        lvl = logging.ERROR
    elif mode == QtMsgType.QtFatalMsg:
        lvl = logging.CRITICAL
    elif mode == QtMsgType.QtInfoMsg:
        lvl = logging.INFO

    logging.getLogger("minikick.qt").log(lvl, "[Qt] %s", message)

def _threading_excepthook(args):
    tb_text = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    thread_name = getattr(args.thread, 'name', 'UnknownThread')
    logger.critical("Unhandled exception in thread '%s':\n%s", thread_name, tb_text)
    write_fault_log_record(
        logging.CRITICAL,
        "minikick.threading",
        f"Unhandled exception in thread '{thread_name}':\n{tb_text}",
        thread_name=thread_name,
    )
    flush_all_logs()

def flush_all_logs():
    for handler in logging.getLogger().handlers:
        try:
            handler.flush()
        except Exception:
            pass
    if _fault_file_handle:
        try:
            _fault_file_handle.flush()
        except Exception:
            pass

def get_log_dir() -> str:
    app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    log_dir = os.path.join(app_data_dir, '.Minikick', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def _silence_ffmpeg_native_logging():
    try:
        import ctypes
        import PySide6
        pyside_dir = os.path.dirname(PySide6.__file__)
        candidate_dirs = [
            pyside_dir,
            os.path.join(pyside_dir, "plugins", "multimedia"),
            os.path.join(pyside_dir, "bin"),
        ]
        for cdir in candidate_dirs:
            if not os.path.isdir(cdir):
                continue
            for f in os.listdir(cdir):
                if 'avutil' in f and (f.endswith('.dll') or f.endswith('.so') or '.so.' in f or f.endswith('.dylib')):
                    dll_path = os.path.join(cdir, f)
                    avutil = ctypes.CDLL(dll_path)
                    avutil.av_log_set_level(8)
                    return
    except Exception:
        pass

def setup_application_logging():
    global _fault_file_handle, _q_log_handler_instance
    
    if _q_log_handler_instance is not None:
        return logging.getLogger(), _q_log_handler_instance

    log_level = _resolve_log_level()
    logger.setLevel(log_level)
    
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        
    _q_log_handler_instance = QLogHandler()
    logger.addHandler(_q_log_handler_instance)
    
    log_dir = get_log_dir()
    log_file = os.path.join(log_dir, 'minikick.log')
    
    file_handler = AutoFlushTimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=7, 
        encoding='utf-8'
    )
    
    file_formatter = StructuredLogFormatter()
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)
    
    logger.info("[Bootstrap] Application logging initialized at level %s", logging.getLevelName(log_level))
    
    for lib_name in (
        "urllib3", "cloudscraper", "comtypes", "piper", "onnxruntime",
        "websocket", "httpx", "httpcore", "h2", "hpack", "pytchat", "asyncio",
        "tiktoklive", "yt_dlp", "PIL"
    ):
        logging.getLogger(lib_name).setLevel(logging.WARNING)

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    _silence_ffmpeg_native_logging()

    try:
        crash_log_path = os.path.join(log_dir, 'minikick_crash.log')
        _fault_file_handle = open(crash_log_path, 'a', encoding='utf-8', buffering=1)
        write_fault_log_record(
            logging.INFO,
            "minikick.bootstrap",
            "Session started (faulthandler active)",
        )
        faulthandler.enable(file=_fault_file_handle, all_threads=True)
    except Exception as fh_err:
        logger.warning("[Bootstrap] Failed to enable faulthandler: %s", fh_err)

    threading.excepthook = _threading_excepthook

    try:
        qInstallMessageHandler(_qt_message_handler)
    except Exception as q_err:
        logger.warning("[Bootstrap] Failed to install Qt MessageHandler: %s", q_err)
    
    return logger, _q_log_handler_instance
