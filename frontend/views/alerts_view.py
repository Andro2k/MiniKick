# frontend\views\alerts_view.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QFileDialog, QStackedWidget, QBoxLayout
)
from backend.models.alert_models import AlertConfig
from frontend.widgets import (
    BaseView, ModernCard, ModernButton, ModernSwitch,
    NoWheelSlider, NoWheelSpinBox, ModernDivider
)
from frontend.common.icons import get_pixmap_colored
from frontend.common.theme import COLOR_GREEN, COLOR_PURPLE

class AlertEventCard(ModernCard):
    config_changed = Signal(object)
    test_requested = Signal(str, str)

    def __init__(self, platform: str, alert_type: str, icon_name: str, i18n, parent=None):
        super().__init__(parent=parent, margin=14, spacing=10)
        self.platform = platform
        self.alert_type = alert_type
        self.i18n = i18n
        self._current_config = AlertConfig(platform=platform, alert_type=alert_type)
        self._is_loading = True
        self._setup_ui(icon_name)

    def _setup_ui(self, icon_name: str):
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        accent_color = COLOR_GREEN if self.platform == "kick" else COLOR_PURPLE
        icon_lbl = QLabel(parent=self)
        icon_lbl.setPixmap(get_pixmap_colored(icon_name, accent_color, size=22))

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        lbl_title = QLabel(self.i18n.get(f"alerts.events.{self.alert_type}"), parent=self)
        lbl_title.setProperty("role", "h3")

        lbl_desc = QLabel(self.i18n.get(f"alerts.events.{self.alert_type}_desc"), parent=self)
        lbl_desc.setProperty("role", "body")

        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_desc)

        self.sw_enabled = ModernSwitch(parent=self)
        self.sw_enabled.setToolTip(self.i18n.get("alerts.fields.active"))
        self.sw_enabled.toggled.connect(self._on_field_changed)

        header_row.addWidget(icon_lbl)
        header_row.addLayout(title_layout, stretch=1)
        header_row.addWidget(self.sw_enabled)

        self.addLayout(header_row)
        self.addWidget(ModernDivider(self))

        template_row = QVBoxLayout()
        template_row.setSpacing(4)
        lbl_template = QLabel(self.i18n.get("alerts.fields.template"), parent=self)
        lbl_template.setProperty("role", "caption")

        self.edit_template = QLineEdit(parent=self)
        self.edit_template.setToolTip(self.i18n.get("alerts.fields.template_hint"))
        self.edit_template.textChanged.connect(self._on_field_changed)

        lbl_template_hint = QLabel(self.i18n.get("alerts.fields.template_hint"), parent=self)
        lbl_template_hint.setProperty("role", "caption")

        template_row.addWidget(lbl_template)
        template_row.addWidget(self.edit_template)
        template_row.addWidget(lbl_template_hint)
        self.addLayout(template_row)

        sound_layout = QVBoxLayout()
        sound_layout.setSpacing(4)
        lbl_sound = QLabel(self.i18n.get("alerts.fields.sound"), parent=self)
        lbl_sound.setProperty("role", "caption")

        sound_input_row = QHBoxLayout()
        sound_input_row.setSpacing(8)
        self.edit_sound = QLineEdit(parent=self)
        self.edit_sound.setPlaceholderText(self.i18n.get("alerts.fields.sound_placeholder"))
        self.edit_sound.textChanged.connect(self._on_field_changed)

        btn_browse_sound = ModernButton(
            text=self.i18n.get("alerts.buttons.browse"),
            role="action_outlined",
            icon_name="folder-open.svg",
            icon_size=14,
            parent=self
        )
        btn_browse_sound.setFixedHeight(32)
        btn_browse_sound.setFixedWidth(110)
        btn_browse_sound.clicked.connect(self._browse_sound)

        sound_input_row.addWidget(self.edit_sound, stretch=1)
        sound_input_row.addWidget(btn_browse_sound)
        sound_layout.addWidget(lbl_sound)
        sound_layout.addLayout(sound_input_row)
        self.addLayout(sound_layout)

        media_layout = QVBoxLayout()
        media_layout.setSpacing(4)
        lbl_media = QLabel(self.i18n.get("alerts.fields.media"), parent=self)
        lbl_media.setProperty("role", "caption")

        media_input_row = QHBoxLayout()
        media_input_row.setSpacing(8)
        self.edit_media = QLineEdit(parent=self)
        self.edit_media.setPlaceholderText(self.i18n.get("alerts.fields.media_placeholder"))
        self.edit_media.textChanged.connect(self._on_field_changed)

        btn_browse_media = ModernButton(
            text=self.i18n.get("alerts.buttons.browse"),
            role="action_outlined",
            icon_name="movie.svg",
            icon_size=14,
            parent=self
        )
        btn_browse_media.setFixedHeight(32)
        btn_browse_media.setFixedWidth(110)
        btn_browse_media.clicked.connect(self._browse_media)

        media_input_row.addWidget(self.edit_media, stretch=1)
        media_input_row.addWidget(btn_browse_media)
        media_layout.addWidget(lbl_media)
        media_layout.addLayout(media_input_row)
        self.addLayout(media_layout)

        params_row = QHBoxLayout()
        params_row.setSpacing(16)

        dur_col = QVBoxLayout()
        dur_col.setSpacing(4)
        lbl_duration = QLabel(self.i18n.get("alerts.fields.duration"), parent=self)
        lbl_duration.setProperty("role", "caption")
        self.spin_duration = NoWheelSpinBox(parent=self)
        self.spin_duration.setRange(1, 60)
        self.spin_duration.setSuffix(" s")
        self.spin_duration.setFixedWidth(100)
        self.spin_duration.valueChanged.connect(self._on_field_changed)
        dur_col.addWidget(lbl_duration)
        dur_col.addWidget(self.spin_duration)

        vol_col = QVBoxLayout()
        vol_col.setSpacing(4)
        lbl_vol_title = QLabel(self.i18n.get("alerts.fields.volume"), parent=self)
        lbl_vol_title.setProperty("role", "caption")
        self.lbl_volume_val = QLabel("80%", parent=self)
        self.lbl_volume_val.setProperty("role", "caption")

        vol_header = QHBoxLayout()
        vol_header.addWidget(lbl_vol_title)
        vol_header.addStretch()
        vol_header.addWidget(self.lbl_volume_val)

        self.slider_volume = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(80)
        self.slider_volume.valueChanged.connect(self._on_volume_changed)

        vol_col.addLayout(vol_header)
        vol_col.addWidget(self.slider_volume)

        params_row.addLayout(dur_col)
        params_row.addLayout(vol_col, stretch=1)
        self.addLayout(params_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        tts_layout = QHBoxLayout()
        tts_layout.setSpacing(8)
        self.sw_tts = ModernSwitch(parent=self)
        self.sw_tts.toggled.connect(self._on_field_changed)
        lbl_tts = QLabel(self.i18n.get("alerts.fields.tts"), parent=self)
        lbl_tts.setProperty("role", "caption")
        tts_layout.addWidget(self.sw_tts)
        tts_layout.addWidget(lbl_tts)

        btn_role = "action_kick" if self.platform == "kick" else "action_twitch"
        self.btn_test = ModernButton(
            text=self.i18n.get("alerts.buttons.test"),
            role=btn_role,
            icon_name="player-play.svg",
            icon_size=15,
            parent=self
        )
        self.btn_test.setFixedHeight(32)
        self.btn_test.setMinimumWidth(130)
        self.btn_test.clicked.connect(self._on_test_clicked)

        action_row.addLayout(tts_layout)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_test)

        self.addLayout(action_row)
        self._is_loading = False

    def load_config(self, cfg: AlertConfig):
        self._is_loading = True
        self._current_config = cfg
        self.sw_enabled.setChecked(cfg.enabled)
        self.edit_template.setText(cfg.text_template)
        self.edit_sound.setText(cfg.sound_path)
        self.edit_media.setText(cfg.media_path)
        self.spin_duration.setValue(max(1, cfg.duration_ms // 1000))
        vol_pct = int(cfg.sound_volume * 100)
        self.slider_volume.setValue(vol_pct)
        self.lbl_volume_val.setText(f"{vol_pct}%")
        self.sw_tts.setChecked(cfg.tts_read)
        self._is_loading = False

    def _on_volume_changed(self, val: int):
        self.lbl_volume_val.setText(f"{val}%")
        self._on_field_changed()

    def _browse_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.get("alerts.fields.sound"),
            "",
            "Audio (*.mp3 *.wav *.ogg);;All Files (*.*)"
        )
        if file_path:
            self.edit_sound.setText(file_path)

    def _browse_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.get("alerts.fields.media"),
            "",
            "Media (*.png *.gif *.webp *.mp4 *.webm);;All Files (*.*)"
        )
        if file_path:
            self.edit_media.setText(file_path)

    def _on_field_changed(self):
        if self._is_loading:
            return
        cfg = AlertConfig(
            platform=self.platform,
            alert_type=self.alert_type,
            enabled=self.sw_enabled.isChecked(),
            sound_path=self.edit_sound.text().strip(),
            media_path=self.edit_media.text().strip(),
            text_template=self.edit_template.text().strip(),
            duration_ms=self.spin_duration.value() * 1000,
            sound_volume=round(self.slider_volume.value() / 100.0, 2),
            tts_read=self.sw_tts.isChecked()
        )
        self._current_config = cfg
        self.config_changed.emit(cfg)

    def _on_test_clicked(self):
        self.test_requested.emit(self.platform, self.alert_type)


