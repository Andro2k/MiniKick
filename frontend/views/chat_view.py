# frontend/views/chat_view.py

from PySide6.QtWidgets import (QBoxLayout, QComboBox, QLineEdit, QWidget, 
                               QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QSlider, 
                               QFrame, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, Signal, Slot

from frontend.widgets.controls_component import ModernSwitch
from frontend.widgets.blocks_component import ViewHeader, SettingRow, SettingSliderRow
from frontend.navigation.bot_panel_component import BotMutePanel
from frontend.common.theme import COLOR_ACCENT

class ChatView(QWidget):
    volume_changed = Signal(int)
    voice_changed = Signal(str)
    provider_toggled = Signal(bool)
    settings_modified = Signal(dict)
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)
    language_filter_changed = Signal(str)

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self._setup_ui()
        self._connect_internal_signals()

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
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text=self.i18n.get("chat.header.title"),
            subtitle_text=self.i18n.get("chat.header.subtitle"),
            icon_name="message.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        self.body_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.body_layout.setSpacing(16)

        config_card = QFrame()
        config_card.setProperty("role", "card")
        config_card.setMinimumWidth(380) 
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(8, 8, 8, 8)
        config_layout.setSpacing(6)

        self.chk_tts = ModernSwitch()
        self.chk_name = ModernSwitch() 
        self.chk_provider = ModernSwitch()
        self.chk_command = ModernSwitch()
        
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setProperty("role", "monospace")

        row_tts = SettingRow("volume.svg", self.i18n.get("chat.settings.tts_title"), self.i18n.get("chat.settings.tts_desc"), self.chk_tts)
        row_read_name = SettingRow("user.svg", self.i18n.get("chat.settings.name_title"), self.i18n.get("chat.settings.name_desc"), self.chk_name)
        row_provider = SettingRow("globe.svg", self.i18n.get("chat.settings.provider_title"), self.i18n.get("chat.settings.provider_desc"), self.chk_provider)
        row_cmd = SettingRow("code.svg", self.i18n.get("chat.settings.cmd_title"), self.i18n.get("chat.settings.cmd_desc"), self.chk_command)
        row_volume = SettingSliderRow("adjustments.svg", self.i18n.get("chat.settings.vol_title"), self.i18n.get("chat.settings.vol_desc"), self.slider_vol, self.lbl_vol_perc)
        
        lang_voice_layout = QHBoxLayout()
        self.combo_lang = QComboBox()
        self.combo_lang.setFixedWidth(120)
        self.combo_voice = QComboBox()
        self.combo_voice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lang_voice_layout.addWidget(self.combo_lang)
        lang_voice_layout.addWidget(self.combo_voice)

        self.txt_command = QLineEdit()
        self.txt_command.setPlaceholderText(self.i18n.get("chat.settings.prefix_placeholder"))
        self.txt_command.setFixedWidth(80)

        row_prefix = SettingRow("grid-pattern.svg", self.i18n.get("chat.settings.prefix_title"), self.i18n.get("chat.settings.prefix_desc"), self.txt_command)

        self.bot_panel = BotMutePanel(self.i18n)

        config_layout.addWidget(row_tts)
        config_layout.addWidget(row_read_name)
        config_layout.addWidget(row_provider)
        config_layout.addLayout(lang_voice_layout)
        config_layout.addWidget(row_volume)
        config_layout.addWidget(row_cmd)
        config_layout.addWidget(row_prefix)
        config_layout.addSpacing(10)
        config_layout.addWidget(self.bot_panel, stretch=1) 
        
        chat_card = QFrame()
        chat_card.setProperty("role", "card")
        chat_card.setMinimumHeight(400) 
        
        chat_layout = QVBoxLayout(chat_card)
        chat_layout.setContentsMargins(8, 8, 8, 8)
        chat_layout.setSpacing(6)

        lbl_chat_title = QLabel(self.i18n.get("chat.display.title"))
        lbl_chat_title.setProperty("role", "h3")
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setProperty("role", "console")

        chat_layout.addWidget(lbl_chat_title)
        chat_layout.addWidget(self.chat_display)

        self.body_layout.addWidget(config_card)
        self.body_layout.addWidget(chat_card, stretch=1)
        self.main_layout.addLayout(self.body_layout)

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 900:
            self.body_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        else:
            self.body_layout.setDirection(QBoxLayout.Direction.LeftToRight)

    def _connect_internal_signals(self):
        self.chk_provider.toggled.connect(self.provider_toggled.emit)
        self.slider_vol.valueChanged.connect(self._on_slider_vol_changed)
        
        self.combo_lang.currentTextChanged.connect(self.language_filter_changed.emit)
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        
        self.txt_command.textChanged.connect(self._enforce_prefix_mask)
        self.bot_panel.bot_add_requested.connect(self.bot_add_requested.emit)
        self.bot_panel.bot_remove_requested.connect(self.bot_remove_requested.emit)

        controls = [self.chk_tts, self.chk_name, self.chk_command, self.txt_command]
        for control in controls:
            if isinstance(control, ModernSwitch):
                control.toggled.connect(self._emit_current_settings)
            elif isinstance(control, QLineEdit):
                control.textChanged.connect(self._emit_current_settings)

    def set_initial_states(self, settings: dict):
        self.blockSignals(True)
        self.chk_tts.setChecked(settings.get("enabled", True))
        self.chk_name.setChecked(settings.get("read_name", True))
        self.chk_command.setChecked(settings.get("use_command", False))
        self.txt_command.setText(settings.get("command", "!tts"))
        self.chk_provider.setChecked(settings.get("provider") == "web")
        self.slider_vol.setValue(settings.get("volume", 100))
        self.blockSignals(False)
        
        self.clear_bots_list()
        ignored_users_str = settings.get("ignored_users", "")
        if ignored_users_str:
            for bot in ignored_users_str.split(","):
                if bot.strip():
                    self.add_bot_tag(bot.strip())

    def clear_bot_input(self):
        self.bot_panel.clear_input()

    def add_bot_tag(self, bot_name: str):
        self.bot_panel.add_bot_tag(bot_name)

    def clear_bots_list(self):
        self.bot_panel.clear_list()

    def update_languages(self, langs: list[str], select_prefix: str = None):
        self.combo_lang.blockSignals(True)
        self.combo_lang.clear()
        self.combo_lang.addItems(langs)
        if select_prefix:
            idx = self.combo_lang.findText(select_prefix)
            if idx >= 0:
                self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.blockSignals(False)

    def update_voices(self, voices: list[tuple[str, str]], select_id: str = None):
        self.combo_voice.blockSignals(True)
        self.combo_voice.clear()
        index_to_select = 0
        for i, (v_id, v_name) in enumerate(voices):
            self.combo_voice.addItem(v_name, userData=v_id)
            if v_id == select_id:
                index_to_select = i
                
        if self.combo_voice.count() > 0:
            self.combo_voice.setCurrentIndex(index_to_select)
        self.combo_voice.blockSignals(False)

    def append_message(self, user: str, message: str, color: str):
        html_msg = f'<b style="color: {color};">{user}:</b> <span style="color: #f0f0f0;">{message}</span>'
        self.chat_display.append(html_msg)

    @Slot(int)
    def _on_slider_vol_changed(self, value: int):
        self.lbl_vol_perc.setText(f"{value}%")
        self.volume_changed.emit(value)

    def _enforce_prefix_mask(self, text):
        if not text.startswith("!"):
            self.txt_command.setText("!" + text.replace("!", ""))

    def _emit_current_settings(self):
        self.settings_modified.emit({
            "enabled": self.chk_tts.isChecked(),
            "read_name": self.chk_name.isChecked(),
            "use_command": self.chk_command.isChecked(),
            "command": self.txt_command.text().strip().lower(),
            "provider": "web" if self.chk_provider.isChecked() else "local"
        })

    def _on_voice_selected(self, index: int):
        if index >= 0:
            voice_id = self.combo_voice.itemData(index)
            self.voice_changed.emit(voice_id)