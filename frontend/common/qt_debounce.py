# frontend\common\qt_debounce.py

from typing import Callable
from PySide6.QtCore import QTimer


def qt_debounce(callback: Callable[[], None], delay_ms: int) -> Callable[[], None]:
    timer = QTimer()
    timer.setSingleShot(True)
    timer.setInterval(delay_ms)
    timer.timeout.connect(callback)
    return timer.start
