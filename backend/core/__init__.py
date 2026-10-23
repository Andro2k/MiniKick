# backend\core\__init__.py

from typing import TYPE_CHECKING

_EXPORTS = {
    "AppContainerCore": ".app_container_core",
    "setup_application_logging": ".app_logger_core",
    "flush_all_logs": ".app_logger_core",
    "get_log_dir": ".app_logger_core",
    "AutoFlushTimedRotatingFileHandler": ".app_logger_core",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name in _EXPORTS:
        import importlib

        module = importlib.import_module(_EXPORTS[name], package=__name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:
    from .app_container_core import AppContainerCore
    from .app_logger_core import (
        AutoFlushTimedRotatingFileHandler,
        flush_all_logs,
        get_log_dir,
        setup_application_logging,
    )
