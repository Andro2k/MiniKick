# frontend\components\music\player_settings.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication
from PySide6.QtCore import Signal, Qt, QSize, QTimer
from frontend.common.theme import COLOR_NEUTRAL_200
from frontend.common.utils import get_icon_colored, NoWheelComboBox, NoWheelSlider, get_pixmap
from frontend.widgets import ModernCard, ModernButton, SettingRow, SliderRow

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

        self._setup_status_card()
        self._setup_now_playing_card()
        self._setup_volume_card()
        self._setup_overlay_url_card()

    def _setup_status_card(self):
        card = ModernCard(parent=self, margin=12, spacing=8)

        status_layout = QHBoxLayout()
        self.lbl_provider_name = QLabel("YouTube Music")
        self.lbl_provider_name.setProperty("role", "h3")
        
        self.lbl_auth_status = QLabel(self.i18n.get("music.status.youtube_active"))
        self.lbl_auth_status.setProperty("role", "body")
        
        provider_info = QVBoxLayout()
        provider_info.addWidget(self.lbl_provider_name)
        provider_info.addWidget(self.lbl_auth_status)

        status_layout.addLayout(provider_info, stretch=1)
        card.addLayout(status_layout)
        self.panel_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

    def _setup_now_playing_card(self):
        self.card_player = ModernCard(parent=self, margin=12, spacing=8, orientation="horizontal")
        self.card_player.setVisible(True)

        self.icon_music = QLabel()
        self.icon_music.setPixmap(get_pixmap("youtube.svg", 48))
        
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
            self.btn_copy_music_url.setText(self.i18n.get("common.buttons.copy") + " ✓")
            self.btn_copy_music_url.setEnabled(False)
            QTimer.singleShot(2000, lambda: self._reset_copy_btn(original))

    def _reset_copy_btn(self, original_text: str):
        self.btn_copy_music_url.setText(original_text)
        self.btn_copy_music_url.setEnabled(True)

    def set_auth_state(self, connected: bool, label_key: str = ""):
        self._cached_auth_state = (connected, label_key)
        self.lbl_auth_status.setText(self.i18n.get("music.status.youtube_active"))

    def update_current_song(self, song_data: dict | None):
        self._cached_song_state = song_data
        if not song_data:
            self.lbl_song_title.setText(self.i18n.get("music.player.not_playing"))
            self.lbl_song_artist.setText("-")
            self.btn_play_pause.setIcon(get_icon_colored("player-play.svg", COLOR_NEUTRAL_200, 18))
            return

        title = song_data.get("title", self.i18n.get("music.player.unknown_song"))
        artist = song_data.get("artist", "-")
        is_playing = song_data.get("is_playing", False)

        self.lbl_song_title.setText(title)
        self.lbl_song_artist.setText(artist)

        icon_name = "player-pause.svg" if is_playing else "player-play.svg"
        self.btn_play_pause.setIcon(get_icon_colored(icon_name, COLOR_NEUTRAL_200, 18))
