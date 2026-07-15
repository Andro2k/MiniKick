# frontend\views\chat_view.py

from frontend.components.chat.chat_display import ChatDisplayPanel
from frontend.components.chat.overlay_settings import ChatOverlaySettingsPanel
from frontend.components.chat.bot_mute import BotMutePanel
from frontend.components.chat.tts_settings import ChatTtsSettingsPanel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QTabWidget
from PySide6.QtCore import Signal
from frontend.widgets.base_view import BaseView
from frontend.widgets.flow_layout import FlowLayout
from frontend.widgets.blocks import ModernCard, ModernScrollArea


class ChatView(BaseView):
    volume_changed = Signal(int)
    voice_changed = Signal(str)
    provider_toggled = Signal(bool)
    settings_changed = Signal()
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)
    word_add_requested = Signal(str)
    word_remove_requested = Signal(str)
    language_filter_changed = Signal(str)

    def __init__(self, i18n):
        super().__init__(
            i18n=i18n,
            title_key="chat.header.title",
            subtitle_key="chat.header.subtitle"
        )
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        self.body_layout = FlowLayout(hspacing=16, vspacing=16)

        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(380)
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

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.tabs)
        left_container.setMinimumWidth(380)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.body_layout.addWidget(left_container)
        self.body_layout.addWidget(self.chat_display_panel)
        
        self.main_layout.addLayout(self.body_layout)

    def _connect_internal_signals(self):
        self.tts_settings_panel.provider_toggled.connect(self.provider_toggled.emit)
        self.tts_settings_panel.volume_changed.connect(self.volume_changed.emit)
        self.tts_settings_panel.language_filter_changed.connect(self.language_filter_changed.emit)
        self.tts_settings_panel.voice_changed.connect(self.voice_changed.emit)
        self.tts_settings_panel.settings_changed.connect(self.settings_changed.emit)

        self.bot_panel.bot_add_requested.connect(self.bot_add_requested.emit)
        self.bot_panel.bot_remove_requested.connect(self.bot_remove_requested.emit)
        self.bot_panel.word_add_requested.connect(self.word_add_requested.emit)
        self.bot_panel.word_remove_requested.connect(self.word_remove_requested.emit)

        self.overlay_settings_panel.settings_changed.connect(self.settings_changed.emit)

    @property
    def tts_enabled(self) -> bool:
        return self.tts_settings_panel.chk_tts.isChecked()

    @property
    def read_name_enabled(self) -> bool:
        return self.tts_settings_panel.chk_name.isChecked()

    @property
    def use_command_enabled(self) -> bool:
        return self.tts_settings_panel.chk_command.isChecked()

    @property
    def tts_command(self) -> str:
        return self.tts_settings_panel.txt_command.text().strip().lower()

    @property
    def is_web_provider(self) -> bool:
        return self.tts_settings_panel.chk_provider.isChecked()

    @property
    def tts_volume(self) -> int:
        return self.tts_settings_panel.slider_vol.value()

    @property
    def overlay_theme(self) -> str:
        return self.overlay_settings_panel.combo_overlay_theme.currentData() or "glass"

    @property
    def overlay_size(self) -> int:
        return self.overlay_settings_panel.slider_overlay_size.value()

    @property
    def overlay_fade(self) -> int:
        return self.overlay_settings_panel.slider_overlay_fade.value()

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

    def set_settings_ui(self, enabled: bool, read_name: bool, use_command: bool, command: str, is_web_provider: bool, volume: int, role_voices: dict = None):
        self.tts_settings_panel.set_settings_ui(enabled, read_name, use_command, command, is_web_provider, volume, role_voices)

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

    def append_message(self, user: str, message: str, color: str, timestamp: str = "", is_html: bool = False):
        self.chat_display_panel.append_message(user, message, color, timestamp, is_html)