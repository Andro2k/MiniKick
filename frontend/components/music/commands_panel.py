# frontend\components\music\commands_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from frontend.common import (
    MARGIN_NONE, MARGIN_TAB_PANEL, MARGIN_SETTING_ROW_COMPACT,
    SPACING_NONE, SPACING_MD
)
from frontend.widgets import ModernCard, ModernSwitch, SettingRow, SectionHeader

class MusicCommandsPanel(QWidget):
    command_toggled = Signal(str, bool)

    _COMMANDS_CONFIG = [
        ("!sr", "plus-filled.svg", "music.cmds.sr_label", "music.cmds.sr_desc", "sw_sr"),
        ("!skip", "skip-next-filled.svg", "music.cmds.skip_label", "music.cmds.skip_desc", "sw_skip"),
        ("!song", "circle-info-filled.svg", "music.cmds.song_label", "music.cmds.song_desc", "sw_song"),
        ("!pause", "pause-filled.svg", "music.cmds.pause_label", "music.cmds.pause_desc", "sw_pause"),
        ("!resume", "play-filled.svg", "music.cmds.resume_label", "music.cmds.resume_desc", "sw_resume"),
        ("!playlist", "playlist-filled.svg", "music.cmds.playlist_label", "music.cmds.playlist_desc", "sw_playlist"),
        ("!vol", "volume-up-filled.svg", "music.cmds.vol_label", "music.cmds.vol_desc", "sw_volume"),
    ]

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.setProperty("role", "tab_panel")
        self.i18n = i18n
        self.switches: dict[str, ModernSwitch] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.panel_layout = QVBoxLayout(self)
        self.panel_layout.setContentsMargins(*MARGIN_TAB_PANEL)
        self.panel_layout.setSpacing(SPACING_MD)
        self.panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        header_cmds = SectionHeader(self.i18n.get("music.cmds.title"), first=True, parent=self)
        self.panel_layout.addWidget(header_cmds)

        self.card_cmds = ModernCard(parent=self, margin=MARGIN_NONE, spacing=SPACING_NONE, orientation="vertical")
        self.card_cmds.setEnabled(False)

        for i, (cmd, icon, lbl_key, desc_key, attr_name) in enumerate(self._COMMANDS_CONFIG):
            if i > 0:
                self.card_cmds.add_separator()
            sw = ModernSwitch()
            sw.toggled.connect(lambda val, c=cmd: self.command_toggled.emit(c, val))
            self.switches[cmd] = sw
            setattr(self, attr_name, sw)
            row = SettingRow(icon, self.i18n.get(lbl_key), self.i18n.get(desc_key), sw, contents_margins=MARGIN_SETTING_ROW_COMPACT)
            self.card_cmds.addWidget(row)

        self.panel_layout.addWidget(self.card_cmds, alignment=Qt.AlignmentFlag.AlignTop)

    def set_enabled_state(self, enabled: bool):
        self.card_cmds.setEnabled(enabled)

    def set_switch_states(self, states: dict[str, bool]) -> None:
        for cmd, sw in self.switches.items():
            val = bool(states.get(cmd, False))
            if sw.isChecked() != val:
                sw.blockSignals(True)
                sw.setChecked(val)
                sw.blockSignals(False)
