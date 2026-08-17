# frontend\components\chat\overlay_settings.py

from PySide6.QtCore import Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication
from frontend.widgets import (
    ModernCard, SettingRow, ModernSwitch, ModernButton, 
    CompactSpinBox, ModernDivider, ModernSegmentedControl
)
from frontend.common.utils import NoWheelComboBox

class ChatOverlaySettingsPanel(ModernCard):
    settings_changed = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=12, spacing=8, orientation="vertical")
        self.i18n = i18n
        self._chat_overlay_url = ""
        self.chat_overlay_full_url = ""
       
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._emit_settings_changed)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.combo_overlay_theme = NoWheelComboBox(self)
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

        self.seg_overlay_orientation = ModernSegmentedControl(self)
        self.seg_overlay_orientation.add_option("vertical", "arrows-vertical.svg", self.i18n.get("chat.overlay.orientation_vertical"))
        self.seg_overlay_orientation.add_option("horizontal", "arrows-horizontal.svg", self.i18n.get("chat.overlay.orientation_horizontal"))
        
        row_overlay_orientation = SettingRow(
            "align-left-2.svg",
            self.i18n.get("chat.overlay.orientation_title"),
            self.i18n.get("chat.overlay.orientation_desc"),
            self.seg_overlay_orientation
        )

        self.seg_overlay_flow = ModernSegmentedControl(self)
        self._populate_flow_options("vertical")

        row_overlay_flow = SettingRow(
            "arrows-sort.svg",
            self.i18n.get("chat.overlay.flow_title"),
            self.i18n.get("chat.overlay.flow_desc"),
            self.seg_overlay_flow
        )

        self.seg_overlay_entry = ModernSegmentedControl(self)
        self.seg_overlay_entry.add_option("bottom", "chevron-up.svg", self.i18n.get("chat.overlay.entry_bottom"))
        self.seg_overlay_entry.add_option("top", "chevron-down.svg", self.i18n.get("chat.overlay.entry_top"))
        self.seg_overlay_entry.add_option("left", "chevron-right.svg", self.i18n.get("chat.overlay.entry_left"))
        self.seg_overlay_entry.add_option("right", "chevron-left.svg", self.i18n.get("chat.overlay.entry_right"))

        row_overlay_entry = SettingRow(
            "movie.svg",
            self.i18n.get("chat.overlay.entry_title"),
            self.i18n.get("chat.overlay.entry_desc"),
            self.seg_overlay_entry
        )
        
        self.spin_overlay_size = CompactSpinBox(10, 32, 14, suffix="px")
        row_overlay_size = SettingRow(
            "text-size.svg",
            self.i18n.get("chat.overlay.size_title"),
            self.i18n.get("chat.overlay.size_desc"),
            self.spin_overlay_size
        )
        
        self.spin_overlay_fade = CompactSpinBox(0, 120, 15, suffix="s", special_value_text=self.i18n.get("chat.overlay.fade_never"))
        row_overlay_fade = SettingRow(
            "stopwatch.svg",
            self.i18n.get("chat.overlay.fade_title"),
            self.i18n.get("chat.overlay.fade_desc"),
            self.spin_overlay_fade
        )
        
        self.sw_overlay_show_bots = ModernSwitch()
        self.sw_overlay_show_bots.setChecked(False)
        row_overlay_show_bots = SettingRow(
            "bot.svg",
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
        self.addWidget(row_overlay_orientation)
        self.addWidget(row_overlay_flow)
        self.addWidget(row_overlay_entry)
        self.addWidget(row_overlay_size)
        self.addWidget(row_overlay_fade)
        self.addWidget(row_overlay_show_bots)
        self.addWidget(row_overlay_show_time)
        
        divider = ModernDivider()
        self.addWidget(divider)
        self.addWidget(row_copy_obs)
        self.addStretch()

    def _populate_flow_options(self, orientation: str):
        self.seg_overlay_flow.blockSignals(True)
        if orientation == "horizontal":
            options = [
                ("right-to-left", "chevron-left.svg", self.i18n.get("chat.overlay.flow_r2l")),
                ("left-to-right", "chevron-right.svg", self.i18n.get("chat.overlay.flow_l2r"))
            ]
        else:
            options = [
                ("bottom-to-top", "chevron-up.svg", self.i18n.get("chat.overlay.flow_b2t")),
                ("top-to-bottom", "chevron-down.svg", self.i18n.get("chat.overlay.flow_t2b"))
            ]
        self.seg_overlay_flow.set_options(options)
        self.seg_overlay_flow.blockSignals(False)

    def _on_orientation_changed(self, orientation: str):
        self._populate_flow_options(orientation)
        if orientation == "horizontal":
            self.seg_overlay_entry.set_current_value("right")
        else:
            self.seg_overlay_entry.set_current_value("bottom")
        self._update_overlay_url()

    def _connect_signals(self):
        self.combo_overlay_theme.currentIndexChanged.connect(self._update_overlay_url)
        self.seg_overlay_orientation.value_changed.connect(self._on_orientation_changed)
        self.seg_overlay_flow.value_changed.connect(self._update_overlay_url)
        self.seg_overlay_entry.value_changed.connect(self._update_overlay_url)
        self.spin_overlay_size.valueChanged.connect(self._update_overlay_url)
        self.spin_overlay_fade.valueChanged.connect(self._update_overlay_url)
        self.sw_overlay_show_bots.toggled.connect(self._update_overlay_url)
        self.sw_overlay_show_time.toggled.connect(self._update_overlay_url)
        self.btn_copy_overlay_obs.clicked.connect(self._copy_overlay_obs_url)

        self.combo_overlay_theme.currentIndexChanged.connect(self._on_setting_changed)
        self.seg_overlay_orientation.value_changed.connect(self._on_setting_changed)
        self.seg_overlay_flow.value_changed.connect(self._on_setting_changed)
        self.seg_overlay_entry.value_changed.connect(self._on_setting_changed)
        self.sw_overlay_show_bots.toggled.connect(self._on_setting_changed)
        self.sw_overlay_show_time.toggled.connect(self._on_setting_changed)
        self.spin_overlay_size.valueChanged.connect(self._on_setting_changed)
        self.spin_overlay_fade.valueChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self, *args):
        self._save_timer.start()

    def _emit_settings_changed(self):
        self.settings_changed.emit()

    @property
    def chat_overlay_url(self):
        return self._chat_overlay_url

    @chat_overlay_url.setter
    def chat_overlay_url(self, value):
        self._chat_overlay_url = value
        self._update_overlay_url()

    def _update_overlay_url(self, *args):
        theme = self.combo_overlay_theme.currentData() or "glass"
        orientation = self.seg_overlay_orientation.current_value() or "vertical"
        flow = self.seg_overlay_flow.current_value() or ("right-to-left" if orientation == "horizontal" else "bottom-to-top")
        entry = self.seg_overlay_entry.current_value() or ("right" if orientation == "horizontal" else "bottom")
        size = self.spin_overlay_size.value()
        fade = self.spin_overlay_fade.value()
        show_bots = "true" if self.sw_overlay_show_bots.isChecked() else "false"
        show_time = "true" if self.sw_overlay_show_time.isChecked() else "false"
        
        base_url = self._chat_overlay_url or ""
        params = f"theme={theme}&orientation={orientation}&flow={flow}&entry={entry}&size={size}px&fade={fade}&show_bots={show_bots}&show_time={show_time}"
        if "?" in base_url:
            base_part, token_part = base_url.split("?", 1)
            self.chat_overlay_full_url = f"{base_part}?{token_part}&{params}"
        else:
            self.chat_overlay_full_url = f"{base_url}?{params}"

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

    def set_overlay_settings_ui(self, theme: str, size: int, fade: int, show_bots: bool, show_time: bool, orientation: str = "vertical", flow: str = "", entry: str = ""):
        self.blockSignals(True)
        self.combo_overlay_theme.blockSignals(True)
        self.seg_overlay_orientation.blockSignals(True)
        self.seg_overlay_flow.blockSignals(True)
        self.seg_overlay_entry.blockSignals(True)
        self.spin_overlay_size.blockSignals(True)
        self.spin_overlay_fade.blockSignals(True)
        self.sw_overlay_show_bots.blockSignals(True)
        self.sw_overlay_show_time.blockSignals(True)

        idx = self.combo_overlay_theme.findData(theme)
        if idx != -1:
            self.combo_overlay_theme.setCurrentIndex(idx)

        if orientation:
            self.seg_overlay_orientation.set_current_value(orientation)
            self._populate_flow_options(orientation)

        if flow:
            self.seg_overlay_flow.set_current_value(flow)

        if entry:
            self.seg_overlay_entry.set_current_value(entry)

        self.spin_overlay_size.setValue(size)
        self.spin_overlay_fade.setValue(fade)
        self.sw_overlay_show_bots.setChecked(show_bots)
        self.sw_overlay_show_time.setChecked(show_time)

        self.combo_overlay_theme.blockSignals(False)
        self.seg_overlay_orientation.blockSignals(False)
        self.seg_overlay_flow.blockSignals(False)
        self.seg_overlay_entry.blockSignals(False)
        self.spin_overlay_size.blockSignals(False)
        self.spin_overlay_fade.blockSignals(False)
        self.sw_overlay_show_bots.blockSignals(False)
        self.sw_overlay_show_time.blockSignals(False)
        self.blockSignals(False)
        
        self._update_overlay_url()
