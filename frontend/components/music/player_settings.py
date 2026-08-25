# frontend\components\music\player_settings.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QProgressBar
from PySide6.QtCore import Signal, Qt, QSize, QTimer
from frontend.common.theme import COLOR_NEUTRAL_400, COLOR_RED
from frontend.common import get_icon_colored, get_pixmap
from frontend.widgets import ModernCard, ModernButton, SliderRow, NoWheelComboBox, NoWheelSlider

class MusicPlayerSettingsPanel(QWidget):
    volume_changed = Signal(int)
    play_pause_requested = Signal()
    skip_requested = Signal()

    def __init__(self, i18n, music_overlay_url: str = "", parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._music_overlay_url = music_overlay_url
        self._cached_song_state = None
        self._cached_auth_state = None
        self._pending_volume = 100

        self._current_progress_ms = 0
        self._duration_ms = 0
        self._is_playing = False

        self._volume_timer = QTimer(self)
        self._volume_timer.setSingleShot(True)
        self._volume_timer.setInterval(200)
        self._volume_timer.timeout.connect(self._emit_volume)

        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(1000)
        self._progress_timer.timeout.connect(self._on_progress_tick)

        self._setup_ui()

    def _setup_ui(self):
        self.panel_layout = QVBoxLayout(self)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(16)
        self.panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._setup_status_card()
        self._setup_now_playing_card()
        self._setup_volume_card()
        self._setup_overlay_url_card()

    def _setup_status_card(self):
        card = ModernCard(parent=self, margin=12, spacing=8)

        status_layout = QHBoxLayout()
        
        self.lbl_auth_status = QLabel(self.i18n.get("music.status.youtube_active"))
        self.lbl_auth_status.setProperty("role", "h3")
        
        provider_info = QVBoxLayout()
        provider_info.addWidget(self.lbl_auth_status)

        status_layout.addLayout(provider_info, stretch=1)
        card.addLayout(status_layout)
        self.panel_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

    def _setup_now_playing_card(self):
        self.card_player = ModernCard(parent=self, margin=12, spacing=8, orientation="vertical")
        self.card_player.setVisible(True)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        self.icon_music = QLabel()
        self.icon_music.setPixmap(get_pixmap("youtube.svg", 56))
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.lbl_song_title = QLabel(self.i18n.get("music.player.not_playing"))
        self.lbl_song_title.setProperty("role", "h3")
        self.lbl_song_title.setWordWrap(True)
        
        self.lbl_song_artist = QLabel("-")
        self.lbl_song_artist.setProperty("role", "body")
        self.lbl_song_artist.setWordWrap(True)

        self.lbl_song_requester = QLabel("-")
        self.lbl_song_requester.setProperty("role", "caption")
        self.lbl_song_requester.setWordWrap(True)

        info_layout.addWidget(self.lbl_song_title)
        info_layout.addWidget(self.lbl_song_artist)
        info_layout.addWidget(self.lbl_song_requester)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)
        
        self.btn_play_pause = ModernButton("", role="action_neutral_border")
        self.btn_play_pause.setFixedSize(36, 36)
        self.btn_play_pause.setIcon(get_icon_colored("player-play.svg", COLOR_NEUTRAL_400, 18))
        self.btn_play_pause.setIconSize(QSize(18, 18))
        self.btn_play_pause.clicked.connect(self.play_pause_requested.emit)
        
        self.btn_skip = ModernButton("", role="action_neutral_border")
        self.btn_skip.setFixedSize(36, 36)
        self.btn_skip.setIcon(get_icon_colored("player-skip.svg", COLOR_NEUTRAL_400, 18))
        self.btn_skip.setIconSize(QSize(18, 18))
        self.btn_skip.clicked.connect(self.skip_requested.emit)
        
        controls_layout.addWidget(self.btn_play_pause)
        controls_layout.addWidget(self.btn_skip)

        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        top_layout.addWidget(self.icon_music, alignment=Qt.AlignmentFlag.AlignTop)
        top_layout.addLayout(info_layout, stretch=1)
        top_layout.addLayout(controls_layout)

        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)

        time_layout = QHBoxLayout()
        self.lbl_time_elapsed = QLabel("00:00")
        self.lbl_time_elapsed.setProperty("role", "caption")

        self.lbl_time_total = QLabel("00:00")
        self.lbl_time_total.setProperty("role", "caption")

        time_layout.addWidget(self.lbl_time_elapsed)
        time_layout.addStretch()
        time_layout.addWidget(self.lbl_time_total)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(time_layout)

        self.card_player.addLayout(top_layout)
        self.card_player.addLayout(progress_layout)
        self.panel_layout.addWidget(self.card_player, alignment=Qt.AlignmentFlag.AlignTop)

    def _setup_volume_card(self):
        self.card_volume = ModernCard(parent=self, margin=12, spacing=8)

        self.slider_vol = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
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
        self.slider_vol.valueChanged.connect(self._on_volume_slider_changed)
        self.card_volume.addWidget(self.row_vol)
        self.panel_layout.addWidget(self.card_volume, alignment=Qt.AlignmentFlag.AlignTop)

    def _on_volume_slider_changed(self, val):
        self.lbl_vol_perc.setText(f"{val}%")
        self._pending_volume = val
        self._volume_timer.start()

    def _emit_volume(self):
        self.volume_changed.emit(self._pending_volume)

    def _setup_overlay_url_card(self):
        self.card_overlay_url = ModernCard(parent=self, margin=12, spacing=8)

        url_info = QVBoxLayout()
        lbl_title = QLabel(self.i18n.get("music.overlay.url_title"))
        lbl_title.setProperty("role", "h3")
        lbl_desc = QLabel(self.i18n.get("music.overlay.url_desc"))
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        url_info.addWidget(lbl_title)
        url_info.addWidget(lbl_desc)

        layout_setting_row = QHBoxLayout()
        lbl_layout = QLabel(self.i18n.get("music.overlay.layout_label"), parent=self)
        lbl_layout.setProperty("role", "body")
        self.combo_music_layout = NoWheelComboBox(self)
        self.combo_music_layout.addItem(self.i18n.get("music.overlay.layout_banner"), "banner")
        self.combo_music_layout.addItem(self.i18n.get("music.overlay.layout_pill"), "pill")
        self.combo_music_layout.addItem(self.i18n.get("music.overlay.layout_floating"), "floating")
        self.combo_music_layout.addItem(self.i18n.get("music.overlay.layout_compact"), "compact")
        self.combo_music_layout.addItem(self.i18n.get("music.overlay.layout_standard"), "standard")

        layout_setting_row.addWidget(lbl_layout)
        layout_setting_row.addWidget(self.combo_music_layout)

        theme_layout = QHBoxLayout()
        lbl_theme = QLabel(self.i18n.get("music.overlay.theme_label"), parent=self)
        lbl_theme.setProperty("role", "body")
        self.combo_music_theme = NoWheelComboBox(self)
        self.combo_music_theme.addItem(self.i18n.get("music.overlay.theme_dynamic"), "dynamic")
        self.combo_music_theme.addItem(self.i18n.get("music.overlay.theme_glass"), "glass")
        self.combo_music_theme.addItem(self.i18n.get("music.overlay.theme_minimal"), "minimal")
        self.combo_music_theme.addItem(self.i18n.get("music.overlay.theme_neon"), "neon")
        self.combo_music_theme.addItem(self.i18n.get("music.overlay.theme_cyber"), "cyber")
        self.combo_music_theme.addItem(self.i18n.get("music.overlay.theme_card"), "card")
        
        theme_layout.addWidget(lbl_theme)
        theme_layout.addWidget(self.combo_music_theme)

        self.btn_copy_music_url = ModernButton(
            self.i18n.get("common.buttons.copy"),
            role="action_neutral_border"
        )
        self.btn_copy_music_url.clicked.connect(self._copy_music_overlay_url)

        self.card_overlay_url.addLayout(url_info)
        self.card_overlay_url.addLayout(layout_setting_row)
        self.card_overlay_url.addLayout(theme_layout)
        self.card_overlay_url.addWidget(self.btn_copy_music_url)
        self.panel_layout.addWidget(self.card_overlay_url, alignment=Qt.AlignmentFlag.AlignTop)

    def _copy_music_overlay_url(self):
        layout = self.combo_music_layout.currentData() or "standard"
        theme = self.combo_music_theme.currentData() or "glass"
        url = self._music_overlay_url
        if url:
            sep = "&" if "?" in url else "?"
            url += f"{sep}layout={layout}&theme={theme}"
            QApplication.clipboard().setText(url)
            original = self.btn_copy_music_url.text()
            self.btn_copy_music_url.setText(self.i18n.get("rewards.obs.copied"))
            self.btn_copy_music_url.setEnabled(False)
            QTimer.singleShot(2000, lambda: self._reset_copy_btn(original))

    def _reset_copy_btn(self, original_text: str):
        self.btn_copy_music_url.setText(original_text)
        self.btn_copy_music_url.setEnabled(True)

    def set_auth_state(self, connected: bool, label_key: str = ""):
        self._cached_auth_state = (connected, label_key)
        self.lbl_auth_status.setText(self.i18n.get("music.status.youtube_active"))

    def _format_time(self, ms: int) -> str:
        if ms <= 0:
            return "00:00"
        seconds = int(ms // 1000)
        minutes = seconds // 60
        sec_rem = seconds % 60
        if minutes >= 60:
            hours = minutes // 60
            min_rem = minutes % 60
            return f"{hours:02d}:{min_rem:02d}:{sec_rem:02d}"
        return f"{minutes:02d}:{sec_rem:02d}"

    def _on_progress_tick(self):
        if self._is_playing and self._duration_ms > 0:
            self._current_progress_ms = min(self._current_progress_ms + 1000, self._duration_ms)
            self._update_progress_ui()

    def _update_progress_ui(self):
        if self._duration_ms > 0:
            percentage = int((self._current_progress_ms / self._duration_ms) * 100)
            self.progress_bar.setValue(min(100, max(0, percentage)))
            self.lbl_time_elapsed.setText(self._format_time(self._current_progress_ms))
            self.lbl_time_total.setText(self._format_time(self._duration_ms))
        else:
            self.progress_bar.setValue(0)
            self.lbl_time_elapsed.setText("00:00")
            self.lbl_time_total.setText("00:00")

    def update_current_song(self, song_data: dict | None):
        self._cached_song_state = song_data
        if not song_data:
            self.lbl_song_title.setText(self.i18n.get("music.player.not_playing"))
            self.lbl_song_artist.setText("-")
            self.lbl_song_requester.setText("-")
            self.btn_play_pause.setIcon(get_icon_colored("player-play.svg", COLOR_NEUTRAL_400, 18))
            self._is_playing = False
            self._duration_ms = 0
            self._current_progress_ms = 0
            self._progress_timer.stop()
            self._update_progress_ui()
            return

        title = song_data.get("title", self.i18n.get("music.player.unknown_song"))
        artist = song_data.get("artist", "-")
        requester = song_data.get("requester", "")
        is_playing = song_data.get("is_playing", False)
        duration = song_data.get("duration", 0) or 0
        progress = song_data.get("progress", 0) or 0

        self.lbl_song_title.setText(title)
        self.lbl_song_artist.setText(artist)

        if requester:
            platform = (song_data.get("platform") or "kick").lower()
            if platform == "twitch":
                color_hex = "#A970FF"
            elif platform == "youtube":
                color_hex = COLOR_RED
            else:
                color_hex = "#53FC18"
            user_styled = f"<span style='color:{color_hex}; font-weight:600;'>@{requester}</span>"
            req_text = self.i18n.get("music.player.requested_by").replace("{user}", user_styled)
        else:
            req_text = self.i18n.get("music.player.requested_by_streamer")
        self.lbl_song_requester.setText(req_text)

        icon_name = "player-pause.svg" if is_playing else "player-play.svg"
        self.btn_play_pause.setIcon(get_icon_colored(icon_name, COLOR_NEUTRAL_400, 18))

        self._duration_ms = duration
        self._current_progress_ms = progress
        self._is_playing = is_playing

        self._update_progress_ui()

        if is_playing:
            if not self._progress_timer.isActive():
                self._progress_timer.start()
        else:
            self._progress_timer.stop()

