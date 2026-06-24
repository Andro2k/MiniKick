# frontend/views/music_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QFrame, QScrollArea)
from PySide6.QtCore import Qt, Signal

from frontend.common.theme import COLOR_ACCENT, COLOR_TEXT_SECONDARY
from frontend.common.utils import get_icon_colored
from frontend.widgets.blocks_component import ViewHeader, SettingRow
from frontend.widgets.controls_component import ModernButton, ModernSwitch


class MusicView(QWidget):
    connect_requested = Signal()
    disconnect_requested = Signal()
    command_toggled = Signal(str, bool)

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)

        self.header = ViewHeader(
            title_text=self.i18n.get("music.header.title"),
            subtitle_text=self.i18n.get("music.header.subtitle"),
            icon_name="volume.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        self._setup_auth_card()
        self._setup_now_playing_card()
        self._setup_commands_card()

        self.main_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def _setup_auth_card(self):
        card = QFrame()
        card.setProperty("role", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        status_layout = QHBoxLayout()
        self.lbl_provider_name = QLabel(self.i18n.get("music.provider.name"))
        self.lbl_provider_name.setProperty("role", "h3")
        
        self.lbl_auth_status = QLabel(self.i18n.get("music.status.disconnected"))
        self.lbl_auth_status.setProperty("role", "body")
        
        provider_info = QVBoxLayout()
        provider_info.addWidget(self.lbl_provider_name)
        provider_info.addWidget(self.lbl_auth_status)

        self.btn_connect = ModernButton(self.i18n.get("music.btn.connect"), role="action_accent")
        self.btn_connect.setFixedSize(150, 36)
        self.btn_connect.clicked.connect(self.connect_requested.emit)

        self.btn_disconnect = ModernButton(self.i18n.get("music.btn.disconnect"), role="action_danger")
        self.btn_disconnect.setFixedSize(120, 36)
        self.btn_disconnect.setVisible(False)
        self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)

        status_layout.addLayout(provider_info, stretch=1)
        status_layout.addWidget(self.btn_connect)
        status_layout.addWidget(self.btn_disconnect)

        layout.addLayout(status_layout)
        self.main_layout.addWidget(card)

    def _setup_now_playing_card(self):
        self.card_player = QFrame()
        self.card_player.setProperty("role", "card")
        self.card_player.setVisible(False)
        
        layout = QHBoxLayout(self.card_player)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        icon_music = QLabel()
        icon_music.setPixmap(get_icon_colored("brand-spotify.svg", COLOR_ACCENT, 28).pixmap(28, 28))
        
        info_layout = QVBoxLayout()
        self.lbl_song_title = QLabel(self.i18n.get("music.player.not_playing"))
        self.lbl_song_title.setProperty("role", "h2")
        
        self.lbl_song_artist = QLabel("-")
        self.lbl_song_artist.setProperty("role", "body")
        self.lbl_song_artist.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")

        info_layout.addWidget(self.lbl_song_title)
        info_layout.addWidget(self.lbl_song_artist)

        layout.addWidget(icon_music, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(info_layout, stretch=1)
        
        self.main_layout.addWidget(self.card_player)

    def _setup_commands_card(self):
        self.card_cmds = QFrame()
        self.card_cmds.setProperty("role", "card")
        self.card_cmds.setEnabled(False)
        
        layout = QVBoxLayout(self.card_cmds)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        lbl_title = QLabel(self.i18n.get("music.cmds.title"))
        lbl_title.setProperty("role", "h2")
        layout.addWidget(lbl_title)

        self.sw_sr = ModernSwitch()
        self.sw_sr.toggled.connect(lambda val: self.command_toggled.emit("!sr", val))
        row_sr = SettingRow("add.svg", self.i18n.get("music.cmds.sr_label"), self.i18n.get("music.cmds.sr_desc"), self.sw_sr)

        self.sw_skip = ModernSwitch()
        self.sw_skip.toggled.connect(lambda val: self.command_toggled.emit("!skip", val))
        row_skip = SettingRow("chevron-right-pipe.svg", self.i18n.get("music.cmds.skip_label"), self.i18n.get("music.cmds.skip_desc"), self.sw_skip)

        self.sw_song = ModernSwitch()
        self.sw_song.toggled.connect(lambda val: self.command_toggled.emit("!song", val))
        row_song = SettingRow("info-circle.svg", self.i18n.get("music.cmds.song_label"), self.i18n.get("music.cmds.song_desc"), self.sw_song)

        layout.addWidget(row_sr)
        layout.addWidget(row_skip)
        layout.addWidget(row_song)
        
        self.main_layout.addWidget(self.card_cmds)

    def set_auth_state(self, connected: bool, label_key: str = ""):
        self.btn_connect.setVisible(not connected)
        self.btn_disconnect.setVisible(connected)
        self.card_cmds.setEnabled(connected)
        self.card_player.setVisible(connected)

        if connected:
            translated_label = self.i18n.get(label_key)
            self.lbl_auth_status.setText(f"{self.i18n.get('music.status.active')}: {translated_label}")
            self.lbl_auth_status.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: bold;")
        else:
            self.lbl_auth_status.setText(self.i18n.get("music.status.disconnected"))
            self.lbl_auth_status.setStyleSheet("")

    def update_current_song(self, song_data: dict | None):
        if not song_data:
            self.lbl_song_title.setText(self.i18n.get("music.player.paused_title"))
            self.lbl_song_artist.setText(self.i18n.get("music.player.paused_desc"))
            return

        self.lbl_song_title.setText(song_data.get("title", ""))
        self.lbl_song_artist.setText(song_data.get("artist", ""))