# frontend\components\chat\overlay_settings.py

from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication, QLabel, QHBoxLayout, QGridLayout, QWidget, QSizePolicy
)
from frontend.common import (
    MARGIN_NONE, MARGIN_MD, MARGIN_CHIP, MARGIN_TAB_PANEL, SPACING_XS, SPACING_SM, SPACING_MD,
    COLOR_NEUTRAL_400, get_pixmap_colored
)
from frontend.widgets import (
    ModernCard, SettingRow, ModernSwitch, ModernButton, 
    CompactSpinBox, ModernSegmentedControl, NoWheelComboBox,
    InspectorPropertyRow
)
from .chat_mockup import ChatOverlayMockupWidget

class CompactToggleItem(QWidget):
    def __init__(self, icon_name: str, title: str, switch: ModernSwitch, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.switch = switch
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_CHIP)
        layout.setSpacing(SPACING_SM)

        if icon_name:
            icon_lbl = QLabel(self)
            icon_lbl.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_400, size=14))
            icon_lbl.setFixedSize(16, 16)
            layout.addWidget(icon_lbl)

        lbl = QLabel(title, self)
        lbl.setProperty("role", "caption")
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(lbl, stretch=1)

        layout.addWidget(switch, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if tooltip:
            self.setToolTip(tooltip)
            lbl.setToolTip(tooltip)

class ChatOverlaySettingsPanel(ModernCard):
    settings_changed = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=MARGIN_TAB_PANEL, spacing=SPACING_MD, orientation="vertical")
        self.setProperty("role", "tab_panel")
        self.i18n = i18n
        self._chat_overlay_url = ""
        self.chat_overlay_full_url = ""
        self._is_updating_ui = False

        self._current_orientation = "vertical"
        self._vertical_config = {
            "theme": "glass",
            "size": 14,
            "fade": 15,
            "flow": "bottom-to-top",
            "anim_in": "fade",
        }
        self._horizontal_config = {
            "theme": "glass",
            "size": 14,
            "fade": 15,
            "flow": "right-to-left",
            "anim_in": "fade",
        }

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._emit_settings_changed)

        self._setup_ui()
        self._connect_signals()

    def _create_section_header(self, text: str) -> QLabel:
        lbl = QLabel(text, self)
        lbl.setProperty("role", "caption")
        lbl.setProperty("state", "bold")
        return lbl

    def _create_metric_header(self, icon_name: str, text: str, tooltip: str = "") -> QWidget:
        header_widget = QWidget(self)
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(*MARGIN_NONE)
        layout.setSpacing(SPACING_XS)

        if icon_name:
            icon_lbl = QLabel(header_widget)
            icon_lbl.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_400, size=13))
            icon_lbl.setFixedSize(14, 14)
            layout.addWidget(icon_lbl)

        lbl = QLabel(text, header_widget)
        lbl.setProperty("role", "caption")
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(lbl, stretch=1)

        if tooltip:
            header_widget.setToolTip(tooltip)
            lbl.setToolTip(tooltip)

        return header_widget

    def _setup_ui(self):
        card_style = ModernCard(self, margin=MARGIN_MD, spacing=SPACING_SM, orientation="vertical")
        card_style.addWidget(self._create_section_header(self.i18n.get("chat.overlay.section_style")))

        self.combo_overlay_theme = NoWheelComboBox(self)
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_glass"), "glass")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_neon"), "neon")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_card"), "card")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_cyber"), "cyber")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_minimal"), "minimal")

        row_theme = InspectorPropertyRow(
            self.i18n.get("chat.overlay.theme_title"),
            self.combo_overlay_theme,
            icon_name="palette-filled.svg",
            tooltip=self.i18n.get("chat.overlay.theme_desc"),
            parent=self
        )
        card_style.addWidget(row_theme)

        grid_metrics = QGridLayout()
        grid_metrics.setContentsMargins(*MARGIN_NONE)
        grid_metrics.setSpacing(SPACING_SM)

        self.spin_overlay_size = CompactSpinBox(10, 36, 14, suffix="px", fixed_width=0)
        self.spin_overlay_size.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.spin_overlay_fade = CompactSpinBox(0, 120, 15, suffix="s", special_value_text=self.i18n.get("chat.overlay.fade_never"), fixed_width=0)
        self.spin_overlay_fade.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        header_size = self._create_metric_header(
            "text-filled.svg",
            self.i18n.get("chat.overlay.size_title"),
            self.i18n.get("chat.overlay.size_desc")
        )
        header_fade = self._create_metric_header(
            "stopwatch-filled.svg",
            self.i18n.get("chat.overlay.fade_title"),
            self.i18n.get("chat.overlay.fade_desc")
        )

        grid_metrics.addWidget(header_size, 0, 0)
        grid_metrics.addWidget(header_fade, 0, 1)

        grid_metrics.addWidget(self.spin_overlay_size, 1, 0)
        grid_metrics.addWidget(self.spin_overlay_fade, 1, 1)

        grid_metrics.setColumnStretch(0, 1)
        grid_metrics.setColumnStretch(1, 1)

        card_style.addLayout(grid_metrics)
        self.addWidget(card_style)

        card_layout = ModernCard(self, margin=MARGIN_MD, spacing=SPACING_SM, orientation="vertical")
        card_layout.addWidget(self._create_section_header(self.i18n.get("chat.overlay.section_layout")))

        self.seg_overlay_orientation = ModernSegmentedControl(self)
        self.seg_overlay_orientation.add_option("vertical", "carousel-v-filled.svg", self.i18n.get("chat.overlay.orientation_vertical"))
        self.seg_overlay_orientation.add_option("horizontal", "carousel-h-filled.svg", self.i18n.get("chat.overlay.orientation_horizontal"))

        row_orientation = InspectorPropertyRow(
            self.i18n.get("chat.overlay.orientation_title"),
            self.seg_overlay_orientation,
            icon_name="align-left-filled.svg",
            tooltip=self.i18n.get("chat.overlay.orientation_desc"),
            parent=self
        )
        card_layout.addWidget(row_orientation)

        self.seg_overlay_flow = ModernSegmentedControl(self)
        self._populate_flow_options("vertical")

        row_flow = InspectorPropertyRow(
            self.i18n.get("chat.overlay.flow_title"),
            self.seg_overlay_flow,
            icon_name="transfer-v-filled.svg",
            tooltip=self.i18n.get("chat.overlay.flow_desc"),
            parent=self
        )
        card_layout.addWidget(row_flow)

        self.combo_anim_in = NoWheelComboBox(self)
        self.combo_anim_in.addItem(self.i18n.get("chat.overlay.anim_in_fade"), "fade")
        self.combo_anim_in.addItem(self.i18n.get("chat.overlay.anim_in_slide"), "slide")
        self.combo_anim_in.addItem(self.i18n.get("chat.overlay.anim_in_pop"), "pop")

        row_anim = InspectorPropertyRow(
            self.i18n.get("chat.overlay.anim_in_title"),
            self.combo_anim_in,
            icon_name="bolt-circle-filled.svg",
            tooltip=self.i18n.get("chat.overlay.anim_in_desc"),
            parent=self
        )
        card_layout.addWidget(row_anim)
        self.addWidget(card_layout)

        card_visibility = ModernCard(self, margin=MARGIN_MD, spacing=SPACING_SM, orientation="vertical")
        card_visibility.addWidget(self._create_section_header(self.i18n.get("chat.overlay.section_visibility")))

        grid_toggles = QGridLayout()
        grid_toggles.setContentsMargins(*MARGIN_NONE)
        grid_toggles.setSpacing(SPACING_SM)

        self.sw_overlay_show_time = ModernSwitch(self)
        self.sw_overlay_show_time.setChecked(False)

        self.sw_edge_fade = ModernSwitch(self)
        self.sw_edge_fade.setChecked(True)

        self.sw_overlay_show_bots = ModernSwitch(self)
        self.sw_overlay_show_bots.setChecked(False)

        self.sw_hide_commands = ModernSwitch(self)
        self.sw_hide_commands.setChecked(False)

        self.sw_big_emotes = ModernSwitch(self)
        self.sw_big_emotes.setChecked(True)

        self.sw_show_badges = ModernSwitch(self)
        self.sw_show_badges.setChecked(True)

        self.sw_overlay_show_gifs = ModernSwitch(self)
        self.sw_overlay_show_gifs.setChecked(True)

        self.sw_show_platform = ModernSwitch(self)
        self.sw_show_platform.setChecked(True)

        item_time = CompactToggleItem("clock-filled.svg", self.i18n.get("chat.overlay.show_time_title"), self.sw_overlay_show_time, self.i18n.get("chat.overlay.show_time_desc"), self)
        item_edge = CompactToggleItem("eye-filled.svg", self.i18n.get("chat.overlay.edge_fade_title"), self.sw_edge_fade, self.i18n.get("chat.overlay.edge_fade_desc"), self)
        item_bots = CompactToggleItem("bot.svg", self.i18n.get("chat.overlay.show_bots_title"), self.sw_overlay_show_bots, self.i18n.get("chat.overlay.show_bots_desc"), self)
        item_cmds = CompactToggleItem("bolt-circle-filled.svg", self.i18n.get("chat.overlay.hide_commands_title"), self.sw_hide_commands, self.i18n.get("chat.overlay.hide_commands_desc"), self)
        item_emotes = CompactToggleItem("emoji-circle-filled.svg", self.i18n.get("chat.overlay.big_emotes_title"), self.sw_big_emotes, self.i18n.get("chat.overlay.big_emotes_desc"), self)
        item_badges = CompactToggleItem("shield-user-filled.svg", self.i18n.get("chat.overlay.show_badges_title"), self.sw_show_badges, self.i18n.get("chat.overlay.show_badges_desc"), self)
        item_gifs = CompactToggleItem("gift-filled.svg", self.i18n.get("chat.overlay.show_gifs_title"), self.sw_overlay_show_gifs, self.i18n.get("chat.overlay.show_gifs_desc"), self)
        item_plat = CompactToggleItem("brand-kick.svg", self.i18n.get("chat.overlay.show_platform_title"), self.sw_show_platform, self.i18n.get("chat.overlay.show_platform_desc"), self)

        grid_toggles.addWidget(item_time, 0, 0)
        grid_toggles.addWidget(item_edge, 0, 1)
        grid_toggles.addWidget(item_bots, 1, 0)
        grid_toggles.addWidget(item_cmds, 1, 1)
        grid_toggles.addWidget(item_emotes, 2, 0)
        grid_toggles.addWidget(item_badges, 2, 1)
        grid_toggles.addWidget(item_gifs, 3, 0)
        grid_toggles.addWidget(item_plat, 3, 1)

        card_visibility.addLayout(grid_toggles)
        self.addWidget(card_visibility)

        card_preview = ModernCard(self, margin=MARGIN_MD, spacing=SPACING_SM, orientation="vertical")
        lbl_preview = QLabel(self.i18n.get("chat.overlay.preview_title"))
        lbl_preview.setProperty("role", "body")
        card_preview.addWidget(lbl_preview)

        self.mockup_widget = ChatOverlayMockupWidget(self.i18n, parent=self)
        card_preview.addWidget(self.mockup_widget)

        self.btn_copy_overlay_obs = ModernButton(self.i18n.get("common.buttons.copy"), role="action_outlined", parent=self)
        self.row_copy_obs = SettingRow(
            "link-filled.svg",
            self.i18n.get("chat.settings.obs_title"),
            self.i18n.get("chat.settings.obs_desc"),
            self.btn_copy_overlay_obs
        )
        card_preview.addWidget(self.row_copy_obs)
        self.addWidget(card_preview)

        self.addStretch()
        self._update_mockup_preview()

    def _populate_flow_options(self, orientation: str):
        self.seg_overlay_flow.blockSignals(True)
        if orientation == "horizontal":
            options = [
                ("right-to-left", "chevron-left-filled.svg", self.i18n.get("chat.overlay.flow_r2l")),
                ("left-to-right", "chevron-right-filled.svg", self.i18n.get("chat.overlay.flow_l2r"))
            ]
        else:
            options = [
                ("bottom-to-top", "chevron-up-filled.svg", self.i18n.get("chat.overlay.flow_b2t")),
                ("top-to-bottom", "chevron-down-filled.svg", self.i18n.get("chat.overlay.flow_t2b"))
            ]
        self.seg_overlay_flow.set_options(options)
        self.seg_overlay_flow.blockSignals(False)

    def _connect_signals(self):
        self.seg_overlay_orientation.value_changed.connect(self._on_orientation_changed)
        self.combo_overlay_theme.currentIndexChanged.connect(self._on_style_setting_changed)
        self.spin_overlay_size.valueChanged.connect(self._on_style_setting_changed)
        self.spin_overlay_fade.valueChanged.connect(self._on_style_setting_changed)
        self.seg_overlay_flow.value_changed.connect(self._on_style_setting_changed)
        self.combo_anim_in.currentIndexChanged.connect(self._on_style_setting_changed)

        self.sw_overlay_show_bots.toggled.connect(self._on_common_setting_changed)
        self.sw_overlay_show_time.toggled.connect(self._on_common_setting_changed)
        self.sw_big_emotes.toggled.connect(self._on_common_setting_changed)
        self.sw_edge_fade.toggled.connect(self._on_common_setting_changed)
        self.sw_overlay_show_gifs.toggled.connect(self._on_common_setting_changed)
        self.sw_hide_commands.toggled.connect(self._on_common_setting_changed)
        self.sw_show_badges.toggled.connect(self._on_common_setting_changed)
        self.sw_show_platform.toggled.connect(self._on_common_setting_changed)

        self.btn_copy_overlay_obs.clicked.connect(self._copy_overlay_obs_url)

    def _on_orientation_changed(self, orientation: str):
        if self._is_updating_ui:
            return

        departing_cfg = self._vertical_config if self._current_orientation == "vertical" else self._horizontal_config
        departing_cfg["theme"] = self.combo_overlay_theme.currentData() or "glass"
        departing_cfg["size"] = self.spin_overlay_size.value()
        departing_cfg["fade"] = self.spin_overlay_fade.value()
        departing_cfg["flow"] = self.seg_overlay_flow.current_value() or (
            "bottom-to-top" if self._current_orientation == "vertical" else "right-to-left"
        )
        departing_cfg["anim_in"] = self.combo_anim_in.currentData() or "fade"

        self._current_orientation = orientation
        self._populate_flow_options(orientation)

        incoming_cfg = self._vertical_config if orientation == "vertical" else self._horizontal_config
        self._is_updating_ui = True
        try:
            t_idx = self.combo_overlay_theme.findData(incoming_cfg.get("theme", "glass"))
            if t_idx != -1:
                self.combo_overlay_theme.setCurrentIndex(t_idx)

            self.spin_overlay_size.setValue(int(incoming_cfg.get("size", 14)))
            self.spin_overlay_fade.setValue(int(incoming_cfg.get("fade", 15)))

            default_flow = "bottom-to-top" if orientation == "vertical" else "right-to-left"
            flow_val = incoming_cfg.get("flow", default_flow)
            self.seg_overlay_flow.set_current_value(flow_val)

            a_idx = self.combo_anim_in.findData(incoming_cfg.get("anim_in", "fade"))
            if a_idx != -1:
                self.combo_anim_in.setCurrentIndex(a_idx)
        finally:
            self._is_updating_ui = False

        self._update_overlay_url()
        self._update_mockup_preview()
        self._save_timer.start()

    def _on_style_setting_changed(self, *args):
        if self._is_updating_ui:
            return
        active_cfg = self._vertical_config if self._current_orientation == "vertical" else self._horizontal_config
        active_cfg["theme"] = self.combo_overlay_theme.currentData() or "glass"
        active_cfg["size"] = self.spin_overlay_size.value()
        active_cfg["fade"] = self.spin_overlay_fade.value()
        active_cfg["flow"] = self.seg_overlay_flow.current_value() or (
            "bottom-to-top" if self._current_orientation == "vertical" else "right-to-left"
        )
        active_cfg["anim_in"] = self.combo_anim_in.currentData() or "fade"

        self._update_mockup_preview()
        self._save_timer.start()

    def _on_common_setting_changed(self, *args):
        if self._is_updating_ui:
            return
        self._update_mockup_preview()
        self._save_timer.start()

    def _emit_settings_changed(self):
        self.settings_changed.emit()

    @property
    def vertical_config(self) -> dict:
        return dict(self._vertical_config)

    @property
    def horizontal_config(self) -> dict:
        return dict(self._horizontal_config)

    @property
    def overlay_orientation(self) -> str:
        return self.seg_overlay_orientation.current_value() or self._current_orientation

    @property
    def overlay_theme(self) -> str:
        return self.combo_overlay_theme.currentData() or "glass"

    @property
    def overlay_size(self) -> int:
        return self.spin_overlay_size.value()

    @property
    def overlay_fade(self) -> int:
        return self.spin_overlay_fade.value()

    @property
    def overlay_flow(self) -> str:
        return self.seg_overlay_flow.current_value() or (
            "bottom-to-top" if self._current_orientation == "vertical" else "right-to-left"
        )

    @property
    def overlay_anim_in(self) -> str:
        return self.combo_anim_in.currentData() or "fade"

    @property
    def overlay_show_bots(self) -> bool:
        return self.sw_overlay_show_bots.isChecked()

    @property
    def overlay_show_time(self) -> bool:
        return self.sw_overlay_show_time.isChecked()

    @property
    def overlay_show_gifs(self) -> bool:
        return self.sw_overlay_show_gifs.isChecked()

    @overlay_show_gifs.setter
    def overlay_show_gifs(self, value: bool):
        self.sw_overlay_show_gifs.blockSignals(True)
        self.sw_overlay_show_gifs.setChecked(bool(value))
        self.sw_overlay_show_gifs.blockSignals(False)

    @property
    def overlay_edge_fade(self) -> bool:
        return self.sw_edge_fade.isChecked()

    @property
    def overlay_hide_commands(self) -> bool:
        return self.sw_hide_commands.isChecked()

    @property
    def overlay_show_badges(self) -> bool:
        return self.sw_show_badges.isChecked()

    @property
    def overlay_show_platform(self) -> bool:
        return self.sw_show_platform.isChecked()

    @property
    def chat_overlay_url(self) -> str:
        return self._chat_overlay_url

    @chat_overlay_url.setter
    def chat_overlay_url(self, value: str):
        self._chat_overlay_url = value
        self._update_overlay_url()

    def _update_overlay_url(self, *args):
        orientation = self.seg_overlay_orientation.current_value() or "vertical"

        dim = "1920 × 80–300 px" if orientation == "horizontal" else "400 × 1080 px"
        desc = f"{self.i18n.get('chat.settings.obs_desc')} ({self.i18n.get('chat.overlay.recommended_dim').replace('{dim}', dim)})"
        if hasattr(self, 'row_copy_obs') and self.row_copy_obs:
            self.row_copy_obs.set_description(desc)

        base_url = self._chat_overlay_url or ""
        params = f"orientation={orientation}"
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

    def set_overlay_settings_ui(
        self,
        theme: str = "glass",
        size: int = 14,
        fade: int = 15,
        show_bots: bool = False,
        show_time: bool = False,
        orientation: str = "vertical",
        flow: str = "",
        entry: str = "",
        big_emotes: bool = True,
        edge_fade: bool = True,
        anim_in: str = "fade",
        show_gifs: bool = True,
        max_messages: int = 15,
        hide_commands: bool = False,
        show_badges: bool = True,
        show_platform: bool = True,
        vertical_config: dict = None,
        horizontal_config: dict = None,
        common_config: dict = None
    ):
        self._is_updating_ui = True
        try:
            if vertical_config and isinstance(vertical_config, dict):
                self._vertical_config = dict(vertical_config)
            else:
                self._vertical_config = {
                    "theme": theme,
                    "size": size,
                    "fade": fade,
                    "flow": flow or "bottom-to-top",
                    "anim_in": anim_in,
                }

            if horizontal_config and isinstance(horizontal_config, dict):
                self._horizontal_config = dict(horizontal_config)
            else:
                self._horizontal_config = {
                    "theme": theme,
                    "size": size,
                    "fade": fade,
                    "flow": flow or "right-to-left",
                    "anim_in": anim_in,
                }

            if common_config and isinstance(common_config, dict):
                c_show_bots = common_config.get("show_bots", show_bots)
                c_show_time = common_config.get("show_time", show_time)
                c_show_gifs = common_config.get("show_gifs", show_gifs)
                c_big_emotes = common_config.get("big_emotes", big_emotes)
                c_edge_fade = common_config.get("edge_fade", edge_fade)
                c_hide_commands = common_config.get("hide_commands", hide_commands)
                c_show_badges = common_config.get("show_badges", show_badges)
                c_show_platform = common_config.get("show_platform", show_platform)
            else:
                c_show_bots = show_bots
                c_show_time = show_time
                c_show_gifs = show_gifs
                c_big_emotes = big_emotes
                c_edge_fade = edge_fade
                c_hide_commands = hide_commands
                c_show_badges = show_badges
                c_show_platform = show_platform

            self.combo_overlay_theme.blockSignals(True)
            self.seg_overlay_orientation.blockSignals(True)
            self.seg_overlay_flow.blockSignals(True)
            self.spin_overlay_size.blockSignals(True)
            self.spin_overlay_fade.blockSignals(True)
            self.combo_anim_in.blockSignals(True)
            self.sw_overlay_show_bots.blockSignals(True)
            self.sw_overlay_show_time.blockSignals(True)
            self.sw_overlay_show_gifs.blockSignals(True)
            self.sw_big_emotes.blockSignals(True)
            self.sw_edge_fade.blockSignals(True)
            self.sw_hide_commands.blockSignals(True)
            self.sw_show_badges.blockSignals(True)
            self.sw_show_platform.blockSignals(True)

            self.sw_overlay_show_bots.setChecked(c_show_bots)
            self.sw_overlay_show_time.setChecked(c_show_time)
            self.sw_overlay_show_gifs.setChecked(c_show_gifs)
            self.sw_big_emotes.setChecked(c_big_emotes)
            self.sw_edge_fade.setChecked(c_edge_fade)
            self.sw_hide_commands.setChecked(c_hide_commands)
            self.sw_show_badges.setChecked(c_show_badges)
            self.sw_show_platform.setChecked(c_show_platform)

            self._current_orientation = orientation if orientation in ("vertical", "horizontal") else "vertical"
            self.seg_overlay_orientation.set_current_value(self._current_orientation)
            self._populate_flow_options(self._current_orientation)

            active_cfg = self._vertical_config if self._current_orientation == "vertical" else self._horizontal_config
            t_idx = self.combo_overlay_theme.findData(active_cfg.get("theme", "glass"))
            if t_idx != -1:
                self.combo_overlay_theme.setCurrentIndex(t_idx)

            self.spin_overlay_size.setValue(int(active_cfg.get("size", 14)))
            self.spin_overlay_fade.setValue(int(active_cfg.get("fade", 15)))

            default_flow = "bottom-to-top" if self._current_orientation == "vertical" else "right-to-left"
            flow_val = active_cfg.get("flow", default_flow)
            self.seg_overlay_flow.set_current_value(flow_val)

            a_idx = self.combo_anim_in.findData(active_cfg.get("anim_in", "fade"))
            if a_idx != -1:
                self.combo_anim_in.setCurrentIndex(a_idx)

        finally:
            self.combo_overlay_theme.blockSignals(False)
            self.seg_overlay_orientation.blockSignals(False)
            self.seg_overlay_flow.blockSignals(False)
            self.spin_overlay_size.blockSignals(False)
            self.spin_overlay_fade.blockSignals(False)
            self.combo_anim_in.blockSignals(False)
            self.sw_overlay_show_bots.blockSignals(False)
            self.sw_overlay_show_time.blockSignals(False)
            self.sw_overlay_show_gifs.blockSignals(False)
            self.sw_big_emotes.blockSignals(False)
            self.sw_edge_fade.blockSignals(False)
            self.sw_hide_commands.blockSignals(False)
            self.sw_show_badges.blockSignals(False)
            self.sw_show_platform.blockSignals(False)
            self._is_updating_ui = False

        self._update_overlay_url()
        self._update_mockup_preview()

    def _update_mockup_preview(self, *args):
        theme = self.combo_overlay_theme.currentData() or "glass"
        orientation = self.seg_overlay_orientation.current_value() or "vertical"
        show_time = self.sw_overlay_show_time.isChecked()
        show_bots = self.sw_overlay_show_bots.isChecked()
        show_badges = self.sw_show_badges.isChecked()
        show_platform = self.sw_show_platform.isChecked()
        edge_fade = self.sw_edge_fade.isChecked()
        hide_commands = self.sw_hide_commands.isChecked()
        big_emotes = self.sw_big_emotes.isChecked()
        show_gifs = self.sw_overlay_show_gifs.isChecked()
        if hasattr(self, "mockup_widget") and self.mockup_widget:
            self.mockup_widget.set_configuration(
                theme=theme,
                orientation=orientation,
                show_time=show_time,
                show_bots=show_bots,
                show_badges=show_badges,
                show_platform=show_platform,
                edge_fade=edge_fade,
                hide_commands=hide_commands,
                big_emotes=big_emotes,
                show_gifs=show_gifs
            )
