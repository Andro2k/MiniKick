# frontend\views\chat_view.py

import html
from PySide6.QtWidgets import (QBoxLayout, QLineEdit,
                                QHBoxLayout, QTextEdit, QLabel, 
                                QSizePolicy)
from frontend.common.utils import NoWheelComboBox, NoWheelSlider
from PySide6.QtCore import Qt, Signal, Slot
from frontend.widgets.controls_component import ModernSwitch
from frontend.widgets.base_view import BaseView
from frontend.widgets.blocks_component import SettingRow, SliderRow, ModernCard
from frontend.navigation.bot_panel_component import BotMutePanel
from frontend.common.theme import COLOR_NEUTRAL_200

class ChatView(BaseView):
    volume_changed = Signal(int)
    voice_changed = Signal(str)
    provider_toggled = Signal(bool)
    settings_changed = Signal()
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)
    language_filter_changed = Signal(str)

    _MAX_CHAT_BLOCKS = 400

    def __init__(self, i18n):
        super().__init__(
            i18n=i18n,
            title_key="chat.header.title",
            subtitle_key="chat.header.subtitle",
            icon_name="message.svg",
            icon_color=COLOR_NEUTRAL_200
        )
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        self.body_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.body_layout.setSpacing(16)

        config_card = ModernCard()
        config_card.setMinimumWidth(380) 

        self.chk_tts = ModernSwitch()
        self.chk_name = ModernSwitch() 
        self.chk_provider = ModernSwitch()
        self.chk_command = ModernSwitch()
        
        self.slider_vol = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setProperty("role", "monospace")

        row_tts = SettingRow("volume.svg", self.i18n.get("chat.settings.tts_title"), self.i18n.get("chat.settings.tts_desc"), self.chk_tts)
        row_read_name = SettingRow("user.svg", self.i18n.get("chat.settings.name_title"), self.i18n.get("chat.settings.name_desc"), self.chk_name)
        row_provider = SettingRow("globe.svg", self.i18n.get("chat.settings.provider_title"), self.i18n.get("chat.settings.provider_desc"), self.chk_provider)
        row_cmd = SettingRow("code.svg", self.i18n.get("chat.settings.cmd_title"), self.i18n.get("chat.settings.cmd_desc"), self.chk_command)
        row_volume = SliderRow("adjustments.svg", self.i18n.get("chat.settings.vol_title"), self.i18n.get("chat.settings.vol_desc"), self.slider_vol, self.lbl_vol_perc)
        
        lang_voice_layout = QHBoxLayout()
        self.combo_lang = NoWheelComboBox()
        self.combo_lang.setFixedWidth(120)
        self.combo_voice = NoWheelComboBox()
        self.combo_voice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lang_voice_layout.addWidget(self.combo_lang)
        lang_voice_layout.addWidget(self.combo_voice)

        self.txt_command = QLineEdit()
        self.txt_command.setPlaceholderText(self.i18n.get("chat.settings.prefix_placeholder"))
        self.txt_command.setFixedWidth(80)

        row_prefix = SettingRow("hash.svg", self.i18n.get("chat.settings.prefix_title"), self.i18n.get("chat.settings.prefix_desc"), self.txt_command)

        self.bot_panel = BotMutePanel(self.i18n)

        config_card.addWidget(row_tts)
        config_card.addWidget(row_read_name)
        config_card.addWidget(row_provider)
        config_card.addLayout(lang_voice_layout)
        config_card.addWidget(row_volume)
        config_card.addWidget(row_cmd)
        config_card.addWidget(row_prefix)
        config_card.addSpacing(10)
        config_card.addWidget(self.bot_panel, stretch=1) 
        
        chat_card = ModernCard()
        chat_card.setMinimumHeight(400) 

        lbl_chat_title = QLabel(self.i18n.get("chat.display.title"))
        lbl_chat_title.setProperty("role", "h3")
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setProperty("role", "ConsoleDisplay")

        chat_card.addWidget(lbl_chat_title)
        chat_card.addWidget(self.chat_display)

        self.body_layout.addWidget(config_card)
        self.body_layout.addWidget(chat_card, stretch=1)
        
        self.main_layout.addLayout(self.body_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 900:
            self.body_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        else:
            self.body_layout.setDirection(QBoxLayout.Direction.LeftToRight)

    @property
    def tts_enabled(self) -> bool:
        return self.chk_tts.isChecked()

    @property
    def read_name_enabled(self) -> bool:
        return self.chk_name.isChecked()

    @property
    def use_command_enabled(self) -> bool:
        return self.chk_command.isChecked()

    @property
    def tts_command(self) -> str:
        return self.txt_command.text().strip().lower()

    @property
    def is_web_provider(self) -> bool:
        return self.chk_provider.isChecked()

    @property
    def tts_volume(self) -> int:
        return self.slider_vol.value()

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
                control.toggled.connect(self._on_setting_changed)
            elif isinstance(control, QLineEdit):
                control.textChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self, *args):
        self.settings_changed.emit()

    def set_settings_ui(self, enabled: bool, read_name: bool, use_command: bool, command: str, is_web_provider: bool, volume: int):
        self.blockSignals(True)
        self.chk_tts.setChecked(enabled)
        self.chk_name.setChecked(read_name)
        self.chk_command.setChecked(use_command)
        self.txt_command.setText(command)
        self.chk_provider.setChecked(is_web_provider)
        self.slider_vol.setValue(volume)
        self.blockSignals(False)

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
        safe_user = html.escape(user)
        safe_message = html.escape(message)        
        safe_color = color if (color and color.startswith("#") and len(color) <= 7) else COLOR_NEUTRAL_200
        html_msg = f'<b style="color: {safe_color};">{safe_user}:</b> <span style="color: {COLOR_NEUTRAL_200};">{safe_message}</span>'
        self.chat_display.append(html_msg)
        self._trim_chat_history()

    def _trim_chat_history(self):
        doc = self.chat_display.document()
        excess = doc.blockCount() - self._MAX_CHAT_BLOCKS
        if excess <= 0:
            return
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(excess):
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    @Slot(int)
    def _on_slider_vol_changed(self, value: int):
        self.lbl_vol_perc.setText(f"{value}%")
        self.volume_changed.emit(value)

    def _enforce_prefix_mask(self, text):
        if not text.startswith("!"):
            self.txt_command.setText("!" + text.replace("!", ""))

    def _on_voice_selected(self, index: int):
        if index >= 0:
            voice_id = self.combo_voice.itemData(index)
            self.voice_changed.emit(voice_id)