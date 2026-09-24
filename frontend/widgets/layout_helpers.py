# frontend\widgets\layout_helpers.py

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel, QLineEdit,
    QStyleOptionFrame, QStyle
)
from frontend.common import MARGIN_NONE, MARGIN_LG, SPACING_LG, SPACING_MD, SPACING_SM, SPACING_XS

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
    spacing: int = SPACING_XS,
    parent: QWidget | None = None
) -> tuple[QVBoxLayout, QLabel]:
    col = create_col_layout(spacing=spacing)
    return _assemble_field(col, widget, label_text, role, label_first=True, parent=parent)


def create_switch_field(
    switch: QWidget,
    label_text: str,
    role: str = "body",
    spacing: int = SPACING_SM,
    parent: QWidget | None = None,
    label_first: bool = False
) -> tuple[QHBoxLayout, QLabel]:
    box = create_row_layout(spacing=spacing)
    return _assemble_field(box, switch, label_text, role, label_first=label_first, parent=parent)


def create_box_layout(
    direction: QBoxLayout.Direction = QBoxLayout.Direction.LeftToRight,
    spacing: int = SPACING_MD,
    margins: tuple[int, int, int, int] = MARGIN_NONE,
    parent: QWidget | None = None
) -> QBoxLayout:
    layout = QBoxLayout(direction, parent) if parent else QBoxLayout(direction)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def create_two_column_container(
    parent: QWidget | None = None,
    spacing: int = SPACING_MD,
    margins: tuple[int, int, int, int] = MARGIN_NONE
) -> tuple[QWidget, QVBoxLayout, QBoxLayout, QVBoxLayout, QVBoxLayout]:
    body_container = QWidget(parent) if parent else QWidget()
    body_layout = create_col_layout(spacing=spacing, margins=margins, parent=body_container)
    columns_layout = create_box_layout(QBoxLayout.Direction.LeftToRight, spacing=spacing, margins=margins)

    col1 = QWidget(body_container)
    col1_layout = create_col_layout(spacing=spacing, margins=margins, parent=col1)
    col1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    col2 = QWidget(body_container)
    col2_layout = create_col_layout(spacing=spacing, margins=margins, parent=col2)
    col2_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    columns_layout.addWidget(col1, stretch=1)
    columns_layout.addWidget(col2, stretch=1)
    body_layout.addLayout(columns_layout)

    return body_container, body_layout, columns_layout, col1_layout, col2_layout


def create_frameless_input(
    parent: QWidget | None = None,
    placeholder: str = "",
    on_text_changed=None,
    on_return_pressed=None,
    event_filter_parent: QWidget | None = None
) -> QLineEdit:
    txt = QLineEdit(parent) if parent else QLineEdit()
    if placeholder:
        txt.setPlaceholderText(placeholder)
    txt.setFrame(False)
    if on_text_changed:
        txt.textChanged.connect(on_text_changed)
    if on_return_pressed:
        txt.returnPressed.connect(on_return_pressed)
    if event_filter_parent:
        txt.installEventFilter(event_filter_parent)
    return txt


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


def create_error_label(parent: QWidget | None = None) -> QLabel:
    lbl = QLabel(parent) if parent else QLabel()
    lbl.setProperty("state", "error")
    lbl.setWordWrap(True)
    lbl.hide()
    return lbl


def sync_platform_switch_state(switch, is_connected: bool, offline_tooltip: str = "", auto_check: bool = False):
    switch.setEnabled(is_connected)
    if auto_check:
        switch.setChecked(is_connected)
    elif not is_connected:
        switch.setChecked(False)
    switch.setToolTip(offline_tooltip if not is_connected else "")


def sync_dual_platform_switches(switch_kick, switch_twitch, connected_platforms: dict[str, bool] | None, offline_tooltip: str = "", auto_check: bool = False):
    conns = connected_platforms or {}
    kick_on = bool(conns.get("kick", False))
    twitch_on = bool(conns.get("twitch", False))
    sync_platform_switch_state(switch_kick, kick_on, offline_tooltip, auto_check=auto_check)
    sync_platform_switch_state(switch_twitch, twitch_on, offline_tooltip, auto_check=auto_check)


def create_platform_switches(
    kick_label: str = "Kick",
    twitch_label: str = "Twitch",
    checked_default: bool = True,
    spacing: int = SPACING_LG,
    field_spacing: int = SPACING_MD,
    parent: QWidget | None = None,
    on_kick_toggled=None,
    on_twitch_toggled=None,
    add_stretch: bool = True,
    label_first: bool = False
):
    from frontend.widgets.controls_widget import ModernSwitch
    switches_row = create_row_layout(spacing=spacing)
    
    switch_kick = ModernSwitch(parent=parent)
    switch_kick.setChecked(checked_default)
    if on_kick_toggled:
        switch_kick.toggled.connect(on_kick_toggled)
    kick_box, _ = create_switch_field(switch_kick, kick_label, spacing=field_spacing, label_first=label_first)
    switches_row.addLayout(kick_box)

    switch_twitch = ModernSwitch(parent=parent)
    switch_twitch.setChecked(checked_default)
    if on_twitch_toggled:
        switch_twitch.toggled.connect(on_twitch_toggled)
    twitch_box, _ = create_switch_field(switch_twitch, twitch_label, spacing=field_spacing, label_first=label_first)
    switches_row.addLayout(twitch_box)
    
    if add_stretch:
        switches_row.addStretch()

    return switches_row, switch_kick, switch_twitch

def render_styled_frame_background(widget: QWidget) -> None:
    opt = QStyleOptionFrame()
    opt.initFrom(widget)
    p = QPainter(widget)
    widget.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, widget)
    p.end()
