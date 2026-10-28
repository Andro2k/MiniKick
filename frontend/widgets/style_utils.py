# frontend\widgets\style_utils.py

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget


def repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def set_state(widget: QWidget, state: str) -> None:
    widget.setProperty("state", state)
    repolish(widget)


def sync_focus_state(widget: QWidget, event_type: QEvent.Type) -> None:
    if event_type == QEvent.Type.FocusIn:
        set_state(widget, "focused")
    elif event_type == QEvent.Type.FocusOut:
        set_state(widget, "")
