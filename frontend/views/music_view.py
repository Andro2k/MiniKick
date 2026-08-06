# frontend\views\music_view.py

from PySide6.QtWidgets import QBoxLayout, QWidget, QVBoxLayout, QTabWidget, QSizePolicy
from PySide6.QtCore import Qt, Signal
from frontend.widgets import BaseView, ModernScrollArea
from frontend.components.music import (
    MusicStatsPanel,
    MusicPlayerSettingsPanel,
    MusicCommandsPanel,
    MusicQueuePanel,
    MusicSettingsPanel
)

class MusicView(BaseView):
    command_toggled = Signal(str, bool)
    volume_changed = Signal(int)
    remove_queue_item_requested = Signal(int)
    play_pause_requested = Signal()
    skip_requested = Signal()
    youtube_auto_resume_toggled = Signal(bool)
    max_user_songs_changed = Signal(int)
    user_cooldown_changed = Signal(int)
    max_queue_size_changed = Signal(int)
    max_song_duration_changed = Signal(int)
    service_toggled = Signal(bool)
    move_queue_item_requested = Signal(int, int)
    view_shown = Signal()

    def __init__(self, i18n, music_overlay_url: str = ""):
        super().__init__(i18n=i18n, title_key="music.header.title", subtitle_key="music.header.subtitle")
        self._music_overlay_url = music_overlay_url
        self._last_direction = None
        self._setup_ui()
        self._connect_internal_signals()

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def _setup_ui(self):
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(16)

        self.stats_panel = MusicStatsPanel(self.i18n)
        self.body_layout.addWidget(self.stats_panel)

        self.columns_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        self.columns_layout.setSpacing(16)

        col1 = QWidget()
        self.col1_layout = QVBoxLayout(col1)
        self.col1_layout.setContentsMargins(0, 0, 0, 0)
        self.col1_layout.setSpacing(0)
        self.col1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.player_panel = MusicPlayerSettingsPanel(self.i18n, music_overlay_url=self._music_overlay_url)
        self.commands_panel = MusicCommandsPanel(self.i18n)
        self.settings_panel = MusicSettingsPanel(self.i18n)
        self.queue_panel = MusicQueuePanel(self.i18n)

        self.tabs.addTab(ModernScrollArea(self.player_panel), self.i18n.get("music.tabs.player"))
        self.tabs.addTab(ModernScrollArea(self.commands_panel), self.i18n.get("music.tabs.commands"))
        self.tabs.addTab(ModernScrollArea(self.settings_panel), self.i18n.get("music.tabs.settings"))

        self.col1_layout.addWidget(self.tabs)

        col2 = QWidget()
        self.col2_layout = QVBoxLayout(col2)
        self.col2_layout.setContentsMargins(0, 0, 0, 0)
        self.col2_layout.setSpacing(0)
        self.col2_layout.addWidget(self.queue_panel)

        self.columns_layout.addWidget(col1, stretch=3)
        self.columns_layout.addWidget(col2, stretch=4)

        self.body_layout.addLayout(self.columns_layout)
        self.main_layout.addWidget(self.body_container)

    def _connect_internal_signals(self):
        self.stats_panel.service_toggled.connect(self._on_service_toggled)

        self.player_panel.volume_changed.connect(self.volume_changed.emit)
        self.player_panel.play_pause_requested.connect(self.play_pause_requested.emit)
        self.player_panel.skip_requested.connect(self.skip_requested.emit)

        self.settings_panel.youtube_auto_resume_toggled.connect(self.youtube_auto_resume_toggled.emit)
        self.settings_panel.max_user_songs_changed.connect(self.max_user_songs_changed.emit)
        self.settings_panel.user_cooldown_changed.connect(self.user_cooldown_changed.emit)
        self.settings_panel.max_queue_size_changed.connect(self.max_queue_size_changed.emit)
        self.settings_panel.max_song_duration_changed.connect(self.max_song_duration_changed.emit)

        self.commands_panel.command_toggled.connect(self.command_toggled.emit)

        self.queue_panel.remove_queue_item_requested.connect(self.remove_queue_item_requested.emit)
        self.queue_panel.move_queue_item_requested.connect(self.move_queue_item_requested.emit)
        self.queue_panel.queue_updated.connect(self.stats_panel.set_stats)

    def _on_service_toggled(self, checked: bool):
        self.commands_panel.set_enabled_state(checked)
        self.service_toggled.emit(checked)

    @property
    def slider_vol(self):
        return self.player_panel.slider_vol

    @property
    def lbl_vol_perc(self):
        return self.player_panel.lbl_vol_perc

    @property
    def sw_auto_resume(self):
        return self.settings_panel.sw_auto_resume

    @property
    def sw_sr(self):
        return self.commands_panel.sw_sr

    @property
    def sw_skip(self):
        return self.commands_panel.sw_skip

    @property
    def sw_song(self):
        return self.commands_panel.sw_song

    @property
    def sw_pause(self):
        return self.commands_panel.sw_pause

    @property
    def sw_resume(self):
        return self.commands_panel.sw_resume

    @property
    def sw_playlist(self):
        return self.commands_panel.sw_playlist

    @property
    def sw_volume(self):
        return self.commands_panel.sw_volume

    @property
    def card_queue(self):
        return self.queue_panel.card_queue

    @property
    def queue_table(self):
        return self.queue_panel.queue_table

    def set_service_state(self, enabled: bool):
        self.stats_panel.set_service_state(enabled)
        self.commands_panel.set_enabled_state(enabled)

    def update_queue(self, queue_items: list[dict]):
        self.queue_panel.update_queue(queue_items)

    def set_auth_state(self, connected: bool, label_key: str = ""):
        self.player_panel.set_auth_state(connected, label_key)
        self.commands_panel.set_enabled_state(True)
        self.queue_panel.card_queue.setVisible(True)

    def update_current_song(self, song_data: dict | None):
        self.player_panel.update_current_song(song_data)

    def set_rate_limit_values(self, max_user_songs: int, user_cooldown: int, max_queue_size: int, max_song_duration: int):
        self.settings_panel.set_rate_limit_values(max_user_songs, user_cooldown, max_queue_size, max_song_duration)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        if hasattr(self, 'stats_panel'):
            self.stats_panel.relayout(width)

        direction = QBoxLayout.Direction.TopToBottom if width < 900 else QBoxLayout.Direction.LeftToRight
        if direction != self._last_direction:
            self._last_direction = direction
            if hasattr(self, 'columns_layout'):
                self.columns_layout.setDirection(direction)

