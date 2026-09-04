# frontend\components\music\commands_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from frontend.widgets import ModernCard, ModernSwitch, SettingRow

class MusicCommandsPanel(QWidget):
    command_toggled = Signal(str, bool)

    _COMMANDS_CONFIG = [
        ("!sr", "add.svg", "music.cmds.sr_label", "music.cmds.sr_desc", "sw_sr"),
        ("!skip", "player-skip.svg", "music.cmds.skip_label", "music.cmds.skip_desc", "sw_skip"),
        ("!song", "info-circle.svg", "music.cmds.song_label", "music.cmds.song_desc", "sw_song"),
        ("!pause", "player-pause.svg", "music.cmds.pause_label", "music.cmds.pause_desc", "sw_pause"),
        ("!resume", "player-play.svg", "music.cmds.resume_label", "music.cmds.resume_desc", "sw_resume"),
        ("!playlist", "list.svg", "music.cmds.playlist_label", "music.cmds.playlist_desc", "sw_playlist"),
        ("!vol", "volume.svg", "music.cmds.vol_label", "music.cmds.vol_desc", "sw_volume"),
    ]

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.switches: dict[str, ModernSwitch] = {}
        self._setup_ui()

    def _setup_ui(self):
        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(16)
        panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.card_cmds = ModernCard(margin=12, spacing=8)
        self.card_cmds.setEnabled(False)

        lbl_title = QLabel(self.i18n.get("music.cmds.title"))
        lbl_title.setProperty("role", "h3")
        self.card_cmds.addWidget(lbl_title)

        for cmd, icon, lbl_key, desc_key, attr_name in self._COMMANDS_CONFIG:
            sw = ModernSwitch()
            sw.toggled.connect(lambda val, c=cmd: self.command_toggled.emit(c, val))
            self.switches[cmd] = sw
            setattr(self, attr_name, sw)
            row = SettingRow(icon, self.i18n.get(lbl_key), self.i18n.get(desc_key), sw)
            self.card_cmds.addWidget(row)

        panel_layout.addWidget(self.card_cmds, alignment=Qt.AlignmentFlag.AlignTop)

    def set_enabled_state(self, enabled: bool):
        self.card_cmds.setEnabled(enabled)

    def set_switch_states(self, states: dict[str, bool]) -> None:
        for cmd, sw in self.switches.items():
            val = bool(states.get(cmd, False))
            if sw.isChecked() != val:
                sw.blockSignals(True)
                sw.setChecked(val)
                sw.blockSignals(False)
