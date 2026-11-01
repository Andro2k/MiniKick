# frontend\widgets\row_action_menu.py

from dataclasses import dataclass
from typing import Callable
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtWidgets import QMenu, QWidget
from frontend.common import get_icon_colored, Palette, ROW_ACTION_COLORS

DANGER_ROLE = "row_action_danger"
MENU_ICON_SIZE = 16
MENU_ANCHOR_GAP = 4


@dataclass(frozen=True)
class RowMenuAction:
    text: str
    icon_name: str
    callback: Callable[[], None]
    role: str = "row_action"
    enabled: bool = True
    tooltip: str = ""


class RowActionMenu(QMenu):
    def __init__(self, actions: list[RowMenuAction], parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("role", "row_menu")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setToolTipsVisible(True)
        self.aboutToHide.connect(lambda: QTimer.singleShot(0, self.deleteLater))
        self._populate(actions)

    def _populate(self, actions: list[RowMenuAction]) -> None:
        previous_is_danger = True
        for spec in actions:
            is_danger = spec.role == DANGER_ROLE
            if is_danger and not previous_is_danger:
                self.addSeparator()
            color = ROW_ACTION_COLORS.get(spec.role, Palette.NEUTRAL_200)
            action = self.addAction(get_icon_colored(spec.icon_name, color, size=MENU_ICON_SIZE), spec.text)
            action.setEnabled(spec.enabled)
            action.setToolTip(spec.tooltip)
            action.triggered.connect(lambda _=False, cb=spec.callback: QTimer.singleShot(0, cb))
            if is_danger:
                self.setDefaultAction(action)
            previous_is_danger = is_danger

    @classmethod
    def open_below(cls, anchor: QWidget, actions: list[RowMenuAction]) -> "RowActionMenu":
        menu = cls(actions, parent=anchor.window())
        x = anchor.width() - menu.sizeHint().width()
        menu.popup(anchor.mapToGlobal(QPoint(x, anchor.height() + MENU_ANCHOR_GAP)))
        return menu
