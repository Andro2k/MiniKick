# frontend\components\music\player_settings.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication
from PySide6.QtCore import Signal, Qt, QSize, QTimer
from frontend.common.theme import COLOR_GREEN, COLOR_NEUTRAL_200
from frontend.common.utils import get_icon_colored, NoWheelComboBox, NoWheelSlider, get_pixmap, get_pixmap_colored
from frontend.widgets import ModernCard, ModernButton, ModernSwitch, SettingRow, SliderRow

class MusicPlayerSettingsPanel(QWidget):
    connect_requested = Signal()
    disconnect_requested = Signal()
    provider_changed = Signal(str)
    volume_changed = Signal(int)
    play_pause_requested = Signal()
    skip_requested = Signal()
    youtube_auto_resume_toggled = Signal(bool)

    def __init__(self, i18n, music_overlay_url: str = "", parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._music_overlay_url = music_overlay_url
        self._cached_song_state = None
        self._cached_auth_state = None
        self._pending_volume = 100

        self._volume_timer = QTimer(self)
        self._volume_timer.setSingleShot(True)
        self._volume_timer.setInterval(200)
        self._volume_timer.timeout.connect(self._emit_volume)

        self._setup_ui()

    def _setup_ui(self):
        self.panel_layout = QVBoxLayout(self)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(16)
        self.panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._setup_provider_selection_card()
        self._setup_auth_card()
        self._setup_now_playing_card()
        self._setup_settings_card()
        self._setup_overlay_url_card()

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
        self.panel_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

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
        self.panel_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

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
        self.panel_layout.addWidget(self.card_player, alignment=Qt.AlignmentFlag.AlignTop)

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

        self.panel_layout.addWidget(self.card_settings, alignment=Qt.AlignmentFlag.AlignTop)

    def _on_volume_slider_changed(self, val):
        self.lbl_vol_perc.setText(f"{val}%")
        self._pending_volume = val
        self._volume_timer.start()

    def _emit_volume(self):
        self.volume_changed.emit(self._pending_volume)

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
        self.panel_layout.addWidget(self.card_overlay_url, alignment=Qt.AlignmentFlag.AlignTop)

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

    def set_auth_state(self, connected: bool, label_key: str = ""):
        provider = self.combo_provider.currentData()
        
        state_key = (provider, connected, label_key)
        if self._cached_auth_state == state_key:
            return
        self._cached_auth_state = state_key

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
        show_player = (is_youtube or connected)
        show_settings = is_youtube

        self.btn_connect.setVisible(show_spotify_connect)
        self.btn_connect.setEnabled(show_spotify_connect)
        self.btn_disconnect.setVisible(show_spotify_disconnect)
        self.card_player.setVisible(show_player)
        
        self.card_settings.setVisible(show_settings)
        self.row_vol.setVisible(show_settings)
        self.row_auto_resume.setVisible(show_settings)
        
        self.card_overlay_url.setVisible(show_player)

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
