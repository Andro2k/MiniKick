# frontend\components\chat\tts_settings.py

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize
from PySide6.QtWidgets import QLabel, QLineEdit, QSizePolicy, QWidget, QHBoxLayout, QPushButton, QVBoxLayout
from frontend.widgets import (ModernCard, SettingRow, SliderRow, ModernSwitch, ModernDivider,
                              NoWheelComboBox, NoWheelSlider)
from frontend.common import (
    validate_trigger_prefix,
    get_icon_colored,
    get_pixmap_colored,
    COLOR_NEUTRAL_200,
    COLOR_NEUTRAL_400,
    COLOR_GREEN,
)

class VoiceSettingRow(QWidget):
    def __init__(self, icon_name: str, title_text: str, combo: NoWheelComboBox,
                 switch: ModernSwitch = None, test_signal=None, tooltip_text="",
                 action_button: QPushButton = None,
                 icon_color=COLOR_NEUTRAL_200, parent=None):
        super().__init__(parent)
        self.switch = switch
        self.combo = combo
        self.btn_test = None
        self.action_button = action_button

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        icon_lbl = QLabel(parent=self)
        icon_lbl.setPixmap(get_pixmap_colored(icon_name, icon_color, size=16))

        lbl_title = QLabel(title_text, parent=self)
        lbl_title.setProperty("role", "h3")

        header_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)

        if self.switch is not None:
            controls_layout.addWidget(self.switch, alignment=Qt.AlignmentFlag.AlignVCenter)
            self.switch.toggled.connect(self._on_switch_toggled)

        combo.setMinimumWidth(0)
        from PySide6.QtWidgets import QComboBox
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(1)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        controls_layout.addWidget(combo, stretch=1)

        if self.action_button is not None:
            controls_layout.addWidget(self.action_button)

        if test_signal is not None:
            self.btn_test = QPushButton()
            self.btn_test.setIcon(get_icon_colored("volume.svg", COLOR_NEUTRAL_400, size=14))
            self.btn_test.setIconSize(QSize(14, 14))
            self.btn_test.setFixedSize(28, 28)
            self.btn_test.setToolTip(tooltip_text)
            self.btn_test.setProperty("role", "action_neutral_border")

            def trigger_test():
                voice_id = combo.currentData() or ""
                if voice_id and test_signal is not None:
                    self.btn_test.setEnabled(False)
                    test_signal.emit(voice_id)
                    QTimer.singleShot(3000, lambda: self.btn_test.setEnabled(True) if (not self.switch or self.switch.isChecked()) else None)

            self.btn_test.clicked.connect(trigger_test)
            controls_layout.addWidget(self.btn_test)

        main_layout.addLayout(controls_layout)

        if self.switch is not None:
            self._on_switch_toggled(self.switch.isChecked())

    def _on_switch_toggled(self, checked: bool):
        self.combo.setEnabled(checked)
        if self.btn_test is not None:
            self.btn_test.setEnabled(checked)

