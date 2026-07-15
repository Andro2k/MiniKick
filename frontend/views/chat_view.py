# frontend\views\chat_view.py

import html
from PySide6.QtWidgets import QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QSizePolicy, QTabWidget, QScrollArea, QFrame
from frontend.common.utils import NoWheelComboBox, NoWheelSlider, validate_trigger_prefix
from PySide6.QtCore import Qt, Signal, Slot
from frontend.widgets.controls_component import ModernSwitch, ModernButton
from frontend.widgets.base_view import BaseView
from frontend.widgets.flow_layout import FlowLayout
from frontend.widgets.blocks_component import SettingRow, SliderRow, ModernCard
from frontend.navigation.bot_panel_component import BotMutePanel
from frontend.common.theme import COLOR_NEUTRAL_200, COLOR_NEUTRAL_500

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
            subtitle_key="chat.header.subtitle"
        )
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        self.body_layout = FlowLayout(hspacing=16, vspacing=16)

        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(380)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tabs.addTab(self._setup_tts_settings_tab(), self.i18n.get("chat.tabs.settings"))
        self.tabs.addTab(self._setup_muted_tab(), self.i18n.get("chat.tabs.muted"))
        self.tabs.addTab(self._setup_overlay_settings_tab(), self.i18n.get("chat.tabs.overlay"))

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.tabs)
        left_container.setMinimumWidth(380)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        chat_card = self._setup_chat_panel()

        self.body_layout.addWidget(left_container)
        self.body_layout.addWidget(chat_card)
        
        self.main_layout.addLayout(self.body_layout)

    def _setup_tts_settings_tab(self) -> QScrollArea:
        config_card = ModernCard()

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
        row_provider = SettingRow("world.svg", self.i18n.get("chat.settings.provider_title"), self.i18n.get("chat.settings.provider_desc"), self.chk_provider)
        row_cmd = SettingRow("code.svg", self.i18n.get("chat.settings.cmd_title"), self.i18n.get("chat.settings.cmd_desc"), self.chk_command)
        row_volume = SliderRow("adjustments.svg", self.i18n.get("chat.settings.vol_title"), self.i18n.get("chat.settings.vol_desc"), self.slider_vol, self.lbl_vol_perc)
        
        lang_voice_layout = QHBoxLayout()
        self.combo_lang = NoWheelComboBox()
        self.combo_voice = NoWheelComboBox()
        self.combo_voice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lang_voice_layout.addWidget(self.combo_lang)
        lang_voice_layout.addWidget(self.combo_voice)

        self.txt_command = QLineEdit()
        self.txt_command.setPlaceholderText(self.i18n.get("chat.settings.prefix_placeholder"))
        self.txt_command.setFixedWidth(80)

        row_prefix = SettingRow("hash.svg", self.i18n.get("chat.settings.prefix_title"), self.i18n.get("chat.settings.prefix_desc"), self.txt_command)

        config_card.addWidget(row_tts)
        config_card.addWidget(row_read_name)
        config_card.addWidget(row_provider)
        config_card.addLayout(lang_voice_layout)
        config_card.addWidget(row_volume)
        config_card.addWidget(row_cmd)
        config_card.addWidget(row_prefix)

        divider = QFrame()
        divider.setProperty("role", "divider")
        divider.setFixedHeight(1)
        config_card.addWidget(divider)
        category_lbl = QLabel(self.i18n.get("chat.roles.title"))
        category_lbl.setProperty("role", "category")
        config_card.addWidget(category_lbl)

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

        config_card.addWidget(row_role_broadcaster)
        config_card.addWidget(row_role_moderator)
        config_card.addWidget(row_role_vip)
        config_card.addWidget(row_role_subscriber)

        config_card.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(config_card)
        return scroll

    def _setup_muted_tab(self) -> ModernCard:
        self.bot_panel = BotMutePanel(self.i18n)
        bot_card = ModernCard()
        bot_card.addWidget(self.bot_panel)
        return bot_card

    def _setup_overlay_settings_tab(self) -> QScrollArea:
        overlay_card = ModernCard()
        
        self.combo_overlay_theme = NoWheelComboBox()
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_glass"), "glass")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_neon"), "neon")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_card"), "card")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_cyber"), "cyber")
        self.combo_overlay_theme.addItem(self.i18n.get("chat.overlay.theme_minimal"), "minimal")
        self.combo_overlay_theme.currentIndexChanged.connect(self._update_overlay_url)
        
        row_overlay_theme = SettingRow(
            "palette.svg", 
            self.i18n.get("chat.overlay.theme_title"), 
            self.i18n.get("chat.overlay.theme_desc"), 
            self.combo_overlay_theme
        )
        
        font_size_widget = QWidget()
        font_size_layout = QHBoxLayout(font_size_widget)
        font_size_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_overlay_size = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_overlay_size.setRange(10, 32)
        self.slider_overlay_size.setValue(14)
        self.slider_overlay_size.setFixedWidth(140)
        self.lbl_overlay_size = QLabel("14px")
        self.lbl_overlay_size.setFixedWidth(40)
        self.lbl_overlay_size.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.slider_overlay_size.valueChanged.connect(self._on_overlay_size_changed)
        font_size_layout.addWidget(self.slider_overlay_size)
        font_size_layout.addWidget(self.lbl_overlay_size)
        
        row_overlay_size = SettingRow(
            "text-size.svg",
            self.i18n.get("chat.overlay.size_title"),
            self.i18n.get("chat.overlay.size_desc"),
            font_size_widget
        )
        
        fade_widget = QWidget()
        fade_layout = QHBoxLayout(fade_widget)
        fade_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_overlay_fade = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider_overlay_fade.setRange(0, 120)
        self.slider_overlay_fade.setValue(15)
        self.slider_overlay_fade.setFixedWidth(140)
        self.lbl_overlay_fade = QLabel("15s")
        self.lbl_overlay_fade.setFixedWidth(40)
        self.lbl_overlay_fade.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.slider_overlay_fade.valueChanged.connect(self._on_overlay_fade_changed)
        fade_layout.addWidget(self.slider_overlay_fade)
        fade_layout.addWidget(self.lbl_overlay_fade)
        
        row_overlay_fade = SettingRow(
            "stopwatch.svg",
            self.i18n.get("chat.overlay.fade_title"),
            self.i18n.get("chat.overlay.fade_desc"),
            fade_widget
        )
        
        self.sw_overlay_show_bots = ModernSwitch()
        self.sw_overlay_show_bots.setChecked(False)
        self.sw_overlay_show_bots.toggled.connect(self._update_overlay_url)
        
        row_overlay_show_bots = SettingRow(
            "user.svg",
            self.i18n.get("chat.overlay.show_bots_title"),
            self.i18n.get("chat.overlay.show_bots_desc"),
            self.sw_overlay_show_bots
        )
        
        self.sw_overlay_show_time = ModernSwitch()
        self.sw_overlay_show_time.setChecked(False)
        self.sw_overlay_show_time.toggled.connect(self._update_overlay_url)
        
        row_overlay_show_time = SettingRow(
            "clock.svg",
            self.i18n.get("chat.overlay.show_time_title"),
            self.i18n.get("chat.overlay.show_time_desc"),
            self.sw_overlay_show_time
        )
        
        self.btn_copy_overlay_obs = ModernButton(self.i18n.get("common.buttons.copy"), role="action_neutral_border")
        self.btn_copy_overlay_obs.clicked.connect(self._copy_overlay_obs_url)
        
        row_copy_obs = SettingRow(
            "link.svg",
            self.i18n.get("chat.settings.obs_title"),
            self.i18n.get("chat.settings.obs_desc"),
            self.btn_copy_overlay_obs
        )
        
        overlay_card.addWidget(row_overlay_theme)
        overlay_card.addWidget(row_overlay_size)
        overlay_card.addWidget(row_overlay_fade)
        overlay_card.addWidget(row_overlay_show_bots)
        overlay_card.addWidget(row_overlay_show_time)
        
        divider3 = QFrame()
        divider3.setProperty("role", "divider")
        divider3.setFixedHeight(1)
        overlay_card.addWidget(divider3)
        overlay_card.addWidget(row_copy_obs)
        overlay_card.addStretch()
        
        overlay_scroll = QScrollArea()
        overlay_scroll.setWidgetResizable(True)
        overlay_scroll.setFrameShape(QFrame.Shape.NoFrame)
        overlay_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        overlay_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        overlay_scroll.setWidget(overlay_card)
        return overlay_scroll

    def _setup_chat_panel(self) -> ModernCard:
        chat_card = ModernCard()
        chat_card.setMinimumWidth(380)
        chat_card.setMinimumHeight(400) 
        chat_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        lbl_chat_title = QLabel(self.i18n.get("chat.display.title"))
        lbl_chat_title.setProperty("role", "h3")
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setProperty("role", "ConsoleDisplay")

        chat_card.addWidget(lbl_chat_title)
        chat_card.addWidget(self.chat_display)
        return chat_card

    def resizeEvent(self, event):
        super().resizeEvent(event)

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

    @property
    def overlay_theme(self) -> str:
        return self.combo_overlay_theme.currentData() or "glass"

    @property
    def overlay_size(self) -> int:
        return self.slider_overlay_size.value()

    @property
    def overlay_fade(self) -> int:
        return self.slider_overlay_fade.value()

    @property
    def overlay_show_bots(self) -> bool:
        return self.sw_overlay_show_bots.isChecked()

    @property
    def overlay_show_time(self) -> bool:
        return self.sw_overlay_show_time.isChecked()

    def _connect_internal_signals(self):
        self.chk_provider.toggled.connect(self.provider_toggled.emit)
        self.slider_vol.valueChanged.connect(self._on_slider_vol_changed)
        self.combo_lang.currentTextChanged.connect(self.language_filter_changed.emit)
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        self.txt_command.textChanged.connect(self._enforce_prefix_mask)
        self.bot_panel.bot_add_requested.connect(self.bot_add_requested.emit)
        self.bot_panel.bot_remove_requested.connect(self.bot_remove_requested.emit)
        
        controls = [self.chk_tts, self.chk_name, self.chk_command, self.txt_command,
                    self.combo_voice_broadcaster, self.combo_voice_moderator,
                    self.combo_voice_vip, self.combo_voice_subscriber,
                    self.combo_overlay_theme, self.slider_overlay_size,
                    self.slider_overlay_fade, self.sw_overlay_show_bots,
                    self.sw_overlay_show_time]
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

    def set_overlay_settings_ui(self, theme: str, size: int, fade: int, show_bots: bool, show_time: bool):
        self.blockSignals(True)
        self.combo_overlay_theme.blockSignals(True)
        self.slider_overlay_size.blockSignals(True)
        self.slider_overlay_fade.blockSignals(True)
        self.sw_overlay_show_bots.blockSignals(True)
        self.sw_overlay_show_time.blockSignals(True)

        idx = self.combo_overlay_theme.findData(theme)
        if idx != -1:
            self.combo_overlay_theme.setCurrentIndex(idx)
        self.slider_overlay_size.setValue(size)
        self.lbl_overlay_size.setText(f"{size}px")
        self.slider_overlay_fade.setValue(fade)
        self.lbl_overlay_fade.setText("Nunca" if fade == 0 else f"{fade}s")
        self.sw_overlay_show_bots.setChecked(show_bots)
        self.sw_overlay_show_time.setChecked(show_time)

        self.combo_overlay_theme.blockSignals(False)
        self.slider_overlay_size.blockSignals(False)
        self.slider_overlay_fade.blockSignals(False)
        self.sw_overlay_show_bots.blockSignals(False)
        self.sw_overlay_show_time.blockSignals(False)
        self.blockSignals(False)
        
        self._update_overlay_url()

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

    def update_voices(self, voices: list[tuple[str, str]], select_id: str = None, role_voices: dict = None):
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

        for role, combo in role_combos.items():
            combo.blockSignals(True)
            combo.clear()

            default_label = self.i18n.get("chat.roles.default_voice")
            combo.addItem(default_label, userData="")

            target_id = role_voices.get(role, "") if role_voices else ""
            select_idx = 0

            for i, (v_id, v_name) in enumerate(voices):
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

    def append_message(self, user: str, message: str, color: str, timestamp: str = "", is_html: bool = False):
        safe_user = html.escape(user)
        safe_message = message if is_html else html.escape(message)        
        safe_color = color if (color and color.startswith("#") and len(color) <= 7) else COLOR_NEUTRAL_200
        ts_span = f'<span style="color: {COLOR_NEUTRAL_500}; font-size: 0.85em; margin-right: 6px;">[{timestamp}]</span>' if timestamp else ""
        html_msg = f'{ts_span}<b style="color: {safe_color};">{safe_user}:</b> <span style="color: {COLOR_NEUTRAL_200};">{safe_message}</span>'
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
        if validate_trigger_prefix(text):
            self.txt_command.setStyleSheet("")
        else:
            self.txt_command.setStyleSheet("border: 1.5px solid #ff4444;")

    def _on_voice_selected(self, index: int):
        if index >= 0:
            voice_id = self.combo_voice.itemData(index)
            self.voice_changed.emit(voice_id)

    @property
    def chat_overlay_url(self):
        return getattr(self, "_chat_overlay_url", "")

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
        
        base_url = getattr(self, "_chat_overlay_url", "")
        if "?" in base_url:
            base_part, token_part = base_url.split("?", 1)
            self.chat_overlay_full_url = f"{base_part}?{token_part}&theme={theme}&size={size}px&fade={fade}&show_bots={show_bots}&show_time={show_time}"
        else:
            self.chat_overlay_full_url = f"{base_url}?theme={theme}&size={size}px&fade={fade}&show_bots={show_bots}&show_time={show_time}"

    def _on_overlay_size_changed(self, value):
        self.lbl_overlay_size.setText(f"{value}px")
        self._update_overlay_url()

    def _on_overlay_fade_changed(self, value):
        self.lbl_overlay_fade.setText("Nunca" if value == 0 else f"{value}s")
        self._update_overlay_url()

    @Slot()
    def _copy_overlay_obs_url(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        QApplication.clipboard().setText(getattr(self, "chat_overlay_full_url", ""))
        original_text = self.btn_copy_overlay_obs.text()
        self.btn_copy_overlay_obs.setText(self.i18n.get("rewards.obs.copied"))
        self.btn_copy_overlay_obs.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_overlay_copy_btn(original_text))

    def _reset_overlay_copy_btn(self, original_text: str):
        self.btn_copy_overlay_obs.setText(original_text)
        self.btn_copy_overlay_obs.setEnabled(True)