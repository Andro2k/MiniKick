# frontend\widgets\layout_helpers.py

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel
from frontend.common import Size

def create_card_frame(
    role: str = "card",
    margins: tuple[int, int, int, int] = Size.Margin.MRG_LRG,
    spacing: int = Size.SPACING_MD,
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
    spacing: int = Size.SPACING_MD,
    margins: tuple[int, int, int, int] = Size.Margin.MRG_NON,
    parent: QWidget | None = None
) -> QHBoxLayout:
    layout = QHBoxLayout(parent) if parent else QHBoxLayout()
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def create_col_layout(
    spacing: int = Size.SPACING_SM,
    margins: tuple[int, int, int, int] = Size.Margin.MRG_NON,
    parent: QWidget | None = None
) -> QVBoxLayout:
    layout = QVBoxLayout(parent) if parent else QVBoxLayout()
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def _assemble_field(
    box: QBoxLayout,
    widget: QWidget,
    label_text: str,
    role: str = "h3",
    label_first: bool = True,
    parent: QWidget | None = None
) -> tuple[QBoxLayout, QLabel]:
    lbl = QLabel(label_text, parent)
    if role:
        lbl.setProperty("role", role)
    if label_first:
        box.addWidget(lbl)
        box.addWidget(widget)
    else:
        box.addWidget(widget)
        box.addWidget(lbl)
    return box, lbl


def create_labeled_field(
    label_text: str,
    widget: QWidget,
    role: str = "h3",
    spacing: int = Size.SPACING_XS,
    parent: QWidget | None = None
) -> tuple[QVBoxLayout, QLabel]:
    col = create_col_layout(spacing=spacing)
    return _assemble_field(col, widget, label_text, role, label_first=True, parent=parent)


def create_switch_field(
    switch: QWidget,
    label_text: str,
    role: str = "body",
    spacing: int = Size.SPACING_SM,
    parent: QWidget | None = None,
    label_first: bool = False
) -> tuple[QHBoxLayout, QLabel]:
    box = create_row_layout(spacing=spacing)
    return _assemble_field(box, switch, label_text, role, label_first=label_first, parent=parent)


def create_box_layout(
    direction: QBoxLayout.Direction = QBoxLayout.Direction.LeftToRight,
    spacing: int = Size.SPACING_MD,
    margins: tuple[int, int, int, int] = Size.Margin.MRG_NON,
    parent: QWidget | None = None
) -> QBoxLayout:
    layout = QBoxLayout(direction, parent) if parent else QBoxLayout(direction)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def create_text_label(
    text: str,
    role: str = "caption",
    word_wrap: bool = True,
    alignment: Qt.AlignmentFlag | None = None,
    parent: QWidget | None = None
) -> QLabel:
    lbl = QLabel(text, parent) if parent else QLabel(text)
    if role:
        lbl.setProperty("role", role)
    if word_wrap:
        lbl.setWordWrap(True)
    if alignment is not None:
        lbl.setAlignment(alignment)
    return lbl


def create_error_label(
    parent: QWidget | None = None
) -> QLabel:
    lbl = QLabel(parent) if parent else QLabel()
    lbl.setProperty("state", "error")
    lbl.setWordWrap(True)
    lbl.hide()
    return lbl
