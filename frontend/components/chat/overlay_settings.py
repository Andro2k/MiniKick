# frontend\components\chat\overlay_settings.py

from PySide6.QtCore import Signal, Slot, QTimer
from PySide6.QtWidgets import QFrame, QApplication
from frontend.widgets import ModernCard, SettingRow, ModernSwitch, ModernButton, CompactSlider
from frontend.common.utils import NoWheelComboBox

class ChatOverlaySettingsPanel(ModernCard):
    settings_changed = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=12, spacing=8, orientation="vertical")
        self.i18n = i18n
        self._chat_overlay_url = ""
        self.chat_overlay_full_url = ""
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.combo_overlay_theme = NoWheelComboBox()
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_glass"), "glass")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_neon"), "neon")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_card"), "card")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_cyber"), "cyber")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_minimal"), "minimal")
        
        row_overlay_theme = SettingRow(
            "palette.svg", 
            self.i18n.get("chat.overlay.theme_title"), 
            self.i18n.get("chat.overlay.theme_desc"), 
            self.combo_overlay_theme
        )
        
        self.slider_overlay_size = CompactSlider(10, 32, 14, suffix="px")
        row_overlay_size = SettingRow(
            "text-size.svg",
            self.i18n.get("chat.overlay.size_title"),
            self.i18n.get("chat.overlay.size_desc"),
            self.slider_overlay_size
        )
        
        self.slider_overlay_fade = CompactSlider(0, 120, 15, suffix="s")
        row_overlay_fade = SettingRow(
            "stopwatch.svg",
            self.i18n.get("chat.overlay.fade_title"),
            self.i18n.get("chat.overlay.fade_desc"),
            self.slider_overlay_fade
        )
        
        self.sw_overlay_show_bots = ModernSwitch()
        self.sw_overlay_show_bots.setChecked(False)
        row_overlay_show_bots = SettingRow(
            "user.svg",
            self.i18n.get("chat.overlay.show_bots_title"),
            self.i18n.get("chat.overlay.show_bots_desc"),
            self.sw_overlay_show_bots
        )
        
        self.sw_overlay_show_time = ModernSwitch()
        self.sw_overlay_show_time.setChecked(False)
        row_overlay_show_time = SettingRow(
            "clock.svg",
            self.i18n.get("chat.overlay.show_time_title"),
            self.i18n.get("chat.overlay.show_time_desc"),
            self.sw_overlay_show_time
        )
        
        self.btn_copy_overlay_obs = ModernButton(self.i18n.get("common.buttons.copy"), role="action_neutral_border")
        row_copy_obs = SettingRow(
            "link.svg",
            self.i18n.get("chat.settings.obs_title"),
            self.i18n.get("chat.settings.obs_desc"),
            self.btn_copy_overlay_obs
        )
        
        self.addWidget(row_overlay_theme)
        self.addWidget(row_overlay_size)
        self.addWidget(row_overlay_fade)
        self.addWidget(row_overlay_show_bots)
        self.addWidget(row_overlay_show_time)
        
        divider = QFrame()
        divider.setProperty("role", "divider")
        divider.setFixedHeight(1)
        self.addWidget(divider)
        self.addWidget(row_copy_obs)
        self.addStretch()

    def _connect_signals(self):
        self.combo_overlay_theme.currentIndexChanged.connect(self._update_overlay_url)
        self.slider_overlay_size.slider.valueChanged.connect(self._on_overlay_size_changed)
        self.slider_overlay_fade.slider.valueChanged.connect(self._on_overlay_fade_changed)
        self.sw_overlay_show_bots.toggled.connect(self._update_overlay_url)
        self.sw_overlay_show_time.toggled.connect(self._update_overlay_url)
        self.btn_copy_overlay_obs.clicked.connect(self._copy_overlay_obs_url)

        controls = [
            self.combo_overlay_theme, self.sw_overlay_show_bots, self.sw_overlay_show_time
        ]
        for control in controls:
            if isinstance(control, ModernSwitch):
                control.toggled.connect(self._on_setting_changed)
            elif isinstance(control, NoWheelComboBox):
                control.currentIndexChanged.connect(self._on_setting_changed)

        self.slider_overlay_size.slider.valueChanged.connect(self._on_setting_changed)
        self.slider_overlay_fade.slider.valueChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self, *args):
        self.settings_changed.emit()

    @property
    def chat_overlay_url(self):
        return self._chat_overlay_url

    @chat_overlay_url.setter
    def chat_overlay_url(self, value):
        self._chat_overlay_url = value
        self._update_overlay_url()

    def _update_overlay_url(self):
        theme = self.combo_overlay_theme.currentData() or "glass"
        size = self.slider_overlay_size.value()
        fade = self.slider_overlay_fade.value()
        show_bots = "true" if self.sw_overlay_show_bots.isChecked() else "false"
        show_time = "true" if self.sw_overlay_show_time.isChecked() else "false"
        
        base_url = self._chat_overlay_url or ""
        if "?" in base_url:
            base_part, token_part = base_url.split("?", 1)
            self.chat_overlay_full_url = f"{base_part}?{token_part}&theme={theme}&size={size}px&fade={fade}&show_bots={show_bots}&show_time={show_time}"
        else:
            self.chat_overlay_full_url = f"{base_url}?theme={theme}&size={size}px&fade={fade}&show_bots={show_bots}&show_time={show_time}"

    def _on_overlay_size_changed(self, value):
        self._update_overlay_url()

    def _on_overlay_fade_changed(self, value):
        self._update_overlay_url()

    @Slot()
    def _copy_overlay_obs_url(self):
        QApplication.clipboard().setText(self.chat_overlay_full_url)
        original_text = self.btn_copy_overlay_obs.text()
        self.btn_copy_overlay_obs.setText(self.i18n.get("rewards.obs.copied"))
        self.btn_copy_overlay_obs.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_overlay_copy_btn(original_text))

    def _reset_overlay_copy_btn(self, original_text: str):
        self.btn_copy_overlay_obs.setText(original_text)
        self.btn_copy_overlay_obs.setEnabled(True)

    def set_overlay_settings_ui(self, theme: str, size: int, fade: int, show_bots: bool, show_time: bool):
        self.blockSignals(True)
        self.combo_overlay_theme.blockSignals(True)
        self.slider_overlay_size.slider.blockSignals(True)
        self.slider_overlay_fade.slider.blockSignals(True)
        self.sw_overlay_show_bots.blockSignals(True)
        self.sw_overlay_show_time.blockSignals(True)

        idx = self.combo_overlay_theme.findData(theme)
        if idx != -1:
            self.combo_overlay_theme.setCurrentIndex(idx)
        self.slider_overlay_size.setValue(size)
        self.slider_overlay_fade.setValue(fade)
        self.sw_overlay_show_bots.setChecked(show_bots)
        self.sw_overlay_show_time.setChecked(show_time)

        self.combo_overlay_theme.blockSignals(False)
        self.slider_overlay_size.slider.blockSignals(False)
        self.slider_overlay_fade.slider.blockSignals(False)
        self.sw_overlay_show_bots.blockSignals(False)
        self.sw_overlay_show_time.blockSignals(False)
        self.blockSignals(False)
        
        self._update_overlay_url()