class AlertsView(BaseView):
    config_changed = Signal(object)
    test_alert_requested = Signal(str, str)
    copy_url_requested = Signal()
    view_shown = Signal()

    def __init__(self, i18n, alerts_overlay_url: str = "", parent=None):
        super().__init__(
            i18n=i18n,
            title_key="alerts.header.title",
            subtitle_key="alerts.header.subtitle",
            parent=parent
        )
        self.alerts_overlay_url = alerts_overlay_url
        self.cards: dict[tuple[str, str], AlertEventCard] = {}
        self._last_direction = None
        self._setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def _setup_ui(self):
        overlay_card = ModernCard(parent=self, margin=12, spacing=8)

        card_header = QHBoxLayout()
        card_header.setSpacing(8)
        icon_link = QLabel(parent=self)
        icon_link.setPixmap(get_pixmap_colored("link.svg", COLOR_GREEN, size=20))

        lbl_obs_title = QLabel(self.i18n.get("alerts.overlay_card.title"), parent=self)
        lbl_obs_title.setProperty("role", "h3")

        card_header.addWidget(icon_link)
        card_header.addWidget(lbl_obs_title)
        card_header.addStretch()
        overlay_card.addLayout(card_header)

        lbl_obs_desc = QLabel(self.i18n.get("alerts.overlay_card.desc"), parent=self)
        lbl_obs_desc.setProperty("role", "body")
        overlay_card.addWidget(lbl_obs_desc)

        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.edit_overlay_url = QLineEdit(self.alerts_overlay_url, parent=self)
        self.edit_overlay_url.setReadOnly(True)

        self.btn_copy_url = ModernButton(
            text=self.i18n.get("alerts.overlay_card.copy_btn"),
            role="action_accent",
            icon_name="clipboard-text.svg",
            icon_size=15,
            parent=self
        )
        self.btn_copy_url.clicked.connect(self.copy_url_requested.emit)

        url_row.addWidget(self.edit_overlay_url, stretch=1)
        url_row.addWidget(self.btn_copy_url)
        overlay_card.addLayout(url_row)

        self.main_layout.addWidget(overlay_card)
        self.main_layout.addSpacing(8)

        platform_row = QHBoxLayout()
        platform_row.setSpacing(8)

        self.btn_tab_kick = ModernButton(
            text=self.i18n.get("alerts.platforms.kick"),
            role="action_kick",
            icon_name="brand-kick.svg",
            icon_size=16,
            parent=self
        )
        self.btn_tab_kick.setFixedHeight(32)
        self.btn_tab_kick.clicked.connect(lambda: self._switch_platform("kick"))

        self.btn_tab_twitch = ModernButton(
            text=self.i18n.get("alerts.platforms.twitch"),
            role="action_outlined",
            icon_name="brand-twitch.svg",
            icon_size=16,
            parent=self
        )
        self.btn_tab_twitch.setFixedHeight(32)
        self.btn_tab_twitch.clicked.connect(lambda: self._switch_platform("twitch"))

        platform_row.addWidget(self.btn_tab_kick)
        platform_row.addWidget(self.btn_tab_twitch)
        platform_row.addStretch()

        self.main_layout.addLayout(platform_row)
        self.main_layout.addSpacing(8)

        self.stack = QStackedWidget(parent=self)

        kick_page = QWidget()
        kick_page_layout = QVBoxLayout(kick_page)
        kick_page_layout.setContentsMargins(0, 0, 0, 0)
        kick_page_layout.setSpacing(16)

        self.kick_columns = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.kick_columns.setContentsMargins(0, 0, 0, 0)
        self.kick_columns.setSpacing(16)

        kick_col1 = QWidget()
        self.kick_col1_layout = QVBoxLayout(kick_col1)
        self.kick_col1_layout.setContentsMargins(0, 0, 0, 0)
        self.kick_col1_layout.setSpacing(16)
        self.kick_col1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        kick_col2 = QWidget()
        self.kick_col2_layout = QVBoxLayout(kick_col2)
        self.kick_col2_layout.setContentsMargins(0, 0, 0, 0)
        self.kick_col2_layout.setSpacing(16)
        self.kick_col2_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.kick_columns.addWidget(kick_col1, stretch=1)
        self.kick_columns.addWidget(kick_col2, stretch=1)
        kick_page_layout.addLayout(self.kick_columns)

        kick_col1_events = [
            ("follow", "user-check.svg"),
            ("subscription", "crown.svg"),
            ("resub", "star.svg"),
        ]
        kick_col2_events = [
            ("sub_gift", "box-multiple-2.svg"),
            ("raid", "users.svg"),
        ]
        for alert_type, icon_name in kick_col1_events:
            card = AlertEventCard("kick", alert_type, icon_name, self.i18n, parent=self)
            card.config_changed.connect(self.config_changed.emit)
            card.test_requested.connect(self.test_alert_requested.emit)
            self.kick_col1_layout.addWidget(card)
            self.cards[("kick", alert_type)] = card

        for alert_type, icon_name in kick_col2_events:
            card = AlertEventCard("kick", alert_type, icon_name, self.i18n, parent=self)
            card.config_changed.connect(self.config_changed.emit)
            card.test_requested.connect(self.test_alert_requested.emit)
            self.kick_col2_layout.addWidget(card)
            self.cards[("kick", alert_type)] = card

        self.stack.addWidget(kick_page)

        twitch_page = QWidget()
        twitch_page_layout = QVBoxLayout(twitch_page)
        twitch_page_layout.setContentsMargins(0, 0, 0, 0)
        twitch_page_layout.setSpacing(16)

        self.twitch_columns = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.twitch_columns.setContentsMargins(0, 0, 0, 0)
        self.twitch_columns.setSpacing(16)

        twitch_col1 = QWidget()
        self.twitch_col1_layout = QVBoxLayout(twitch_col1)
        self.twitch_col1_layout.setContentsMargins(0, 0, 0, 0)
        self.twitch_col1_layout.setSpacing(16)
        self.twitch_col1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        twitch_col2 = QWidget()
        self.twitch_col2_layout = QVBoxLayout(twitch_col2)
        self.twitch_col2_layout.setContentsMargins(0, 0, 0, 0)
        self.twitch_col2_layout.setSpacing(16)
        self.twitch_col2_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.twitch_columns.addWidget(twitch_col1, stretch=1)
        self.twitch_columns.addWidget(twitch_col2, stretch=1)
        twitch_page_layout.addLayout(self.twitch_columns)

        twitch_col1_events = [
            ("follow", "user-check.svg"),
            ("subscription", "crown.svg"),
            ("resub", "star.svg"),
        ]
        twitch_col2_events = [
            ("sub_gift", "box-multiple-2.svg"),
            ("raid", "users.svg"),
            ("cheer", "chart-bubble.svg"),
        ]
        for alert_type, icon_name in twitch_col1_events:
            card = AlertEventCard("twitch", alert_type, icon_name, self.i18n, parent=self)
            card.config_changed.connect(self.config_changed.emit)
            card.test_requested.connect(self.test_alert_requested.emit)
            self.twitch_col1_layout.addWidget(card)
            self.cards[("twitch", alert_type)] = card

        for alert_type, icon_name in twitch_col2_events:
            card = AlertEventCard("twitch", alert_type, icon_name, self.i18n, parent=self)
            card.config_changed.connect(self.config_changed.emit)
            card.test_requested.connect(self.test_alert_requested.emit)
            self.twitch_col2_layout.addWidget(card)
            self.cards[("twitch", alert_type)] = card

        self.stack.addWidget(twitch_page)

        self.main_layout.addWidget(self.stack)

    def _switch_platform(self, platform: str):
        if platform == "kick":
            self.btn_tab_kick.setProperty("role", "action_kick")
            self.btn_tab_twitch.setProperty("role", "action_outlined")
            self.stack.setCurrentIndex(0)
        else:
            self.btn_tab_kick.setProperty("role", "action_outlined")
            self.btn_tab_twitch.setProperty("role", "action_twitch")
            self.stack.setCurrentIndex(1)

        for btn in (self.btn_tab_kick, self.btn_tab_twitch):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        direction = QBoxLayout.Direction.TopToBottom if width < 920 else QBoxLayout.Direction.LeftToRight
        if direction != self._last_direction:
            self._last_direction = direction
            if hasattr(self, 'kick_columns') and hasattr(self, 'twitch_columns'):
                for col_layout in (self.kick_columns, self.twitch_columns):
                    col_layout.setDirection(direction)
                    if direction == QBoxLayout.Direction.TopToBottom:
                        col_layout.setStretch(0, 0)
                        col_layout.setStretch(1, 0)
                    else:
                        col_layout.setStretch(0, 1)
                        col_layout.setStretch(1, 1)

    def set_overlay_url(self, url: str):
        self.alerts_overlay_url = url
        self.edit_overlay_url.setText(url)

    def populate_configs(self, configs: dict[tuple[str, str], AlertConfig]):
        for (plat, a_type), card in self.cards.items():
            if (plat, a_type) in configs:
                card.load_config(configs[(plat, a_type)])
