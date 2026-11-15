# frontend\components\music\table_cell_utils.py
"""Celdas de acción reutilizables para las tablas del módulo de música."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from frontend.common import get_icon_colored, Size
from frontend.widgets import configure_icon_only_button


def build_icon_button(icon_name: str, color: str, tooltip: str, on_click) -> QPushButton:
    btn = QPushButton()
    btn.setProperty("role", "btn_ghost")
    btn.setIcon(get_icon_colored(icon_name, color))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip(tooltip)
    configure_icon_only_button(btn, size=Size.ICON_SMALL)
    btn.clicked.connect(lambda *_: on_click())
    return btn


def build_action_cell(*buttons: QPushButton) -> QWidget:
    cell = QWidget()
    layout = QHBoxLayout(cell)
    layout.setContentsMargins(*Size.Margin.MRG_NON)
    layout.setSpacing(Size.SPACING_XS)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    for btn in buttons:
        layout.addWidget(btn)
    return cell
