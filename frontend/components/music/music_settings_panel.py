# frontend\components\music\music_settings_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from frontend.widgets import ModernCard, ModernSwitch, SettingRow, SliderRow, NoWheelSlider

class MusicSettingsPanel(QWidget):
    youtube_auto_resume_toggled = Signal(bool)
    max_user_songs_changed = Signal(int)
    user_cooldown_changed = Signal(int)
    max_queue_size_changed = Signal(int)
    max_song_duration_changed = Signal(int)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        self.panel_layout = QVBoxLayout(self)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(16)
        self.panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._setup_settings_card()

    def _setup_settings_card(self):
        self.card_settings = ModernCard(margin=12, spacing=8)

        self.sw_auto_resume = ModernSwitch()
        self.sw_auto_resume.toggled.connect(self.youtube_auto_resume_toggled.emit)
        self.row_auto_resume = SettingRow(
            icon_name="refresh.svg",
            title_text=self.i18n.get("music.youtube.auto_resume_title"),
            desc_text=self.i18n.get("music.youtube.auto_resume_desc"),
            right_widget=self.sw_auto_resume
        )
        self.card_settings.addWidget(self.row_auto_resume)

        self.slider_max_user_songs = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_max_user_songs.setRange(1, 10)
        self.slider_max_user_songs.setValue(2)
        self.lbl_max_user_songs = QLabel("2")
        self.lbl_max_user_songs.setProperty("role", "body")
        self.row_max_user_songs = SliderRow(
            icon_name="user.svg",
            title_text=self.i18n.get("music.youtube.max_user_songs_title"),
            desc_text=self.i18n.get("music.youtube.max_user_songs_desc"),
            slider_widget=self.slider_max_user_songs,
            value_label=self.lbl_max_user_songs
        )
        self.slider_max_user_songs.valueChanged.connect(self._on_max_user_songs_changed)
        self.card_settings.addWidget(self.row_max_user_songs)

        self.slider_user_cooldown = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_user_cooldown.setRange(0, 300)
        self.slider_user_cooldown.setValue(30)
        self.lbl_user_cooldown = QLabel("30s")
        self.lbl_user_cooldown.setProperty("role", "body")
        self.row_user_cooldown = SliderRow(
            icon_name="clock.svg",
            title_text=self.i18n.get("music.youtube.user_cooldown_title"),
            desc_text=self.i18n.get("music.youtube.user_cooldown_desc"),
            slider_widget=self.slider_user_cooldown,
            value_label=self.lbl_user_cooldown
        )
        self.slider_user_cooldown.valueChanged.connect(self._on_user_cooldown_changed)
        self.card_settings.addWidget(self.row_user_cooldown)

        self.slider_max_queue = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_max_queue.setRange(5, 100)
        self.slider_max_queue.setValue(30)
        self.lbl_max_queue = QLabel("30")
        self.lbl_max_queue.setProperty("role", "body")
        self.row_max_queue = SliderRow(
            icon_name="list.svg",
            title_text=self.i18n.get("music.youtube.max_queue_size_title"),
            desc_text=self.i18n.get("music.youtube.max_queue_size_desc"),
            slider_widget=self.slider_max_queue,
            value_label=self.lbl_max_queue
        )
        self.slider_max_queue.valueChanged.connect(self._on_max_queue_changed)
        self.card_settings.addWidget(self.row_max_queue)

        self.slider_max_duration = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_max_duration.setRange(1, 30)
        self.slider_max_duration.setValue(10)
        self.lbl_max_duration = QLabel("10m")
        self.lbl_max_duration.setProperty("role", "body")
        self.row_max_duration = SliderRow(
            icon_name="stopwatch.svg",
            title_text=self.i18n.get("music.youtube.max_song_duration_title"),
            desc_text=self.i18n.get("music.youtube.max_song_duration_desc"),
            slider_widget=self.slider_max_duration,
            value_label=self.lbl_max_duration
        )
        self.slider_max_duration.valueChanged.connect(self._on_max_duration_changed)
        self.card_settings.addWidget(self.row_max_duration)

        self.panel_layout.addWidget(self.card_settings, alignment=Qt.AlignmentFlag.AlignTop)

    def _on_max_user_songs_changed(self, val):
        self.lbl_max_user_songs.setText(str(val))
        self.max_user_songs_changed.emit(val)

    def _on_user_cooldown_changed(self, val):
        self.lbl_user_cooldown.setText(f"{val}s")
        self.user_cooldown_changed.emit(val)

    def _on_max_queue_changed(self, val):
        self.lbl_max_queue.setText(str(val))
        self.max_queue_size_changed.emit(val)

    def _on_max_duration_changed(self, val):
        self.lbl_max_duration.setText(f"{val}m")
        self.max_song_duration_changed.emit(val)

    def set_rate_limit_values(self, max_user_songs: int, user_cooldown: int, max_queue_size: int, max_song_duration: int):
        self.slider_max_user_songs.blockSignals(True)
        self.slider_max_user_songs.setValue(max_user_songs)
        self.slider_max_user_songs.blockSignals(False)
        self.lbl_max_user_songs.setText(str(max_user_songs))

        self.slider_user_cooldown.blockSignals(True)
        self.slider_user_cooldown.setValue(user_cooldown)
        self.slider_user_cooldown.blockSignals(False)
        self.lbl_user_cooldown.setText(f"{user_cooldown}s")

        self.slider_max_queue.blockSignals(True)
        self.slider_max_queue.setValue(max_queue_size)
        self.slider_max_queue.blockSignals(False)
        self.lbl_max_queue.setText(str(max_queue_size))

        self.slider_max_duration.blockSignals(True)
        self.slider_max_duration.setValue(max_song_duration)
        self.slider_max_duration.blockSignals(False)
        self.lbl_max_duration.setText(f"{max_song_duration}m")

