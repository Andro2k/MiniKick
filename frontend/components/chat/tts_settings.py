# frontend/components/chat/tts_settings.py

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QFrame
from frontend.widgets.blocks import ModernCard, SettingRow, SliderRow
from frontend.widgets.controls import ModernSwitch
from frontend.common.utils import NoWheelComboBox, NoWheelSlider, validate_trigger_prefix

class ChatTtsSettingsPanel(ModernCard):
    volume_changed = Signal(int)
    voice_changed = Signal(str)
    provider_toggled = Signal(bool)
    settings_changed = Signal()
    language_filter_changed = Signal(str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=12, spacing=8, orientation="vertical")
        self.i18n = i18n
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
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
        row_cmd = SettingRow("code.svg", self.i18n.get("chat.settings.cmd_title"), self.i18n.get("chat.settings.cmd_desc"), self.chk_command)
        
        self.txt_command = QLineEdit()
        self.txt_command.setPlaceholderText(self.i18n.get("chat.settings.prefix_placeholder"))
        self.txt_command.setFixedWidth(80)
        row_prefix = SettingRow("hash.svg", self.i18n.get("chat.settings.prefix_title"), self.i18n.get("chat.settings.prefix_desc"), self.txt_command)

        voice_volume_card = ModernCard(margin=8, spacing=6, orientation="vertical")
        
        row_provider = SettingRow("world.svg", self.i18n.get("chat.settings.provider_title"), self.i18n.get("chat.settings.provider_desc"), self.chk_provider)
        
        lang_voice_layout = QHBoxLayout()
        self.combo_lang = NoWheelComboBox()
        self.combo_voice = NoWheelComboBox()
        self.combo_voice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lang_voice_layout.addWidget(self.combo_lang)
        lang_voice_layout.addWidget(self.combo_voice)
        
        row_volume = SliderRow("adjustments.svg", self.i18n.get("chat.settings.vol_title"), self.i18n.get("chat.settings.vol_desc"), self.slider_vol, self.lbl_vol_perc)
        
        voice_volume_card.addWidget(row_provider)
        voice_volume_card.addLayout(lang_voice_layout)
        voice_volume_card.addWidget(row_volume)

        self.addWidget(row_tts)
        self.addWidget(row_read_name)
        self.addWidget(row_cmd)
        self.addWidget(row_prefix)
        self.addWidget(voice_volume_card)

        divider = QFrame()
        divider.setProperty("role", "divider")
        divider.setFixedHeight(1)
        self.addWidget(divider)
        
        category_lbl = QLabel(self.i18n.get("chat.roles.title"))
        category_lbl.setProperty("role", "category")
        self.addWidget(category_lbl)

        self.combo_voice_broadcaster = NoWheelComboBox()
        self.combo_voice_broadcaster.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_voice_broadcaster.setMinimumWidth(100)
        self.combo_voice_broadcaster.setMaximumWidth(300)
        
        self.combo_voice_moderator = NoWheelComboBox()
        self.combo_voice_moderator.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_voice_moderator.setMinimumWidth(100)
        self.combo_voice_moderator.setMaximumWidth(300)
        
        self.combo_voice_vip = NoWheelComboBox()
        self.combo_voice_vip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_voice_vip.setMinimumWidth(100)
        self.combo_voice_vip.setMaximumWidth(300)
        
        self.combo_voice_subscriber = NoWheelComboBox()
        self.combo_voice_subscriber.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_voice_subscriber.setMinimumWidth(100)
        self.combo_voice_subscriber.setMaximumWidth(300)

        row_role_broadcaster = SettingRow("user.svg", self.i18n.get("chat.roles.broadcaster_title"), self.i18n.get("chat.roles.broadcaster_desc"), self.combo_voice_broadcaster)
        row_role_moderator = SettingRow("shield-half.svg", self.i18n.get("chat.roles.moderator_title"), self.i18n.get("chat.roles.moderator_desc"), self.combo_voice_moderator)
        row_role_vip = SettingRow("star.svg", self.i18n.get("chat.roles.vip_title"), self.i18n.get("chat.roles.vip_desc"), self.combo_voice_vip)
        row_role_subscriber = SettingRow("users.svg", self.i18n.get("chat.roles.subscriber_title"), self.i18n.get("chat.roles.subscriber_desc"), self.combo_voice_subscriber)

        self.addWidget(row_role_broadcaster)
        self.addWidget(row_role_moderator)
        self.addWidget(row_role_vip)
        self.addWidget(row_role_subscriber)

        self.addStretch()

    def _connect_signals(self):
        self.chk_provider.toggled.connect(self.provider_toggled.emit)
        self.slider_vol.valueChanged.connect(self._on_slider_vol_changed)
        self.combo_lang.currentTextChanged.connect(self.language_filter_changed.emit)
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        self.txt_command.textChanged.connect(self._enforce_prefix_mask)

        controls = [
            self.chk_tts, self.chk_name, self.chk_command, self.txt_command,
            self.combo_voice_broadcaster, self.combo_voice_moderator,
            self.combo_voice_vip, self.combo_voice_subscriber
        ]
        for control in controls:
            if isinstance(control, ModernSwitch):
                control.toggled.connect(self._on_setting_changed)
            elif isinstance(control, QLineEdit):
                control.textChanged.connect(self._on_setting_changed)
            elif isinstance(control, NoWheelComboBox):
                control.currentIndexChanged.connect(self._on_setting_changed)
            elif isinstance(control, NoWheelSlider):
                control.valueChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self, *args):
        self.settings_changed.emit()

    @Slot(int)
    def _on_slider_vol_changed(self, value: int):
        self.lbl_vol_perc.setText(f"{value}%")
        self.volume_changed.emit(value)

    def _on_voice_selected(self, index: int):
        if index >= 0:
            voice_id = self.combo_voice.itemData(index)
            self.voice_changed.emit(voice_id)

    def _enforce_prefix_mask(self, text):
        if validate_trigger_prefix(text):
            self.txt_command.setStyleSheet("")
        else:
            self.txt_command.setStyleSheet("border: 1.5px solid #ff4444;")

    def set_settings_ui(self, enabled: bool, read_name: bool, use_command: bool, command: str, is_web_provider: bool, volume: int, role_voices: dict = None):
        self.blockSignals(True)
        self.chk_tts.setChecked(enabled)
        self.chk_name.setChecked(read_name)
        self.chk_command.setChecked(use_command)
        self.txt_command.setText(command)
        self.chk_provider.setChecked(is_web_provider)
        self.slider_vol.setValue(volume)
        self._pending_role_voices = role_voices or {}
        self.blockSignals(False)

    def update_languages(self, langs: list[str], select_prefix: str = None):
        self.combo_lang.blockSignals(True)
        self.combo_lang.clear()
        self.combo_lang.addItems(langs)
        if select_prefix:
            idx = self.combo_lang.findText(select_prefix)
            if idx >= 0:
                self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.blockSignals(False)

    def update_voices(self, voices: list[tuple[str, str]], select_id: str = None, role_voices: dict = None, all_voices: list[tuple[str, str]] = None):
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

        if role_voices is None and hasattr(self, '_pending_role_voices'):
            role_voices = self._pending_role_voices

        role_combos = {
            "broadcaster": self.combo_voice_broadcaster,
            "moderator": self.combo_voice_moderator,
            "vip": self.combo_voice_vip,
            "subscriber": self.combo_voice_subscriber
        }

        role_voices_pool = all_voices if all_voices is not None else voices

        for role, combo in role_combos.items():
            combo.blockSignals(True)
            combo.clear()

            default_label = self.i18n.get("chat.roles.default_voice")
            combo.addItem(default_label, userData="")

            target_id = role_voices.get(role, "") if role_voices else ""
            select_idx = 0

            for i, (v_id, v_name) in enumerate(role_voices_pool):
                combo.addItem(v_name, userData=v_id)
                if v_id == target_id:
                    select_idx = i + 1

            if combo.count() > 0:
                combo.setCurrentIndex(select_idx)
            combo.blockSignals(False)

    def get_role_voices(self) -> dict:
        return {
            "role_voice_broadcaster": self.combo_voice_broadcaster.currentData() or "",
            "role_voice_moderator": self.combo_voice_moderator.currentData() or "",
            "role_voice_vip": self.combo_voice_vip.currentData() or "",
            "role_voice_subscriber": self.combo_voice_subscriber.currentData() or "",
        }
