# resources\tests\test_stream_platform_widgets.py

import inspect
import re

from PySide6.QtWidgets import QLabel

from frontend.widgets import layout_helpers, stream_platform_widgets as platform_widgets
from frontend.widgets.controls_widget import ModernSwitch


class _FakeSwitch:
    def __init__(self, checked: bool = True):
        self.enabled, self.checked, self.tooltip = True, checked, ""

    def setEnabled(self, value): self.enabled = value
    def setChecked(self, value): self.checked = value
    def setToolTip(self, text): self.tooltip = text


def test_layout_helpers_is_domain_agnostic():
    source = inspect.getsource(layout_helpers)
    assert not re.search(r"kick|twitch|platform", source, re.IGNORECASE)
    for moved in ("sync_platform_switch_state", "sync_dual_platform_switches", "create_platform_switches"):
        assert not hasattr(layout_helpers, moved)


def test_platform_helpers_live_in_the_stream_module_and_stay_public():
    import frontend.widgets as widgets

    assert widgets.create_platform_switches is platform_widgets.create_platform_switches
    assert widgets.sync_dual_platform_switches is platform_widgets.sync_dual_platform_switches


def test_offline_platform_switch_is_disabled_unchecked_and_explained():
    switch = _FakeSwitch(checked=True)
    platform_widgets.sync_platform_switch_state(switch, False, "Sin conexión")
    assert (switch.enabled, switch.checked, switch.tooltip) == (False, False, "Sin conexión")


def test_online_platform_switch_keeps_or_forces_its_checked_state():
    switch = _FakeSwitch(checked=False)
    platform_widgets.sync_platform_switch_state(switch, True, "Sin conexión")
    assert (switch.enabled, switch.checked, switch.tooltip) == (True, False, "")

    platform_widgets.sync_platform_switch_state(switch, True, auto_check=True)
    assert switch.checked is True


def test_dual_switches_follow_each_platform_connection():
    kick, twitch = _FakeSwitch(), _FakeSwitch()
    platform_widgets.sync_dual_platform_switches(kick, twitch, {"kick": True}, "Offline")
    assert (kick.enabled, kick.checked, kick.tooltip) == (True, True, "")
    assert (twitch.enabled, twitch.checked, twitch.tooltip) == (False, False, "Offline")

    platform_widgets.sync_dual_platform_switches(kick, twitch, None, "Offline", auto_check=True)
    assert (kick.enabled, twitch.enabled, kick.checked, twitch.checked) == (False, False, False, False)


def test_create_platform_switches_builds_two_labelled_switches(qapp):
    toggled = []
    row, kick, twitch = platform_widgets.create_platform_switches(
        kick_label="K", twitch_label="T", checked_default=False,
        on_kick_toggled=lambda v: toggled.append(("kick", v)),
        on_twitch_toggled=lambda v: toggled.append(("twitch", v)),
    )

    assert isinstance(kick, ModernSwitch) and isinstance(twitch, ModernSwitch)
    assert not kick.isChecked() and not twitch.isChecked()
    assert row.count() == 3

    labels = [row.itemAt(i).layout().itemAt(1).widget() for i in range(2)]
    assert all(isinstance(label, QLabel) for label in labels)
    assert [label.text() for label in labels] == ["K", "T"]

    kick.setChecked(True)
    twitch.setChecked(True)
    assert toggled == [("kick", True), ("twitch", True)]


def test_create_platform_switches_can_skip_the_trailing_stretch(qapp):
    row, _, _ = platform_widgets.create_platform_switches(add_stretch=False, label_first=True)
    assert row.count() == 2
    assert row.itemAt(0).layout().itemAt(0).widget().text() == "Kick"


def test_platform_brand_pixmap_only_knows_streaming_platforms(qapp):
    assert not platform_widgets.platform_brand_pixmap("kick").isNull()
    assert not platform_widgets.platform_brand_pixmap("TWITCH").isNull()
    assert platform_widgets.platform_brand_pixmap("youtube") is None
