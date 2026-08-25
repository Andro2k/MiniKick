# frontend\views\chat_view.py

from frontend.components.chat import ChatDisplayPanel, ChatOverlaySettingsPanel, BotMutePanel, ChatTtsSettingsPanel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QTabWidget, QBoxLayout
from PySide6.QtCore import Signal
from frontend.widgets import BaseView, ModernCard, ModernScrollArea

class ChatView(BaseView):
    volume_changed = Signal(int)
    speed_changed = Signal(int)
    voice_changed = Signal(str)
    provider_changed = Signal(str)
    settings_changed = Signal()
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)
    word_add_requested = Signal(str)
    word_remove_requested = Signal(str)
    language_filter_changed = Signal(str)
    voice_test_requested = Signal(str)

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="chat.header.title", subtitle_key="chat.header.subtitle", parent=parent)
        self._last_body_dir = None
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        self.body_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.body_layout.setSpacing(16)

        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(320)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tts_settings_panel = ChatTtsSettingsPanel(self.i18n)
        self.bot_panel = BotMutePanel(self.i18n)
        self.overlay_settings_panel = ChatOverlaySettingsPanel(self.i18n)
        self.chat_display_panel = ChatDisplayPanel(self.i18n)

        self.chk_command = self.tts_settings_panel.chk_command
        self.txt_command = self.tts_settings_panel.txt_command
        self.chat_display = self.chat_display_panel.chat_display
        self.tabs.addTab(ModernScrollArea(self.tts_settings_panel), self.i18n.get("chat.tabs.settings"))
        
        bot_card = ModernCard()
        bot_card.addWidget(self.bot_panel)
        self.tabs.addTab(bot_card, self.i18n.get("chat.tabs.muted"))
        
        self.tabs.addTab(ModernScrollArea(self.overlay_settings_panel), self.i18n.get("chat.tabs.overlay"))

        self.left_container = QWidget()
        left_layout = QVBoxLayout(self.left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.tabs)
        self.left_container.setMinimumWidth(320)
        self.left_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.chat_display_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.body_layout.addWidget(self.left_container, stretch=4)
        self.body_layout.addWidget(self.chat_display_panel, stretch=5)
        
        self.main_layout.addLayout(self.body_layout, stretch=1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        direction = QBoxLayout.Direction.TopToBottom if width < 1080 else QBoxLayout.Direction.LeftToRight
        if self._last_body_dir != direction:
            self._last_body_dir = direction
            self.body_layout.setDirection(direction)
        self.body_layout.setStretch(0, 1)
        self.body_layout.setStretch(1, 1)

    def _connect_internal_signals(self):
        self.tts_settings_panel.provider_changed.connect(self.provider_changed.emit)
        self.tts_settings_panel.volume_changed.connect(self.volume_changed.emit)
        self.tts_settings_panel.language_filter_changed.connect(self.language_filter_changed.emit)
        self.tts_settings_panel.speed_changed.connect(self.speed_changed.emit)
        self.tts_settings_panel.voice_changed.connect(self.voice_changed.emit)
        self.tts_settings_panel.settings_changed.connect(self.settings_changed.emit)
        self.tts_settings_panel.voice_test_requested.connect(self.voice_test_requested.emit)

        self.bot_panel.bot_add_requested.connect(self.bot_add_requested.emit)
        self.bot_panel.bot_remove_requested.connect(self.bot_remove_requested.emit)
        self.bot_panel.word_add_requested.connect(self.word_add_requested.emit)
        self.bot_panel.word_remove_requested.connect(self.word_remove_requested.emit)

        self.overlay_settings_panel.settings_changed.connect(self.settings_changed.emit)

    @property
    def tts_enabled(self) -> bool:
        return self.tts_settings_panel.chk_tts.isChecked()

    @tts_enabled.setter
    def tts_enabled(self, value: bool):
        self.tts_settings_panel.chk_tts.blockSignals(True)
        self.tts_settings_panel.chk_tts.setChecked(value)
        self.tts_settings_panel.chk_tts.blockSignals(False)

    @property
    def read_name_enabled(self) -> bool:
        return self.tts_settings_panel.chk_name.isChecked()

    @read_name_enabled.setter
    def read_name_enabled(self, value: bool):
        self.tts_settings_panel.chk_name.blockSignals(True)
        self.tts_settings_panel.chk_name.setChecked(value)
        self.tts_settings_panel.chk_name.blockSignals(False)

    @property
    def use_command_enabled(self) -> bool:
        return self.tts_settings_panel.chk_command.isChecked()

    @use_command_enabled.setter
    def use_command_enabled(self, value: bool):
        self.tts_settings_panel.chk_command.blockSignals(True)
        self.tts_settings_panel.chk_command.setChecked(value)
        self.tts_settings_panel.chk_command.blockSignals(False)

    @property
    def tts_command(self) -> str:
        return self.tts_settings_panel.txt_command.text().strip().lower()

    @tts_command.setter
    def tts_command(self, value: str):
        self.tts_settings_panel.txt_command.blockSignals(True)
        self.tts_settings_panel.txt_command.setText(value)
        self.tts_settings_panel.txt_command.blockSignals(False)

    @property
    def tts_provider(self) -> str:
        return self.tts_settings_panel.combo_provider.currentData() or "piper"

    @property
    def is_web_provider(self) -> bool:
        return self.tts_provider == "web"

    @property
    def tts_volume(self) -> int:
        return self.tts_settings_panel.slider_vol.value()

    @tts_volume.setter
    def tts_volume(self, value: int):
        self.tts_settings_panel.slider_vol.blockSignals(True)
        self.tts_settings_panel.slider_vol.setValue(value)
        self.tts_settings_panel.slider_vol.blockSignals(False)

    @property
    def tts_speed(self) -> int:
        return self.tts_settings_panel.slider_speed.value()

    @tts_speed.setter
    def tts_speed(self, value: int):
        self.tts_settings_panel.slider_speed.blockSignals(True)
        self.tts_settings_panel.slider_speed.setValue(value)
        self.tts_settings_panel.lbl_speed_perc.setText(f"{value}%")
        self.tts_settings_panel.slider_speed.blockSignals(False)

    @property
    def overlay_theme(self) -> str:
        return self.overlay_settings_panel.combo_overlay_theme.currentData() or "glass"

    @property
    def overlay_size(self) -> int:
        return self.overlay_settings_panel.spin_overlay_size.value()

    @property
    def overlay_fade(self) -> int:
        return self.overlay_settings_panel.spin_overlay_fade.value()

    @property
    def overlay_show_bots(self) -> bool:
        return self.overlay_settings_panel.sw_overlay_show_bots.isChecked()

    @property
    def overlay_show_time(self) -> bool:
        return self.overlay_settings_panel.sw_overlay_show_time.isChecked()

    @property
    def chat_overlay_url(self) -> str:
        return self.overlay_settings_panel.chat_overlay_url

    @chat_overlay_url.setter
    def chat_overlay_url(self, value: str):
        self.overlay_settings_panel.chat_overlay_url = value

    def set_settings_ui(self, enabled: bool, read_name: bool, use_command: bool, command: str,
                        is_web_provider: bool = False, volume: int = 100, role_voices: dict = None,
                        role_enabled: dict = None, provider: str = None, speed: int = 100):
        self.tts_settings_panel.set_settings_ui(
            enabled, read_name, use_command, command, is_web_provider, volume, role_voices, role_enabled, provider, speed
        )

    def set_overlay_settings_ui(self, theme: str, size: int, fade: int, show_bots: bool, show_time: bool):
        self.overlay_settings_panel.set_overlay_settings_ui(theme, size, fade, show_bots, show_time)

    def clear_bot_input(self):
        self.bot_panel.clear_input()

    def add_bot_tag(self, bot_name: str):
        self.bot_panel.add_bot_tag(bot_name)

    def clear_bots_list(self):
        self.bot_panel.clear_list()

    def clear_word_input(self):
        self.bot_panel.clear_word_input()

    def add_word_tag(self, word: str):
        self.bot_panel.add_word_tag(word)

    def clear_words_list(self):
        self.bot_panel.clear_words_list()

    def update_languages(self, langs: list[str], select_prefix: str = None):
        self.tts_settings_panel.update_languages(langs, select_prefix)

    def update_voices(self, voices: list[tuple[str, str]], select_id: str = None, role_voices: dict = None, all_voices: list[tuple[str, str]] = None):
        self.tts_settings_panel.update_voices(voices, select_id, role_voices, all_voices)

    def get_role_voices(self) -> dict:
        return self.tts_settings_panel.get_role_voices()

    def append_message(self, user: str, message: str, color: str, timestamp: str = "", is_html: bool = False, role: str = "", platform: str = "kick"):
        self.chat_display_panel.append_message(user, message, color, timestamp, is_html, role, platform=platform)

    def set_tts_command_configuration(self, use_command: bool, command_trigger: str):
        self.blockSignals(True)
        self.chk_command.blockSignals(True)
        self.txt_command.blockSignals(True)           
        self.chk_command.setChecked(use_command)
        self.txt_command.setText(command_trigger)            
        self.txt_command.setEnabled(use_command)
        self.chk_command.blockSignals(False)
        self.txt_command.blockSignals(False)
        self.blockSignals(False)

    def set_tts_enabled_state(self, enabled: bool):
        if hasattr(self.tts_settings_panel, 'chk_tts'):
            self.tts_settings_panel.chk_tts.blockSignals(True)
            self.tts_settings_panel.chk_tts.setChecked(enabled)
            self.tts_settings_panel.chk_tts.blockSignals(False)
