# frontend\views\music_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                                QLabel, QScrollArea, QPushButton)
from PySide6.QtCore import Qt, Signal, QSize
from frontend.common.theme import COLOR_RED, COLOR_GREEN, COLOR_NEUTRAL_200
from frontend.common.utils import get_icon_colored, get_icon, NoWheelComboBox, NoWheelSlider
from frontend.widgets.base_view import BaseView
from frontend.widgets.blocks_component import SettingRow, SliderRow, ModernCard
from frontend.widgets.controls_component import ModernButton, ModernSwitch
from frontend.widgets.flow_layout import FlowLayout

class MusicView(BaseView):
    connect_requested = Signal()
    disconnect_requested = Signal()
    command_toggled = Signal(str, bool)
    provider_changed = Signal(str)
    volume_changed = Signal(int)
    remove_queue_item_requested = Signal(int)
    play_pause_requested = Signal()
    skip_requested = Signal()
    youtube_auto_resume_toggled = Signal(bool)

    def __init__(self, i18n):
        super().__init__(
            i18n=i18n,
            title_key="music.header.title",
            subtitle_key="music.header.subtitle"
        )
        self._setup_ui()

    def _setup_ui(self):
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(12)

        self._setup_provider_selection_card()
        self._setup_auth_card()
        self._setup_now_playing_card()
        self._setup_queue_card()
        self._setup_commands_card()

        self.main_layout.addWidget(self.body_container)
        self.main_layout.addStretch()

    def _setup_provider_selection_card(self):
        card = ModernCard(margin=12, spacing=8)

        self.combo_provider = NoWheelComboBox()
        self.combo_provider.addItem("Spotify", "spotify")
        self.combo_provider.addItem("YouTube", "youtube")
        
        self.combo_provider.currentIndexChanged.connect(
            lambda: self.provider_changed.emit(self.combo_provider.currentData())
        )

        row_provider = SettingRow(
            icon_name="headphones.svg",
            title_text=self.i18n.get("music.provider.select_title"),
            desc_text=self.i18n.get("music.provider.select_desc"),
            right_widget=self.combo_provider
        )
        card.addWidget(row_provider)

        self.sw_auto_resume = ModernSwitch()
        self.sw_auto_resume.toggled.connect(self.youtube_auto_resume_toggled.emit)
        self.row_auto_resume = SettingRow(
            icon_name="refresh.svg",
            title_text=self.i18n.get("music.youtube.auto_resume_title"),
            desc_text=self.i18n.get("music.youtube.auto_resume_desc"),
            right_widget=self.sw_auto_resume
        )
        self.row_auto_resume.setVisible(False)
        card.addWidget(self.row_auto_resume)

        self.body_layout.addWidget(card)

    def _setup_auth_card(self):
        card = ModernCard(margin=12, spacing=8)

        status_layout = QHBoxLayout()
        self.lbl_provider_name = QLabel(self.i18n.get("music.provider.name"))
        self.lbl_provider_name.setProperty("role", "h3")
        
        self.lbl_auth_status = QLabel(self.i18n.get("common.status.disconnected"))
        self.lbl_auth_status.setProperty("role", "body")
        
        provider_info = QVBoxLayout()
        provider_info.addWidget(self.lbl_provider_name)
        provider_info.addWidget(self.lbl_auth_status)

        self.btn_connect = ModernButton(self.i18n.get("common.buttons.connect"), role="action_accent")
        self.btn_connect.clicked.connect(self.connect_requested.emit)

        self.btn_disconnect = ModernButton(self.i18n.get("common.buttons.disconnect"), role="action_danger_border")
        self.btn_disconnect.setVisible(False)
        self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)

        status_layout.addLayout(provider_info, stretch=1)
        status_layout.addWidget(self.btn_connect)
        status_layout.addWidget(self.btn_disconnect)

        card.addLayout(status_layout)

        self.slider_vol = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setProperty("role", "body")
        
        self.row_vol = SliderRow(
            icon_name="volume.svg",
            title_text=self.i18n.get("music.player.volume_title"),
            desc_text=self.i18n.get("music.player.volume_desc"),
            slider_widget=self.slider_vol,
            value_label=self.lbl_vol_perc
        )
        self.row_vol.setVisible(False)
        self.slider_vol.valueChanged.connect(self._on_volume_slider_changed)
        card.addWidget(self.row_vol)

        self.body_layout.addWidget(card)

    def _on_volume_slider_changed(self, val):
        self.lbl_vol_perc.setText(f"{val}%")
        self.volume_changed.emit(val)

    def _setup_now_playing_card(self):
        self.card_player = ModernCard(margin=12, spacing=8, orientation="horizontal")
        self.card_player.setVisible(False)

        self.icon_music = QLabel()
        self.icon_music.setPixmap(get_icon_colored("spotify.svg", COLOR_GREEN, 32).pixmap(32, 32))
        
        info_layout = QVBoxLayout()
        self.lbl_song_title = QLabel(self.i18n.get("music.player.not_playing"))
        self.lbl_song_title.setProperty("role", "h3")
        self.lbl_song_title.setWordWrap(True)
        
        self.lbl_song_artist = QLabel("-")
        self.lbl_song_artist.setProperty("role", "body")
        self.lbl_song_artist.setWordWrap(True)

        info_layout.addWidget(self.lbl_song_title)
        info_layout.addWidget(self.lbl_song_artist)

        self.card_player.addWidget(self.icon_music, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.card_player.addLayout(info_layout, stretch=1)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)
        
        self.btn_play_pause = ModernButton("", role="action_neutral_border")
        self.btn_play_pause.setFixedSize(36, 36)
        self.btn_play_pause.setIcon(get_icon_colored("play.svg", COLOR_NEUTRAL_200, 18))
        self.btn_play_pause.setIconSize(QSize(18, 18))
        self.btn_play_pause.clicked.connect(self.play_pause_requested.emit)
        
        self.btn_skip = ModernButton("", role="action_neutral_border")
        self.btn_skip.setFixedSize(36, 36)
        self.btn_skip.setIcon(get_icon_colored("player-skip-forward.svg", COLOR_NEUTRAL_200, 18))
        self.btn_skip.setIconSize(QSize(18, 18))
        self.btn_skip.clicked.connect(self.skip_requested.emit)
        
        controls_layout.addWidget(self.btn_play_pause)
        controls_layout.addWidget(self.btn_skip)
        
        self.card_player.addLayout(controls_layout)
        self.body_layout.addWidget(self.card_player)

    def _setup_commands_card(self):
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

        self.card_cmds.addWidget(row_sr)
        self.card_cmds.addWidget(row_skip)
        self.card_cmds.addWidget(row_song)
        
        self.body_layout.addWidget(self.card_cmds)

    def _setup_queue_card(self):
        self.card_queue = ModernCard(margin=12, spacing=8)
        self.card_queue.setVisible(False)
        
        header_layout = QHBoxLayout()
        lbl_title = QLabel(self.i18n.get("music.queue.title"))
        lbl_title.setProperty("role", "h3")
        
        self.lbl_queue_count = QLabel("(0)")
        self.lbl_queue_count.setProperty("role", "caption")
        
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(self.lbl_queue_count)
        header_layout.addStretch()
        
        self.card_queue.addLayout(header_layout)
        
        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.queue_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_scroll.setMinimumHeight(160)
        self.queue_scroll.setMaximumHeight(320)
        
        self.queue_list_widget = QWidget()
        self.queue_list_layout = FlowLayout(self.queue_list_widget, margin=0, hspacing=8, vspacing=8)
        
        self.queue_scroll.setWidget(self.queue_list_widget)
        self.card_queue.addWidget(self.queue_scroll)
        
        self.lbl_empty_queue = QLabel(self.i18n.get("music.queue.empty"))
        self.lbl_empty_queue.setProperty("role", "body")
        self.lbl_empty_queue.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_list_layout.addWidget(self.lbl_empty_queue)
        
        self.body_layout.addWidget(self.card_queue)

    def update_queue(self, queue_items: list[dict]):
        new_urls = [song.get("url") for song in queue_items]
        if hasattr(self, "_current_queue_urls") and self._current_queue_urls == new_urls:
            return
        self._current_queue_urls = new_urls

        while self.queue_list_layout.count() > 0:
            item = self.queue_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        self.lbl_queue_count.setText(f"({len(queue_items)})")
        
        if not queue_items:
            self.lbl_empty_queue = QLabel(self.i18n.get("music.queue.empty"))
            self.lbl_empty_queue.setProperty("role", "body")
            self.lbl_empty_queue.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.queue_list_layout.addWidget(self.lbl_empty_queue)
            return

        for idx, song in enumerate(queue_items):
            item_frame = QFrame()
            item_frame.setFixedSize(264, 64)
            item_frame.setProperty("role", "bot_tag")
            item_frame.style().unpolish(item_frame)
            item_frame.style().polish(item_frame)
            
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(10, 4, 10, 4)
            item_layout.setSpacing(10)
            
            lbl_idx = QLabel(f"{idx + 1}")
            lbl_idx.setProperty("role", "caption")
            lbl_idx.setFixedWidth(16)
            item_layout.addWidget(lbl_idx)
            
            info_layout = QVBoxLayout()
            info_layout.setSpacing(1)
            
            title_text = song.get("title", "Unknown Title")
            if len(title_text) > 28:
                title_text = title_text[:25] + "..."
                
            artist_text = song.get("artist", "-")
            if len(artist_text) > 30:
                artist_text = artist_text[:27] + "..."
                
            requester = song.get("requester")
            lbl_requester_text = f"@{requester}" if requester else ""
            
            lbl_title = QLabel(title_text)
            lbl_title.setProperty("role", "h3")
            lbl_title.setWordWrap(True)
                
            lbl_artist = QLabel(artist_text)
            lbl_artist.setProperty("role", "caption")
            lbl_artist.setWordWrap(True)
            
            lbl_requester = QLabel(lbl_requester_text)
            lbl_requester.setProperty("role", "caption")
            lbl_requester.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 10px; font-weight: bold;")
            lbl_requester.setWordWrap(True)
            
            info_layout.addWidget(lbl_title)
            info_layout.addWidget(lbl_artist)
            info_layout.addWidget(lbl_requester)
            item_layout.addLayout(info_layout, stretch=1)
            
            btn_delete = QPushButton()
            btn_delete.setProperty("role", "btn_ghost")
            btn_delete.setIcon(get_icon_colored("trash.svg", COLOR_RED, 14))
            btn_delete.setIconSize(QSize(14, 14))
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setToolTip(self.i18n.get("music.queue.remove_tooltip"))
            btn_delete.setFixedSize(QSize(26, 26))
            
            btn_delete.clicked.connect(lambda *args, index=idx: self.remove_queue_item_requested.emit(index))
            item_layout.addWidget(btn_delete)
            
            self.queue_list_layout.addWidget(item_frame)

    def set_auth_state(self, connected: bool, label_key: str = ""):
        provider = self.combo_provider.currentData()
        
        if provider == "youtube":
            self.lbl_provider_name.setText("YouTube")
            self.icon_music.setPixmap(get_icon("youtube.svg").pixmap(32, 32))
            self.btn_connect.setVisible(False)
            self.btn_disconnect.setVisible(False)
            self.card_cmds.setEnabled(True)
            self.card_player.setVisible(True)
            self.card_queue.setVisible(True)
            self.row_vol.setVisible(True)
            self.row_auto_resume.setVisible(True)
            translated_label = self.i18n.get("music.status.youtube_active")
            self.lbl_auth_status.setText(f"{self.i18n.get('common.status.active')}: {translated_label}")
        else:
            self.lbl_provider_name.setText(self.i18n.get("music.provider.name"))
            self.icon_music.setPixmap(get_icon_colored("spotify.svg", COLOR_GREEN, 32).pixmap(32, 32))
            self.btn_connect.setVisible(not connected)
            self.btn_connect.setEnabled(not connected)
            self.btn_disconnect.setVisible(connected)
            self.card_cmds.setEnabled(connected)
            self.card_player.setVisible(connected)
            self.card_queue.setVisible(False)
            self.row_vol.setVisible(False)
            self.row_auto_resume.setVisible(False)

            if connected:
                translated_label = self.i18n.get(label_key) or label_key
                self.lbl_auth_status.setText(f"{self.i18n.get('common.status.active')}: {translated_label}")
            else:
                self.lbl_auth_status.setText(self.i18n.get("common.status.disconnected"))

    def update_current_song(self, song_data: dict | None):
        title = ""
        artist = ""
        is_playing = False
        
        if song_data:
            title = song_data.get("title", "")
            artist = song_data.get("artist", "")
            is_playing = song_data.get("is_playing", False)
        else:
            title = self.i18n.get("music.player.paused_title")
            artist = self.i18n.get("music.player.paused_desc")
            is_playing = False

        if (hasattr(self, "_cached_song_state") and 
            self._cached_song_state == (title, artist, is_playing)):
            return
            
        self._cached_song_state = (title, artist, is_playing)

        self.lbl_song_title.setText(title)
        self.lbl_song_artist.setText(artist)
        
        icon_name = "player-pause.svg" if is_playing else "play.svg"
        self.btn_play_pause.setIcon(get_icon_colored(icon_name, COLOR_NEUTRAL_200, 18))