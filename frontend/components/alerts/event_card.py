# frontend\components\alerts\event_card.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from backend.models import AlertConfig
from frontend.widgets import (
    ModernCard, ModernButton, ModernSwitch,
    NoWheelSlider, NoWheelSpinBox, ModernDivider
)
from frontend.common import get_pixmap_colored, COLOR_GREEN, COLOR_PURPLE

class AlertEventCard(QWidget):
    config_changed = Signal(object)
    save_requested = Signal(object)
    test_requested = Signal(str, str)

    def __init__(self, platform: str, alert_type: str, icon_name: str, i18n, parent=None):
        super().__init__(parent=parent)
        self.platform = platform
        self.alert_type = alert_type
        self.icon_name = icon_name
        self.i18n = i18n
        self._saved_config = AlertConfig(platform=platform, alert_type=alert_type)
        self._current_config = AlertConfig(platform=platform, alert_type=alert_type)
        self._is_loading = True
        self._is_dirty = False

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        header_card = ModernCard(parent=self, margin=12, spacing=10)
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(10)

        top_info_row = QHBoxLayout()
        top_info_row.setSpacing(10)

        accent_color = COLOR_GREEN if self.platform == "kick" else COLOR_PURPLE
        self.icon_lbl = QLabel(parent=self)
        self.icon_lbl.setPixmap(get_pixmap_colored(self.icon_name, accent_color, size=24))

        platform_name = self.i18n.get(f"alerts.platforms.{self.platform}")
        event_name = self.i18n.get(f"alerts.events.{self.alert_type}")

        lbl_header_title = QLabel(f"{platform_name} • {event_name}", parent=self)
        lbl_header_title.setProperty("role", "h3")
        lbl_header_title.setWordWrap(True)

        top_info_row.addWidget(self.icon_lbl)
        top_info_row.addWidget(lbl_header_title, stretch=1)

        btn_role = "action_kick" if self.platform == "kick" else "action_twitch"
        self.btn_test = ModernButton(
            text=self.i18n.get("alerts.buttons.test"),
            role="action_outlined",
            icon_name="player-play.svg",
            icon_size=15,
            parent=self
        )
        self.btn_test.setFixedHeight(32)
        self.btn_test.clicked.connect(self._on_test_clicked)
        top_info_row.addWidget(self.btn_test)

        header_vbox.addLayout(top_info_row)

        actions_row = QHBoxLayout()
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(8)

        self.lbl_dirty = QLabel(self.i18n.get("alerts.status.unsaved"), parent=self)
        self.lbl_dirty.setProperty("role", "caption")
        self.lbl_dirty.setProperty("state", "warning")
        self.lbl_dirty.setWordWrap(True)
        self.lbl_dirty.setVisible(False)

        self.btn_discard = ModernButton(
            text=self.i18n.get("alerts.buttons.discard"),
            role="action_outlined",
            icon_name="x.svg",
            icon_size=14,
            parent=self
        )
        self.btn_discard.setFixedHeight(32)
        self.btn_discard.setEnabled(False)
        self.btn_discard.clicked.connect(self._discard_changes)

        self.btn_save = ModernButton(
            text=self.i18n.get("alerts.buttons.save"),
            role=btn_role,
            icon_name="check.svg",
            icon_size=15,
            parent=self
        )
        self.btn_save.setFixedHeight(32)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save_changes)

        actions_row.addWidget(self.lbl_dirty, stretch=1)
        actions_row.addWidget(self.btn_discard)
        actions_row.addWidget(self.btn_save)

        header_vbox.addLayout(actions_row)
        header_card.addLayout(header_vbox)
        main_layout.addWidget(header_card)

        card_general = ModernCard(parent=self, margin=12, spacing=10)

        sec_gen_header = QHBoxLayout()
        sec_gen_header.setSpacing(8)
        lbl_sec_gen_icon = QLabel(parent=self)
        lbl_sec_gen_icon.setPixmap(get_pixmap_colored("settings.svg", accent_color, size=18))
        lbl_sec_gen_title = QLabel(self.i18n.get("alerts.sections.general"), parent=self)
        lbl_sec_gen_title.setProperty("role", "h3")
        sec_gen_header.addWidget(lbl_sec_gen_icon)
        sec_gen_header.addWidget(lbl_sec_gen_title)
        sec_gen_header.addStretch()

        card_general.addLayout(sec_gen_header)
        card_general.addWidget(ModernDivider(self))

        sw_row = QHBoxLayout()
        sw_row.setSpacing(10)
        lbl_sw_active = QLabel(self.i18n.get("alerts.fields.active"), parent=self)
        lbl_sw_active.setProperty("role", "body")
        lbl_sw_active.setWordWrap(True)
        self.sw_enabled = ModernSwitch(parent=self)
        self.sw_enabled.toggled.connect(self._on_field_changed)
        sw_row.addWidget(lbl_sw_active, stretch=1)
        sw_row.addWidget(self.sw_enabled)
        card_general.addLayout(sw_row)

        template_col = QVBoxLayout()
        template_col.setSpacing(4)
        lbl_template = QLabel(self.i18n.get("alerts.fields.template"), parent=self)
        lbl_template.setProperty("role", "caption")
        lbl_template.setWordWrap(True)

        self.edit_template = QLineEdit(parent=self)
        self.edit_template.setToolTip(self.i18n.get("alerts.fields.template_hint"))
        self.edit_template.textChanged.connect(self._on_field_changed)

        lbl_template_hint = QLabel(self.i18n.get("alerts.fields.template_hint"), parent=self)
        lbl_template_hint.setProperty("role", "caption")
        lbl_template_hint.setWordWrap(True)

        template_col.addWidget(lbl_template)
        template_col.addWidget(self.edit_template)
        template_col.addWidget(lbl_template_hint)
        card_general.addLayout(template_col)

        params_row = QHBoxLayout()
        params_row.setSpacing(16)

        dur_col = QVBoxLayout()
        dur_col.setSpacing(4)
        lbl_duration = QLabel(self.i18n.get("alerts.fields.duration"), parent=self)
        lbl_duration.setProperty("role", "caption")
        lbl_duration.setWordWrap(True)
        self.spin_duration = NoWheelSpinBox(parent=self)
        self.spin_duration.setRange(1, 60)
        self.spin_duration.setSuffix(" s")
        self.spin_duration.setFixedWidth(80)
        self.spin_duration.valueChanged.connect(self._on_field_changed)
        dur_col.addWidget(lbl_duration)
        dur_col.addWidget(self.spin_duration)

        tts_col = QVBoxLayout()
        tts_col.setSpacing(4)
        lbl_tts_title = QLabel(self.i18n.get("alerts.fields.tts"), parent=self)
        lbl_tts_title.setProperty("role", "caption")
        lbl_tts_title.setWordWrap(True)
        self.sw_tts = ModernSwitch(parent=self)
        self.sw_tts.toggled.connect(self._on_field_changed)
        tts_col.addWidget(lbl_tts_title)
        tts_col.addWidget(self.sw_tts)

        params_row.addLayout(dur_col)
        params_row.addLayout(tts_col)
        params_row.addStretch(1)
        card_general.addLayout(params_row)

        main_layout.addWidget(card_general)

        card_media = ModernCard(parent=self, margin=12, spacing=10)

        sec_media_header = QHBoxLayout()
        sec_media_header.setSpacing(8)
        lbl_sec_media_icon = QLabel(parent=self)
        lbl_sec_media_icon.setPixmap(get_pixmap_colored("volume.svg", accent_color, size=18))
        lbl_sec_media_title = QLabel(self.i18n.get("alerts.sections.media"), parent=self)
        lbl_sec_media_title.setProperty("role", "h3")
        sec_media_header.addWidget(lbl_sec_media_icon)
        sec_media_header.addWidget(lbl_sec_media_title)
        sec_media_header.addStretch()

        card_media.addLayout(sec_media_header)
        card_media.addWidget(ModernDivider(self))

        sound_layout = QVBoxLayout()
        sound_layout.setSpacing(4)
        lbl_sound = QLabel(self.i18n.get("alerts.fields.sound"), parent=self)
        lbl_sound.setProperty("role", "caption")
        lbl_sound.setWordWrap(True)

        sound_input_row = QHBoxLayout()
        sound_input_row.setSpacing(8)
        self.edit_sound = QLineEdit(parent=self)
        self.edit_sound.setMinimumWidth(0)
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
        btn_browse_sound.clicked.connect(self._browse_sound)

        sound_input_row.addWidget(self.edit_sound, stretch=1)
        sound_input_row.addWidget(btn_browse_sound)
        sound_layout.addWidget(lbl_sound)
        sound_layout.addLayout(sound_input_row)
        card_media.addLayout(sound_layout)

        vol_col = QVBoxLayout()
        vol_col.setSpacing(4)
        lbl_vol_title = QLabel(self.i18n.get("alerts.fields.volume"), parent=self)
        lbl_vol_title.setProperty("role", "caption")
        lbl_vol_title.setWordWrap(True)
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
        card_media.addLayout(vol_col)

        media_layout = QVBoxLayout()
        media_layout.setSpacing(4)
        lbl_media = QLabel(self.i18n.get("alerts.fields.media"), parent=self)
        lbl_media.setProperty("role", "caption")
        lbl_media.setWordWrap(True)

        media_input_row = QHBoxLayout()
        media_input_row.setSpacing(8)
        self.edit_media = QLineEdit(parent=self)
        self.edit_media.setMinimumWidth(0)
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
        btn_browse_media.clicked.connect(self._browse_media)

        media_input_row.addWidget(self.edit_media, stretch=1)
        media_input_row.addWidget(btn_browse_media)
        media_layout.addWidget(lbl_media)
        media_layout.addLayout(media_input_row)
        card_media.addLayout(media_layout)

        main_layout.addWidget(card_media)
        main_layout.addStretch()

        self._is_loading = False

    def load_config(self, cfg: AlertConfig):
        self._is_loading = True
        self._saved_config = cfg
        self._current_config = AlertConfig(
            platform=cfg.platform,
            alert_type=cfg.alert_type,
            enabled=cfg.enabled,
            sound_path=cfg.sound_path,
            media_path=cfg.media_path,
            text_template=cfg.text_template,
            duration_ms=cfg.duration_ms,
            sound_volume=cfg.sound_volume,
            tts_read=cfg.tts_read,
        )
        self.sw_enabled.setChecked(cfg.enabled)
        self.edit_template.setText(cfg.text_template)
        self.edit_sound.setText(cfg.sound_path)
        self.edit_media.setText(cfg.media_path)
        self.spin_duration.setValue(max(1, cfg.duration_ms // 1000))
        vol_pct = int(cfg.sound_volume * 100)
        self.slider_volume.setValue(vol_pct)
        self.lbl_volume_val.setText(f"{vol_pct}%")
        self.sw_tts.setChecked(cfg.tts_read)

        self._is_dirty = False
        self.btn_save.setEnabled(False)
        self.btn_discard.setEnabled(False)
        self.lbl_dirty.setVisible(False)
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

        dirty = False
        if self._saved_config:
            dirty = (
                cfg.enabled != self._saved_config.enabled or
                cfg.sound_path != self._saved_config.sound_path or
                cfg.media_path != self._saved_config.media_path or
                cfg.text_template != self._saved_config.text_template or
                cfg.duration_ms != self._saved_config.duration_ms or
                cfg.sound_volume != self._saved_config.sound_volume or
                cfg.tts_read != self._saved_config.tts_read
            )

        self._is_dirty = dirty
        self.btn_save.setEnabled(dirty)
        self.btn_discard.setEnabled(dirty)
        self.lbl_dirty.setVisible(dirty)

        self.config_changed.emit(cfg)

    def _save_changes(self):
        self._saved_config = AlertConfig(
            platform=self._current_config.platform,
            alert_type=self._current_config.alert_type,
            enabled=self._current_config.enabled,
            sound_path=self._current_config.sound_path,
            media_path=self._current_config.media_path,
            text_template=self._current_config.text_template,
            duration_ms=self._current_config.duration_ms,
            sound_volume=self._current_config.sound_volume,
            tts_read=self._current_config.tts_read,
        )
        self._is_dirty = False
        self.btn_save.setEnabled(False)
        self.btn_discard.setEnabled(False)
        self.lbl_dirty.setVisible(False)
        self.save_requested.emit(self._saved_config)

    def _discard_changes(self):
        if self._saved_config:
            self.load_config(self._saved_config)

    def _on_test_clicked(self):
        self.test_requested.emit(self.platform, self.alert_type)