class ChatTtsSettingsPanel(ModernCard):
    volume_changed = Signal(int)
    speed_changed = Signal(int)
    voice_changed = Signal(str)
    provider_changed = Signal(str)
    manage_piper_voices_requested = Signal()
    settings_changed = Signal()
    language_filter_changed = Signal(str)
    voice_test_requested = Signal(str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=8, spacing=4, orientation="vertical")
        self.i18n = i18n
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.chk_tts = ModernSwitch(self)
        self.chk_name = ModernSwitch(self)
        self.combo_provider = NoWheelComboBox(self)
        self.combo_provider.addItem(self.i18n.get("chat.status.provider_piper"), userData="piper")
        self.combo_provider.addItem(self.i18n.get("chat.status.provider_cloud"), userData="web")
        self.combo_provider.addItem(self.i18n.get("chat.status.provider_local"), userData="local")
        self.chk_command = ModernSwitch(self)

        self.btn_manage_piper = QPushButton(self.i18n.get("chat.settings.manage_piper_btn"), self)
        self.btn_manage_piper.setIcon(get_icon_colored("cloud-download.svg", COLOR_GREEN, size=14))
        self.btn_manage_piper.setIconSize(QSize(14, 14))
        self.btn_manage_piper.setToolTip(self.i18n.get("chat.settings.manage_piper_tooltip"))
        self.btn_manage_piper.setProperty("role", "action_accent_border")
        self.btn_manage_piper.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manage_piper.clicked.connect(self.manage_piper_voices_requested.emit)

        self.slider_vol = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.lbl_vol_perc = QLabel("100%", parent=self)
        self.lbl_vol_perc.setProperty("role", "monospace")

        self.slider_speed = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
        self.slider_speed.setRange(50, 150)
        self.slider_speed.setValue(100)
        self.lbl_speed_perc = QLabel("100%", parent=self)
        self.lbl_speed_perc.setProperty("role", "monospace")

        row_tts = SettingRow("volume.svg", self.i18n.get("chat.settings.tts_title"), self.i18n.get("chat.settings.tts_desc"), self.chk_tts)
        row_read_name = SettingRow("user.svg", self.i18n.get("chat.settings.name_title"), self.i18n.get("chat.settings.name_desc"), self.chk_name)
        row_cmd = SettingRow("code.svg", self.i18n.get("chat.settings.cmd_title"), self.i18n.get("chat.settings.cmd_desc"), self.chk_command)

        self.txt_command = QLineEdit(parent=self)
        self.txt_command.setPlaceholderText(self.i18n.get("chat.settings.prefix_placeholder"))
        self.txt_command.setFixedWidth(80)
        self.txt_command.setEnabled(self.chk_command.isChecked())
        row_prefix = SettingRow("hash.svg", self.i18n.get("chat.settings.prefix_title"), self.i18n.get("chat.settings.prefix_desc"), self.txt_command)
        row_volume = SliderRow("adjustments.svg", self.i18n.get("chat.settings.vol_title"), self.i18n.get("chat.settings.vol_desc"), self.slider_vol, self.lbl_vol_perc)
        row_speed = SliderRow("dashboard.svg", self.i18n.get("chat.settings.speed_title"), self.i18n.get("chat.settings.speed_desc"), self.slider_speed, self.lbl_speed_perc)

        self.addWidget(row_tts)
        self.addWidget(row_read_name)
        self.addWidget(row_cmd)
        self.addWidget(row_prefix)
        self.addWidget(row_volume)
        self.addWidget(row_speed)

        divider = ModernDivider()
        self.addWidget(divider)

        category_lbl = QLabel(self.i18n.get("chat.roles.title"))
        category_lbl.setProperty("role", "category")
        self.addWidget(category_lbl)

        voices_card = ModernCard(parent=self, margin=4, spacing=4, orientation="vertical")

        row_provider = VoiceSettingRow(
            "world.svg",
            self.i18n.get("chat.settings.provider_title"),
            self.combo_provider,
            action_button=self.btn_manage_piper
        )
        voices_card.addWidget(row_provider)

        self.combo_voice = NoWheelComboBox(self)
        self.combo_voice_broadcaster = NoWheelComboBox(self)
        self.combo_voice_moderator = NoWheelComboBox(self)
        self.combo_voice_vip = NoWheelComboBox(self)
        self.combo_voice_subscriber = NoWheelComboBox(self)

        self.sw_role_everyone = ModernSwitch(self)
        self.sw_role_everyone.setChecked(True)
        self.sw_role_broadcaster = ModernSwitch(self)
        self.sw_role_broadcaster.setChecked(True)
        self.sw_role_moderator = ModernSwitch(self)
        self.sw_role_moderator.setChecked(True)
        self.sw_role_vip = ModernSwitch(self)
        self.sw_role_vip.setChecked(True)
        self.sw_role_subscriber = ModernSwitch(self)
        self.sw_role_subscriber.setChecked(True)

        row_voice_general = VoiceSettingRow(
            "users.svg",
            self.i18n.get("chat.settings.voice_general_title"),
            self.combo_voice,
            switch=self.sw_role_everyone,
            test_signal=self.voice_test_requested,
            tooltip_text=self.i18n.get("chat.status.test_btn_tooltip")
        )
        row_role_broadcaster = VoiceSettingRow(
            "microphone.svg",
            self.i18n.get("chat.roles.broadcaster_title"),
            self.combo_voice_broadcaster,
            switch=self.sw_role_broadcaster,
            test_signal=self.voice_test_requested,
            tooltip_text=self.i18n.get("chat.status.test_btn_tooltip")
        )
        row_role_moderator = VoiceSettingRow(
            "shield-user-bold.svg",
            self.i18n.get("chat.roles.moderator_title"),
            self.combo_voice_moderator,
            switch=self.sw_role_moderator,
            test_signal=self.voice_test_requested,
            tooltip_text=self.i18n.get("chat.status.test_btn_tooltip")
        )
        row_role_vip = VoiceSettingRow(
            "star.svg",
            self.i18n.get("chat.roles.vip_title"),
            self.combo_voice_vip,
            switch=self.sw_role_vip,
            test_signal=self.voice_test_requested,
            tooltip_text=self.i18n.get("chat.status.test_btn_tooltip")
        )
        row_role_subscriber = VoiceSettingRow(
            "crown.svg",
            self.i18n.get("chat.roles.subscriber_title"),
            self.combo_voice_subscriber,
            switch=self.sw_role_subscriber,
            test_signal=self.voice_test_requested,
            tooltip_text=self.i18n.get("chat.status.test_btn_tooltip")
        )

        voices_card.addWidget(row_voice_general)
        voices_card.addWidget(row_role_broadcaster)
        voices_card.addWidget(row_role_moderator)
        voices_card.addWidget(row_role_vip)
        voices_card.addWidget(row_role_subscriber)

        self.addWidget(voices_card)
        self.addStretch()

    def _connect_signals(self):
        self.combo_provider.currentIndexChanged.connect(self._on_provider_combo_changed)
        self.slider_vol.valueChanged.connect(self._on_slider_vol_changed)
        self.slider_speed.valueChanged.connect(self._on_slider_speed_changed)
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        self.txt_command.textChanged.connect(self._enforce_prefix_mask)
        self.chk_command.toggled.connect(self.txt_command.setEnabled)

        controls = [
            self.chk_tts, self.chk_name, self.chk_command, self.txt_command,
            self.combo_provider, self.slider_speed,
            self.combo_voice_broadcaster, self.combo_voice_moderator,
            self.combo_voice_vip, self.combo_voice_subscriber,
            self.sw_role_everyone, self.sw_role_broadcaster,
            self.sw_role_moderator, self.sw_role_vip, self.sw_role_subscriber
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

    def _on_provider_combo_changed(self, index: int):
        provider = self.combo_provider.currentData() or "piper"
        self.btn_manage_piper.setVisible(provider == "piper")
        self.provider_changed.emit(provider)

    def _on_setting_changed(self, *args):
        self.settings_changed.emit()

    @Slot(int)
    def _on_slider_vol_changed(self, value: int):
        self.lbl_vol_perc.setText(f"{value}%")
        self.volume_changed.emit(value)

    @Slot(int)
    def _on_slider_speed_changed(self, value: int):
        self.lbl_speed_perc.setText(f"{value}%")
        self.speed_changed.emit(value)

    def _on_voice_selected(self, index: int):
        if index >= 0:
            voice_id = self.combo_voice.itemData(index)
            self.voice_changed.emit(voice_id)

    def _enforce_prefix_mask(self, text):
        is_valid = validate_trigger_prefix(text)
        self.txt_command.setProperty("state", "normal" if is_valid else "error")
        self.txt_command.style().unpolish(self.txt_command)
        self.txt_command.style().polish(self.txt_command)

    def set_settings_ui(self, enabled: bool, read_name: bool, use_command: bool, command: str,
                        is_web_provider: bool = False, volume: int = 100, role_voices: dict = None,
                        role_enabled: dict = None, provider: str = None, speed: int = 100):
        interactive_widgets = [
            self.chk_tts, self.chk_name, self.chk_command, self.txt_command,
            self.combo_provider, self.slider_vol, self.slider_speed,
            self.sw_role_everyone, self.sw_role_broadcaster,
            self.sw_role_moderator, self.sw_role_vip, self.sw_role_subscriber
        ]
        for w in interactive_widgets:
            w.blockSignals(True)
        self.blockSignals(True)

        try:
            self.chk_tts.setChecked(enabled)
            self.chk_name.setChecked(read_name)
            self.chk_command.setChecked(use_command)
            self.txt_command.setText(command)
            self.txt_command.setEnabled(use_command)

            if provider:
                provider_val = provider
            else:
                provider_val = "web" if is_web_provider else "piper"

            idx = self.combo_provider.findData(provider_val)
            if idx >= 0:
                self.combo_provider.setCurrentIndex(idx)
            self.btn_manage_piper.setVisible(provider_val == "piper")

            self.slider_vol.setValue(volume)
            self.lbl_vol_perc.setText(f"{volume}%")
            self.slider_speed.setValue(speed)
            self.lbl_speed_perc.setText(f"{speed}%")
            self._pending_role_voices = role_voices or {}

            if role_enabled:
                self.sw_role_everyone.setChecked(role_enabled.get("everyone", True))
                self.sw_role_broadcaster.setChecked(role_enabled.get("broadcaster", True))
                self.sw_role_moderator.setChecked(role_enabled.get("moderator", True))
                self.sw_role_vip.setChecked(role_enabled.get("vip", True))
                self.sw_role_subscriber.setChecked(role_enabled.get("subscriber", True))
        finally:
            for w in interactive_widgets:
                w.blockSignals(False)
            self.blockSignals(False)

    def update_languages(self, langs: list[str], select_prefix: str = None):
        pass

    def update_voices(self, voices: list[tuple[str, str]], select_id: str = None, role_voices: dict = None, all_voices: list[tuple[str, str]] = None):
        is_loading = (len(voices) == 1 and voices[0][0] == "loading")
        
        self.combo_voice.blockSignals(True)
        self.combo_voice.clear()

        role_voices_pool = all_voices if all_voices is not None else voices

        index_to_select = 0
        for i, (v_id, v_name) in enumerate(role_voices_pool):
            self.combo_voice.addItem(v_name, userData=v_id)
            if v_id == select_id:
                index_to_select = i
        if self.combo_voice.count() > 0:
            self.combo_voice.setCurrentIndex(index_to_select)
        self.combo_voice.setEnabled(not is_loading)
        self.combo_voice.blockSignals(False)

        if role_voices is None and hasattr(self, '_pending_role_voices'):
            role_voices = self._pending_role_voices

        role_combos = {
            "broadcaster": self.combo_voice_broadcaster,
            "moderator": self.combo_voice_moderator,
            "vip": self.combo_voice_vip,
            "subscriber": self.combo_voice_subscriber
        }

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
            combo.setEnabled(not is_loading)
            combo.blockSignals(False)

    def get_role_voices(self) -> dict:
        return {
            "role_voice_broadcaster": self.combo_voice_broadcaster.currentData() or "",
            "role_voice_moderator": self.combo_voice_moderator.currentData() or "",
            "role_voice_vip": self.combo_voice_vip.currentData() or "",
            "role_voice_subscriber": self.combo_voice_subscriber.currentData() or "",
            "role_enabled_everyone": self.sw_role_everyone.isChecked(),
            "role_enabled_broadcaster": self.sw_role_broadcaster.isChecked(),
            "role_enabled_moderator": self.sw_role_moderator.isChecked(),
            "role_enabled_vip": self.sw_role_vip.isChecked(),
            "role_enabled_subscriber": self.sw_role_subscriber.isChecked(),
        }
