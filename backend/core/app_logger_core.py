# backend\core\app_logger_core.py

import faulthandler
import logging
import os
import sys
import threading
import traceback
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from PySide6.QtCore import qInstallMessageHandler, QtMsgType
from backend.handlers import QLogHandler, StreamToLogger

_fault_file_handle = None
_q_log_handler_instance = None

class AutoFlushTimedRotatingFileHandler(TimedRotatingFileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        if record.levelno >= logging.WARNING:
            self.flush()

logger = logging.getLogger("minikick.core.app_logger")

def _qt_message_handler(mode: QtMsgType, context, message: str):
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
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.critical("[Thread Crash] Excepción no controlada en hilo '%s':\n%s", thread_name, tb_text)
    if _fault_file_handle:
        try:
            _fault_file_handle.write(f"\n[{now_str}] [THREAD_CRASH] Unhandled exception in thread '{thread_name}':\n{tb_text}\n")
            _fault_file_handle.flush()
        except Exception:
            pass
    flush_all_logs()

def flush_all_logs():
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
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
        for root, dirs, files in os.walk(pyside_dir):
            for f in files:
                if f.startswith('avutil') and f.endswith('.dll'):
                    dll_path = os.path.join(root, f)
                    avutil = ctypes.CDLL(dll_path)
                    avutil.av_log_set_level(16)
                    return
    except Exception:
        pass

def setup_application_logging():
    global _fault_file_handle, _q_log_handler_instance
    
    if _q_log_handler_instance is not None:
        return logging.getLogger(), _q_log_handler_instance

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) 
    
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
    
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)   
    logger.addHandler(file_handler)
    
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
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _fault_file_handle.write(
            f"\n================================================================================\n"
            f"[{now_str}] [BOOTSTRAP] --- MiniKick Session Started (Faulthandler active) ---\n"
            f"================================================================================\n"
        )
        _fault_file_handle.flush()
        faulthandler.enable(file=_fault_file_handle, all_threads=True)
    except Exception as fh_err:
        logger.warning("[Bootstrap] No se pudo habilitar faulthandler: %s", fh_err)

    threading.excepthook = _threading_excepthook

    try:
        qInstallMessageHandler(_qt_message_handler)
    except Exception as q_err:
        logger.warning("[Bootstrap] No se pudo instalar el MessageHandler de Qt: %s", q_err)
    
    return logger, _q_log_handler_instance
