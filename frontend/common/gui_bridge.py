# frontend\common\gui_bridge.py

import functools
import logging
import threading
from typing import Callable

from PySide6.QtCore import QCoreApplication, QObject, Qt, Signal, Slot

logger = logging.getLogger("minikick.frontend.gui_bridge")


class _GuiBridge(QObject):
    _call = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._call.connect(self._run, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _run(self, fn: Callable[[], None]) -> None:
        try:
            fn()
        except RuntimeError as e:
            logger.debug("GUI call skipped (object already deleted): %s", e)


_bridge: _GuiBridge | None = None
_bridge_lock = threading.Lock()


def _get_bridge() -> _GuiBridge:
    global _bridge
    with _bridge_lock:
        if _bridge is None:
            bridge = _GuiBridge()
            app = QCoreApplication.instance()
            if app is not None:
                bridge.moveToThread(app.thread())
            _bridge = bridge
        return _bridge


def run_on_gui(fn: Callable, *args, **kwargs) -> None:
    _get_bridge()._call.emit(functools.partial(fn, *args, **kwargs))
