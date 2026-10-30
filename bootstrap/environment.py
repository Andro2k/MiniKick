# bootstrap\environment.py\\

import logging
import os
import sys
import time

PROCESS_STARTED = time.perf_counter()

logger = logging.getLogger("minikick.bootstrap.env")

_QT_LOGGING_RULES = (
    "qt.multimedia.*=false;"
    "qt.multimedia.ffmpeg.*=false;"
    "qt.qpa.wayland.*=false"
)
_WINDOWS_APP_ID = "MiniKick"


def configure_environment() -> None:
    _load_dotenv()
    os.environ["AV_LOG_LEVEL"] = "fatal"
    os.environ["QT_LOGGING_RULES"] = _QT_LOGGING_RULES
    _sanitize_path()
    _silence_proactor_warnings()


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_WINDOWS_APP_ID)
        logger.debug("[Bootstrap] Set explicit AppUserModelID: %s", _WINDOWS_APP_ID)
    except Exception as e:
        logger.debug("[Bootstrap] Could not set AppUserModelID: %s", e)


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _sanitize_path() -> None:
    entries = os.environ.get("PATH", "").split(os.pathsep)
    valid = [p for p in entries if p.strip() and _is_accessible_dir(p)]
    os.environ["PATH"] = os.pathsep.join(valid)


def _is_accessible_dir(path: str) -> bool:
    try:
        return os.path.isdir(path)
    except OSError:
        return False


def _silence_proactor_warnings() -> None:
    if sys.platform != "win32":
        return
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _ProactorBasePipeTransport.__del__ = lambda self, _warn=None: None
    except Exception:
        pass