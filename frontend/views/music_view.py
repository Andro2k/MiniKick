# frontend\views\music_view.py

from PySide6.QtWidgets import QBoxLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication, QHeaderView, QAbstractItemView, QTableWidgetItem
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from frontend.common.theme import COLOR_RED, COLOR_GREEN, COLOR_NEUTRAL_200
from frontend.common.utils import get_icon_colored, NoWheelComboBox, NoWheelSlider, get_pixmap, get_pixmap_colored
from frontend.widgets import BaseView, SettingRow, SliderRow, ModernCard, ModernButton, ModernSwitch, ModernTableCard

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

    def __init__(self, i18n, music_overlay_url: str = ""):
        super().__init__(i18n=i18n, title_key="music.header.title", subtitle_key="music.header.subtitle")
        self._music_overlay_url = music_overlay_url
        self._current_queue_urls = []
        self._cached_song_state = None
        self._last_direction = None
        self._setup_ui()

    def _setup_ui(self):
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(16)

        self.columns_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        self.columns_layout.setSpacing(16)

        col1 = QWidget()
        self.col1_layout = QVBoxLayout(col1)
        self.col1_layout.setContentsMargins(0, 0, 0, 0)
        self.col1_layout.setSpacing(16)
        self.col1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        col2 = QWidget()
        self.col2_layout = QVBoxLayout(col2)
        self.col2_layout.setContentsMargins(0, 0, 0, 0)
        self.col2_layout.setSpacing(16)

        self.columns_layout.addWidget(col1, stretch=3)
        self.columns_layout.addWidget(col2, stretch=4)

        self.body_layout.addLayout(self.columns_layout)

        self._setup_provider_selection_card()
        self._setup_auth_card()
        self._setup_now_playing_card()
        self._setup_settings_card()
        self._setup_commands_card()
        self._setup_overlay_url_card()
        self._setup_queue_card()

        self.main_layout.addWidget(self.body_container)

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
        self.col1_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

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
        self.col1_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

    def _setup_settings_card(self):
        self.card_settings = ModernCard(margin=12, spacing=8)
        self.card_settings.setVisible(False)

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
        self.card_settings.addWidget(self.row_vol)

        self.sw_auto_resume = ModernSwitch()
        self.sw_auto_resume.toggled.connect(self.youtube_auto_resume_toggled.emit)
        self.row_auto_resume = SettingRow(
            icon_name="refresh.svg",
            title_text=self.i18n.get("music.youtube.auto_resume_title"),
            desc_text=self.i18n.get("music.youtube.auto_resume_desc"),
            right_widget=self.sw_auto_resume
        )
        self.row_auto_resume.setVisible(False)
        self.card_settings.addWidget(self.row_auto_resume)

        self.col1_layout.addWidget(self.card_settings, alignment=Qt.AlignmentFlag.AlignTop)

    def _on_volume_slider_changed(self, val):
        self.lbl_vol_perc.setText(f"{val}%")
        self.volume_changed.emit(val)

    def _setup_now_playing_card(self):
        self.card_player = ModernCard(margin=12, spacing=8, orientation="horizontal")
        self.card_player.setVisible(False)

        self.icon_music = QLabel()
        self.icon_music.setPixmap(get_pixmap_colored("spotify.svg", COLOR_GREEN, 32))
        
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
        self.btn_play_pause.setIcon(get_icon_colored("player-play.svg", COLOR_NEUTRAL_200, 18))
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
        self.col1_layout.addWidget(self.card_player, alignment=Qt.AlignmentFlag.AlignTop)

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

        self.sw_pause = ModernSwitch()
        self.sw_pause.toggled.connect(lambda val: self.command_toggled.emit("!pause", val))
        row_pause = SettingRow("player-pause.svg", self.i18n.get("music.cmds.pause_label"), self.i18n.get("music.cmds.pause_desc"), self.sw_pause)

        self.sw_resume = ModernSwitch()
        self.sw_resume.toggled.connect(lambda val: self.command_toggled.emit("!resume", val))
        row_resume = SettingRow("player-play.svg", self.i18n.get("music.cmds.resume_label"), self.i18n.get("music.cmds.resume_desc"), self.sw_resume)

        self.card_cmds.addWidget(row_sr)
        self.card_cmds.addWidget(row_skip)
        self.card_cmds.addWidget(row_song)
        self.card_cmds.addWidget(row_pause)
        self.card_cmds.addWidget(row_resume)
        
        self.col1_layout.addWidget(self.card_cmds, alignment=Qt.AlignmentFlag.AlignTop)

    def _setup_overlay_url_card(self):
        self.card_overlay_url = ModernCard(margin=12, spacing=8)
        self.card_overlay_url.setVisible(False)

        url_info = QVBoxLayout()
        lbl_title = QLabel(self.i18n.get("music.overlay.url_title"))
        lbl_title.setProperty("role", "h3")
        lbl_desc = QLabel(self.i18n.get("music.overlay.url_desc"))
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        url_info.addWidget(lbl_title)
        url_info.addWidget(lbl_desc)

        theme_layout = QHBoxLayout()
        lbl_theme = QLabel(self.i18n.get("music.overlay.theme_label"))
        lbl_theme.setProperty("role", "body")
        self.combo_music_theme = NoWheelComboBox()
        self.combo_music_theme.addItem("Glassmorphism", "glass")
        self.combo_music_theme.addItem("Minimalist", "minimal")
        self.combo_music_theme.addItem("Neon Glow", "neon")
        self.combo_music_theme.addItem("Cyberpunk", "cyber")
        self.combo_music_theme.addItem("Premium Card", "card")
        
        theme_layout.addWidget(lbl_theme)
        theme_layout.addWidget(self.combo_music_theme)

        self.btn_copy_music_url = ModernButton(
            self.i18n.get("common.buttons.copy"),
            role="action_neutral_border"
        )
        self.btn_copy_music_url.clicked.connect(self._copy_music_overlay_url)

        self.card_overlay_url.addLayout(url_info)
        self.card_overlay_url.addLayout(theme_layout)
        self.card_overlay_url.addWidget(self.btn_copy_music_url)
        self.col1_layout.addWidget(self.card_overlay_url, alignment=Qt.AlignmentFlag.AlignTop)

    def _setup_queue_card(self):
        self.card_queue = ModernTableCard(
            title_text=self.i18n.get("music.queue.title"),
            headers=[
                self.i18n.get("music.queue.col_num"),
                self.i18n.get("music.queue.col_title"),
                self.i18n.get("music.queue.col_artist"),
                self.i18n.get("music.queue.col_requester"),
                self.i18n.get("music.queue.col_duration"),
                self.i18n.get("music.queue.col_actions")
            ]
        )
        self.card_queue.setVisible(False)
        
        self.queue_table = self.card_queue.table
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.queue_table.setShowGrid(False)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.horizontalHeader().setHighlightSections(False)
        
        column_stretch_modes = {
            0: QHeaderView.ResizeMode.ResizeToContents,
            1: QHeaderView.ResizeMode.Stretch,
            2: QHeaderView.ResizeMode.Stretch,
            3: QHeaderView.ResizeMode.ResizeToContents,
            4: QHeaderView.ResizeMode.ResizeToContents,
            5: QHeaderView.ResizeMode.ResizeToContents
        }
        for col, mode in column_stretch_modes.items():
            self.queue_table.horizontalHeader().setSectionResizeMode(col, mode)
        
        self.queue_table.setMinimumHeight(200)
        
        self.card_queue.setup_empty_state(
            title=self.i18n.get("music.queue.empty"),
            desc=self.i18n.get("music.queue.empty_desc"),
            icon_name="illustration_music.svg",
            button_text="",
            on_button_clicked=lambda: None
        )
        if hasattr(self.card_queue, "btn_empty_action") and self.card_queue.btn_empty_action:
            self.card_queue.btn_empty_action.setVisible(False)
            
        self.col2_layout.addWidget(self.card_queue, stretch=1)

    def _create_table_item(self, text: str, alignment: Qt.AlignmentFlag = None, color: Qt.GlobalColor = None) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if alignment is not None:
            item.setTextAlignment(alignment)
        if color is not None:
            item.setForeground(color)
        return item

    def _create_delete_button(self, index: int) -> QWidget:
        btn_delete = QPushButton()
        btn_delete.setProperty("role", "btn_ghost")
        btn_delete.setIcon(get_icon_colored("trash.svg", COLOR_RED, 14))
        btn_delete.setIconSize(QSize(14, 14))
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setToolTip(self.i18n.get("music.queue.remove_tooltip"))
        btn_delete.setFixedSize(QSize(26, 26))
        btn_delete.clicked.connect(lambda *args, idx=index: self.remove_queue_item_requested.emit(idx))
        
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.addWidget(btn_delete)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return cell_widget

    def update_queue(self, queue_items: list[dict]):
        new_urls = [song.get("url") for song in queue_items]
        if self._current_queue_urls == new_urls:
            return
        self._current_queue_urls = new_urls
        
        if hasattr(self.card_queue, "lbl_title") and self.card_queue.lbl_title:
            title_base = self.i18n.get("music.queue.title")
            self.card_queue.lbl_title.setText(f"{title_base} ({len(queue_items)})")
        
        self.card_queue.set_empty(len(queue_items) == 0)
        
        if not queue_items:
            self.queue_table.setRowCount(0)
            return
            
        self.queue_table.setRowCount(len(queue_items))
        
        for idx, song in enumerate(queue_items):
            self.queue_table.setItem(idx, 0, self._create_table_item(f"{idx + 1}", Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.gray))
            
            title_text = song.get("title", self.i18n.get("music.player.unknown_song"))
            self.queue_table.setItem(idx, 1, self._create_table_item(title_text))
            
            artist_text = song.get("artist", "-")
            self.queue_table.setItem(idx, 2, self._create_table_item(artist_text))
            
            requester = song.get("requester", "")
            requester_text = f"@{requester}" if requester else "-"
            req_color = Qt.GlobalColor.green if requester else None
            self.queue_table.setItem(idx, 3, self._create_table_item(requester_text, color=req_color))
            
            duration = song.get("duration", "-")
            self.queue_table.setItem(idx, 4, self._create_table_item(duration, Qt.AlignmentFlag.AlignCenter))
            self.queue_table.setCellWidget(idx, 5, self._create_delete_button(idx))

    def set_auth_state(self, connected: bool, label_key: str = ""):
        provider = self.combo_provider.currentData()
        is_youtube = (provider == "youtube")

        if is_youtube:
            self.lbl_provider_name.setText("YouTube")
            self.icon_music.setPixmap(get_pixmap("youtube.svg", 48))
            translated_label = self.i18n.get("music.status.youtube_active")
            self.lbl_auth_status.setText(f"{self.i18n.get('common.status.active')}: {translated_label}")
        else:
            self.lbl_provider_name.setText(self.i18n.get("music.provider.name"))
            self.icon_music.setPixmap(get_pixmap_colored("spotify.svg", COLOR_GREEN, 48))
            if connected:
                translated_label = self.i18n.get(label_key) or label_key
                self.lbl_auth_status.setText(f"{self.i18n.get('common.status.active')}: {translated_label}")
            else:
                self.lbl_auth_status.setText(self.i18n.get("common.status.disconnected"))

        show_spotify_connect = (not is_youtube and not connected)
        show_spotify_disconnect = (not is_youtube and connected)
        enable_commands = (is_youtube or connected)
        show_player = (is_youtube or connected)
        show_queue = is_youtube
        show_settings = is_youtube

        self.btn_connect.setVisible(show_spotify_connect)
        self.btn_connect.setEnabled(show_spotify_connect)
        self.btn_disconnect.setVisible(show_spotify_disconnect)
        self.card_cmds.setEnabled(enable_commands)
        self.card_player.setVisible(show_player)
        self.card_queue.setVisible(show_queue)
        
        self.card_settings.setVisible(show_settings)
        self.row_vol.setVisible(show_settings)
        self.row_auto_resume.setVisible(show_settings)
        
        self.card_overlay_url.setVisible(show_player)

    def _copy_music_overlay_url(self):
        theme = self.combo_music_theme.currentData() or "glass"
        url = self._music_overlay_url
        sep = "&" if "?" in url else "?"
        url += f"{sep}theme={theme}"
        
        QApplication.clipboard().setText(url)
        original = self.btn_copy_music_url.text()
        self.btn_copy_music_url.setText(self.i18n.get("rewards.obs.copied"))
        self.btn_copy_music_url.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_copy_btn(original))

    def _reset_copy_btn(self, original_text: str):
        self.btn_copy_music_url.setText(original_text)
        self.btn_copy_music_url.setEnabled(True)

    def update_current_song(self, song_data: dict | None):
        if song_data:
            title = song_data.get("title", "")
            artist = song_data.get("artist", "")
            is_playing = song_data.get("is_playing", False)
        else:
            title = self.i18n.get("music.player.paused_title")
            artist = self.i18n.get("music.player.paused_desc")
            is_playing = False

        if self._cached_song_state == (title, artist, is_playing):
            return
            
        self._cached_song_state = (title, artist, is_playing)
        self.lbl_song_title.setText(title)
        self.lbl_song_artist.setText(artist)
        
        icon_name = "player-pause.svg" if is_playing else "player-play.svg"
        self.btn_play_pause.setIcon(get_icon_colored(icon_name, COLOR_NEUTRAL_200, 18))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        direction = QBoxLayout.Direction.TopToBottom if width < 900 else QBoxLayout.Direction.LeftToRight
        
        if direction != self._last_direction:
            self._last_direction = direction
            if hasattr(self, 'columns_layout'):
                self.columns_layout.setDirection(direction)
