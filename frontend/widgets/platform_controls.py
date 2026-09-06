# frontend\widgets\platform_controls.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal
from frontend.common import MARGIN_NONE, SPACING_XL, SPACING_SM
from .controls import ModernSwitch

class PlatformSwitchGroup(QWidget):
    platform_toggled = Signal(str, bool)

    PLATFORM_LABELS = {
        "kick": "Kick",
        "twitch": "Twitch",
        "youtube": "YouTube",
        "tiktok": "TikTok",
    }

    def __init__(
        self,
        platforms: list[str] | None = None,
        connected_platforms: dict[str, bool] | None = None,
        active_platforms: dict[str, bool] | None = None,
        offline_tooltip: str = "",
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.platforms = platforms or ["kick", "twitch"]
        self.connected_platforms = connected_platforms or {p: True for p in self.platforms}
        self.active_platforms = active_platforms or {}
        self.offline_tooltip = offline_tooltip

        self.switches: dict[str, ModernSwitch] = {}
        self.labels: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_NONE)
        layout.setSpacing(SPACING_XL)

        for plat in self.platforms:
            box = QHBoxLayout()
            box.setSpacing(SPACING_SM)

            sw = ModernSwitch(self)
            is_connected = self.connected_platforms.get(plat, False)
            is_active = self.active_platforms.get(plat, is_connected)

            sw.setEnabled(is_connected)
            sw.setChecked(is_active and is_connected)
            if not is_connected and self.offline_tooltip:
                sw.setToolTip(self.offline_tooltip)

            sw.toggled.connect(lambda checked, p=plat: self._on_toggled(p, checked))

            lbl = QLabel(self.PLATFORM_LABELS.get(plat, plat.capitalize()), self)
            lbl.setProperty("role", "body")

            box.addWidget(sw)
            box.addWidget(lbl)
            layout.addLayout(box)

            self.switches[plat] = sw
            self.labels[plat] = lbl

        layout.addStretch()

    def _on_toggled(self, plat: str, checked: bool):
        self.active_platforms[plat] = checked
        self.platform_toggled.emit(plat, checked)

    def set_connected_platforms(self, connected: dict[str, bool], offline_tooltip: str = ""):
        self.connected_platforms = connected or {}
        if offline_tooltip:
            self.offline_tooltip = offline_tooltip

        for plat, sw in self.switches.items():
            is_conn = self.connected_platforms.get(plat, False)
            sw.setEnabled(is_conn)
            if not is_conn:
                if self.offline_tooltip:
                    sw.setToolTip(self.offline_tooltip)
                sw.blockSignals(True)
                sw.setChecked(False)
                sw.blockSignals(False)
            else:
                sw.setToolTip("")

    def set_platform_checked(self, plat: str, checked: bool):
        if plat in self.switches:
            sw = self.switches[plat]
            sw.blockSignals(True)
            sw.setChecked(checked)
            sw.blockSignals(False)
            self.active_platforms[plat] = checked

    def is_platform_checked(self, plat: str) -> bool:
        sw = self.switches.get(plat)
        return sw.isChecked() if sw else False

    def get_active_platforms(self) -> dict[str, bool]:
        return {p: self.is_platform_checked(p) for p in self.platforms}
