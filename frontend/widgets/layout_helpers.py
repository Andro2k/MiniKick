# frontend\widgets\layout_helpers.py

from __future__ import annotations
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel
from frontend.common import MARGIN_NONE, MARGIN_LG, SPACING_MD, SPACING_SM, SPACING_XS

def create_card_frame(
    role: str = "card",
    margins: tuple[int, int, int, int] = MARGIN_LG,
    spacing: int = SPACING_MD,
    parent: QWidget | None = None
) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame(parent) if parent else QFrame()
    if role:
        card.setProperty("role", role)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return card, layout


def create_row_layout(
    spacing: int = SPACING_MD,
    margins: tuple[int, int, int, int] = MARGIN_NONE,
    parent: QWidget | None = None
) -> QHBoxLayout:
    layout = QHBoxLayout(parent) if parent else QHBoxLayout()
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def create_col_layout(
    spacing: int = SPACING_SM,
    margins: tuple[int, int, int, int] = MARGIN_NONE,
    parent: QWidget | None = None
) -> QVBoxLayout:
    layout = QVBoxLayout(parent) if parent else QVBoxLayout()
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def create_labeled_field(
    label_text: str,
    widget: QWidget,
    role: str = "h3",
    spacing: int = SPACING_XS,
    parent: QWidget | None = None
) -> tuple[QVBoxLayout, QLabel]:
    col = create_col_layout(spacing=spacing, parent=parent)
    lbl = QLabel(label_text, parent)
    if role:
        lbl.setProperty("role", role)
    col.addWidget(lbl)
    col.addWidget(widget)
    return col, lbl
