# bootstrap\__init__.py

from importlib import import_module
from typing import TYPE_CHECKING

_EXPORTS = {
    "configure_environment": ".environment",
    "Application": ".application",
    "CrashHandler": ".crash",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    module_path = _EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_path, package=__name__), name)
    globals()[name] = value
    return value


if TYPE_CHECKING:
    from .application import Application
    from .crash import CrashHandler
    from .environment import configure_environment