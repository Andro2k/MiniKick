# frontend\widgets\stream_platform_widgets.py

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget
from frontend.common import BrandColors, Size, get_pixmap_colored
from .controls_widget import ModernSwitch
from .layout_helpers import create_row_layout, create_switch_field

_PLATFORM_BRANDS = {
    "KICK": ("brand-kick.svg", BrandColors.GREEN),
    "TWITCH": ("brand-twitch.svg", BrandColors.PURPLE),
}


def platform_brand_pixmap(platform: str) -> QPixmap | None:
    brand = _PLATFORM_BRANDS.get(platform.upper())
    return get_pixmap_colored(*brand) if brand else None


def sync_platform_switch_state(
    switch,
    is_connected: bool,
    offline_tooltip: str = "",
    auto_check: bool = False
):
    switch.setEnabled(is_connected)
    if auto_check:
        switch.setChecked(is_connected)
    elif not is_connected:
        switch.setChecked(False)
    switch.setToolTip(offline_tooltip if not is_connected else "")


def sync_dual_platform_switches(
    switch_kick, switch_twitch,
    connected_platforms: dict[str, bool] | None,
    offline_tooltip: str = "",
    auto_check: bool = False
):
    conns = connected_platforms or {}
    kick_on = bool(conns.get("kick", False))
    twitch_on = bool(conns.get("twitch", False))
    sync_platform_switch_state(switch_kick, kick_on, offline_tooltip, auto_check=auto_check)
    sync_platform_switch_state(switch_twitch, twitch_on, offline_tooltip, auto_check=auto_check)


def create_platform_switches(
    kick_label: str = "Kick",
    twitch_label: str = "Twitch",
    checked_default: bool = True,
    spacing: int = Size.SPACING_LG,
    field_spacing: int = Size.SPACING_MD,
    parent: QWidget | None = None,
    on_kick_toggled=None,
    on_twitch_toggled=None,
    add_stretch: bool = True,
    label_first: bool = False
):
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
