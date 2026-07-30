# frontend\components\music\commands_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from frontend.widgets import ModernCard, ModernSwitch, SettingRow

class MusicCommandsPanel(QWidget):
    command_toggled = Signal(str, bool)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
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

        self.sw_sr = ModernSwitch()
        self.sw_sr.toggled.connect(lambda val: self.command_toggled.emit("!sr", val))
        row_sr = SettingRow("add.svg", self.i18n.get("music.cmds.sr_label"), self.i18n.get("music.cmds.sr_desc"), self.sw_sr)

        self.sw_skip = ModernSwitch()
        self.sw_skip.toggled.connect(lambda val: self.command_toggled.emit("!skip", val))
        row_skip = SettingRow("player-skip-forward.svg", self.i18n.get("music.cmds.skip_label"), self.i18n.get("music.cmds.skip_desc"), self.sw_skip)

        self.sw_song = ModernSwitch()
        self.sw_song.toggled.connect(lambda val: self.command_toggled.emit("!song", val))
        row_song = SettingRow("info-circle.svg", self.i18n.get("music.cmds.song_label"), self.i18n.get("music.cmds.song_desc"), self.sw_song)

        self.sw_pause = ModernSwitch()
        self.sw_pause.toggled.connect(lambda val: self.command_toggled.emit("!pause", val))
        row_pause = SettingRow("player-pause.svg", self.i18n.get("music.cmds.pause_label"), self.i18n.get("music.cmds.pause_desc"), self.sw_pause)

        self.sw_resume = ModernSwitch()
        self.sw_resume.toggled.connect(lambda val: self.command_toggled.emit("!resume", val))
        row_resume = SettingRow("player-play.svg", self.i18n.get("music.cmds.resume_label"), self.i18n.get("music.cmds.resume_desc"), self.sw_resume)

        self.sw_playlist = ModernSwitch()
        self.sw_playlist.toggled.connect(lambda val: self.command_toggled.emit("!playlist", val))
        row_playlist = SettingRow("list.svg", self.i18n.get("music.cmds.playlist_label"), self.i18n.get("music.cmds.playlist_desc"), self.sw_playlist)

        self.sw_volume = ModernSwitch()
        self.sw_volume.toggled.connect(lambda val: self.command_toggled.emit("!vol", val))
        row_volume = SettingRow("volume.svg", self.i18n.get("music.cmds.vol_label"), self.i18n.get("music.cmds.vol_desc"), self.sw_volume)

        self.card_cmds.addWidget(row_sr)
        self.card_cmds.addWidget(row_skip)
        self.card_cmds.addWidget(row_song)
        self.card_cmds.addWidget(row_pause)
        self.card_cmds.addWidget(row_resume)
        self.card_cmds.addWidget(row_playlist)
        self.card_cmds.addWidget(row_volume)
        
        panel_layout.addWidget(self.card_cmds, alignment=Qt.AlignmentFlag.AlignTop)

    def set_enabled_state(self, enabled: bool):
        self.card_cmds.setEnabled(enabled)
