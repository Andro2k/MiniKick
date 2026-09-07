# frontend\components\alerts\event_card.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize

@dataclass
class AlertConfigData:
    platform: str
    alert_type: str
    enabled: bool = True
    sound_path: str = ""
    media_path: str = ""
    text_template: str = "{user}"
    duration_ms: int = 5000
    sound_volume: float = 0.8
    tts_read: bool = False
    layout: str = "above"
    style: str = "compact"
from frontend.widgets import (
    ModernCard, ModernButton, ModernSwitch,
    NoWheelSlider, NoWheelSpinBox, ModernDivider,
    ModernSegmentedControl, NoWheelComboBox, SettingRow,
    create_badge, ClearableLineEdit
)
from frontend.common import (
    get_pixmap_colored, COLOR_GREEN, COLOR_PURPLE, COLOR_NEUTRAL_400,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    MARGIN_NONE, MARGIN_XS, MARGIN_H_XS
)
from .alert_mockup import AlertOverlayMockupWidget

class AlertEventCard(QWidget):
    config_changed = Signal(object)
    save_requested = Signal(object)
    test_requested = Signal(str, str)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def __init__(self, platform: str, alert_type: str, icon_name: str, i18n, parent=None):
        super().__init__(parent=parent)
        self.platform = platform
        self.alert_type = alert_type
        self.icon_name = icon_name
        self.i18n = i18n
        self._config_cls = AlertConfigData
        self._saved_config = self._config_cls(platform=platform, alert_type=alert_type)
        self._current_config = self._config_cls(platform=platform, alert_type=alert_type)
        self._is_loading = True
        self._is_dirty = False
        self._platform_connected = True

        self._setup_ui()
        self._is_loading = False

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*MARGIN_NONE)
        main_layout.setSpacing(SPACING_MD)

        accent_color = COLOR_GREEN if self.platform == "kick" else COLOR_PURPLE
        btn_role = "action_kick" if self.platform == "kick" else "action_twitch"

        header_card = ModernCard(parent=self, margin=SPACING_MD, spacing=SPACING_SM)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(*MARGIN_NONE)
        header_row.setSpacing(SPACING_MD)

        self.icon_lbl = QLabel(parent=self)
        self.icon_lbl.setPixmap(get_pixmap_colored(self.icon_name, accent_color, size=20))

        platform_name = self.i18n.get(f"alerts.platforms.{self.platform}")
        event_name = self.i18n.get(f"alerts.events.{self.alert_type}")

        lbl_header_title = QLabel(f"{platform_name} • {event_name}", parent=self)
        lbl_header_title.setProperty("role", "h3")

        self.badge_offline = create_badge(self.i18n.get("alerts.status.disconnected"), state="warning")
        self.badge_offline.setVisible(False)

        self.lbl_dirty = QLabel(self.i18n.get("alerts.status.unsaved"), parent=self)
        self.lbl_dirty.setProperty("role", "caption")
        self.lbl_dirty.setProperty("state", "warning")
        self.lbl_dirty.setVisible(False)

        header_row.addWidget(self.icon_lbl)
        header_row.addWidget(lbl_header_title)
        header_row.addWidget(self.badge_offline)
        header_row.addWidget(self.lbl_dirty)
        header_row.addStretch(1)

        self.btn_discard = ModernButton(
            text=self.i18n.get("alerts.buttons.discard"),
            role="action_outlined",
            icon_name="x.svg",
            icon_size=13,
            parent=self
        )
        self.btn_discard.setEnabled(False)
        self.btn_discard.clicked.connect(self._discard_changes)

        self.btn_save = ModernButton(
            text=self.i18n.get("alerts.buttons.save"),
            role=btn_role,
            icon_name="check.svg",
            icon_size=14,
            parent=self
        )
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save_changes)

        self.btn_test = ModernButton(
            text=self.i18n.get("alerts.buttons.test"),
            role="action_outlined",
            icon_name="player-play.svg",
            icon_size=14,
            parent=self
        )
        self.btn_test.clicked.connect(self._on_test_clicked)

        header_row.addWidget(self.btn_discard)
        header_row.addWidget(self.btn_save)
        header_row.addWidget(self.btn_test)

        header_card.addLayout(header_row)
        main_layout.addWidget(header_card)

        card_appearance = ModernCard(parent=self, margin=SPACING_LG, spacing=SPACING_MD)

        sec_app_header = QHBoxLayout()
        sec_app_header.setSpacing(SPACING_MD)
        lbl_sec_app_icon = QLabel(parent=self)
        lbl_sec_app_icon.setPixmap(get_pixmap_colored("palette.svg", COLOR_NEUTRAL_400, size=16))
        lbl_sec_app_title = QLabel(self.i18n.get("alerts.sections.appearance"), parent=self)
        lbl_sec_app_title.setProperty("role", "h3")
        sec_app_header.addWidget(lbl_sec_app_icon)
        sec_app_header.addWidget(lbl_sec_app_title)
        sec_app_header.addStretch()

        card_appearance.addLayout(sec_app_header)
        card_appearance.addWidget(ModernDivider(self))

        body_row = QHBoxLayout()
        body_row.setContentsMargins(*MARGIN_NONE)
        body_row.setSpacing(SPACING_LG)

        col_controls = QVBoxLayout()
        col_controls.setContentsMargins(*MARGIN_NONE)
        col_controls.setSpacing(SPACING_SM)

        self.seg_layout = ModernSegmentedControl(self)
        self.seg_layout.add_option("above", "arrows-vertical.svg", self.i18n.get("alerts.layout.above"))
        self.seg_layout.add_option("side", "arrows-horizontal.svg", self.i18n.get("alerts.layout.side"))
        self.seg_layout.add_option("overlay", "box-multiple-2.svg", self.i18n.get("alerts.layout.overlay"))
        self.seg_layout.value_changed.connect(lambda _: self._on_field_changed())

        row_layout = SettingRow(
            "arrows-sort.svg",
            self.i18n.get("alerts.layout.title"),
            self.i18n.get("alerts.layout.desc"),
            self.seg_layout,
            icon_color=COLOR_NEUTRAL_400,
            parent=self
        )
        col_controls.addWidget(row_layout)

        self.combo_style = NoWheelComboBox(self)
        self.combo_style.addItem(self.i18n.get("alerts.style.compact"), "compact")
        self.combo_style.addItem(self.i18n.get("alerts.style.glass"), "glass")
        self.combo_style.addItem(self.i18n.get("alerts.style.minimal"), "minimal")
        self.combo_style.currentIndexChanged.connect(lambda _: self._on_field_changed())

        row_style = SettingRow(
            "adjustments.svg",
            self.i18n.get("alerts.style.title"),
            self.i18n.get("alerts.style.desc"),
            self.combo_style,
            icon_color=COLOR_NEUTRAL_400,
            parent=self
        )
        col_controls.addWidget(row_style)
        col_controls.addStretch()

        col_preview = QVBoxLayout()
        col_preview.setContentsMargins(*MARGIN_NONE)
        col_preview.setSpacing(SPACING_XS)

        lbl_preview = QLabel(self.i18n.get("alerts.preview.title"), parent=self)
        lbl_preview.setProperty("role", "caption")
        col_preview.addWidget(lbl_preview)

        self.mockup_widget = AlertOverlayMockupWidget(self.i18n, parent=self)
        col_preview.addWidget(self.mockup_widget)
        col_preview.addStretch()

        body_row.addLayout(col_controls, stretch=1)
        body_row.addLayout(col_preview, stretch=1)

        card_appearance.addLayout(body_row)
        main_layout.addWidget(card_appearance)

        card_config = ModernCard(parent=self, margin=SPACING_LG, spacing=SPACING_MD)

        sec_cfg_header = QHBoxLayout()
        sec_cfg_header.setSpacing(SPACING_MD)
        lbl_sec_cfg_icon = QLabel(parent=self)
        lbl_sec_cfg_icon.setPixmap(get_pixmap_colored("settings.svg", COLOR_NEUTRAL_400, size=16))
        lbl_sec_cfg_title = QLabel(self.i18n.get("alerts.sections.general"), parent=self)
        lbl_sec_cfg_title.setProperty("role", "h3")
        sec_cfg_header.addWidget(lbl_sec_cfg_icon)
        sec_cfg_header.addWidget(lbl_sec_cfg_title)
        sec_cfg_header.addStretch()

        card_config.addLayout(sec_cfg_header)
        card_config.addWidget(ModernDivider(self))

        quick_strip = QHBoxLayout()
        quick_strip.setContentsMargins(*MARGIN_XS)
        quick_strip.setSpacing(SPACING_XL)

        active_box = QHBoxLayout()
        active_box.setSpacing(SPACING_MD)
        lbl_sw_active = QLabel(self.i18n.get("alerts.fields.active"), parent=self)
        lbl_sw_active.setProperty("role", "body")
        self.sw_enabled = ModernSwitch(parent=self)
        self.sw_enabled.toggled.connect(self._on_field_changed)
        active_box.addWidget(lbl_sw_active)
        active_box.addWidget(self.sw_enabled)
        quick_strip.addLayout(active_box)

        dur_box = QHBoxLayout()
        dur_box.setSpacing(SPACING_MD)
        lbl_duration = QLabel(self.i18n.get("alerts.fields.duration"), parent=self)
        lbl_duration.setProperty("role", "caption")
        self.spin_duration = NoWheelSpinBox(parent=self)
        self.spin_duration.setRange(1, 60)
        self.spin_duration.setSuffix(" s")
        self.spin_duration.valueChanged.connect(self._on_field_changed)
        dur_box.addWidget(lbl_duration)
        dur_box.addWidget(self.spin_duration)
        quick_strip.addLayout(dur_box)

        tts_box = QHBoxLayout()
        tts_box.setSpacing(SPACING_MD)
        lbl_tts_title = QLabel(self.i18n.get("alerts.fields.tts"), parent=self)
        lbl_tts_title.setProperty("role", "caption")
        self.sw_tts = ModernSwitch(parent=self)
        self.sw_tts.toggled.connect(self._on_field_changed)
        tts_box.addWidget(lbl_tts_title)
        tts_box.addWidget(self.sw_tts)
        quick_strip.addLayout(tts_box)

        quick_strip.addStretch(1)
        card_config.addLayout(quick_strip)
        card_config.addWidget(ModernDivider(self))

        template_col = QVBoxLayout()
        template_col.setContentsMargins(*MARGIN_H_XS)
        template_col.setSpacing(SPACING_XS)

        lbl_template = QLabel(self.i18n.get("alerts.fields.template"), parent=self)
        lbl_template.setProperty("role", "caption")

        self.edit_template = ClearableLineEdit(parent=self)
        self.edit_template.setToolTip(self.i18n.get("alerts.fields.template_hint"))
        self.edit_template.textChanged.connect(self._on_field_changed)

        lbl_template_hint = QLabel(self.i18n.get("alerts.fields.template_hint"), parent=self)
        lbl_template_hint.setProperty("role", "caption")
        lbl_template_hint.setWordWrap(True)

        template_col.addWidget(lbl_template)
        template_col.addWidget(self.edit_template)
        template_col.addWidget(lbl_template_hint)
        card_config.addLayout(template_col)
        card_config.addWidget(ModernDivider(self))

        media_row = QHBoxLayout()
        media_row.setContentsMargins(*MARGIN_H_XS)
        media_row.setSpacing(SPACING_XL)

        col_video = QVBoxLayout()
        col_video.setSpacing(SPACING_SM)

        lbl_media = QLabel(self.i18n.get("alerts.fields.media"), parent=self)
        lbl_media.setProperty("role", "caption")

        media_input_row = QHBoxLayout()
        media_input_row.setSpacing(SPACING_SM)
        self.edit_media = ClearableLineEdit(placeholder=self.i18n.get("alerts.fields.media_placeholder"), parent=self)
        self.edit_media.setMinimumWidth(0)
        self.edit_media.textChanged.connect(self._on_field_changed)

        btn_browse_media = ModernButton(
            text=self.i18n.get("alerts.buttons.browse"),
            role="action_outlined",
            icon_name="movie.svg",
            icon_size=14,
            parent=self
        )
        btn_browse_media.clicked.connect(self._browse_media)

        media_input_row.addWidget(self.edit_media, stretch=1)
        media_input_row.addWidget(btn_browse_media)

        col_video.addWidget(lbl_media)
        col_video.addLayout(media_input_row)
        col_video.addStretch()

        col_audio = QVBoxLayout()
        col_audio.setSpacing(SPACING_SM)

        lbl_sound = QLabel(self.i18n.get("alerts.fields.sound"), parent=self)
        lbl_sound.setProperty("role", "caption")

        sound_input_row = QHBoxLayout()
        sound_input_row.setSpacing(SPACING_SM)
        self.edit_sound = ClearableLineEdit(placeholder=self.i18n.get("alerts.fields.sound_placeholder"), parent=self)
        self.edit_sound.setMinimumWidth(0)
        self.edit_sound.textChanged.connect(self._on_field_changed)

        btn_browse_sound = ModernButton(
            text=self.i18n.get("alerts.buttons.browse"),
            role="action_outlined",
            icon_name="folder-open.svg",
            icon_size=14,
            parent=self
        )
        btn_browse_sound.clicked.connect(self._browse_sound)

        sound_input_row.addWidget(self.edit_sound, stretch=1)
        sound_input_row.addWidget(btn_browse_sound)

        col_audio.addWidget(lbl_sound)
        col_audio.addLayout(sound_input_row)

        vol_header = QHBoxLayout()
        vol_header.setSpacing(SPACING_SM)
        lbl_vol_title = QLabel(self.i18n.get("alerts.fields.volume"), parent=self)
        lbl_vol_title.setProperty("role", "caption")
        self.lbl_volume_val = QLabel("80%", parent=self)
        self.lbl_volume_val.setProperty("role", "caption")

        self.slider_volume = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(80)
        self.slider_volume.valueChanged.connect(self._on_volume_changed)

        vol_header.addWidget(lbl_vol_title)
        vol_header.addWidget(self.slider_volume, stretch=1)
        vol_header.addWidget(self.lbl_volume_val)

        col_audio.addLayout(vol_header)
        col_audio.addStretch()

        media_row.addLayout(col_video, stretch=1)
        media_row.addLayout(col_audio, stretch=1)
        card_config.addLayout(media_row)

        main_layout.addWidget(card_config)
        main_layout.addStretch()

        self._is_loading = False

    def _update_mockup(self):
        if hasattr(self, "mockup_widget") and hasattr(self, "seg_layout") and hasattr(self, "combo_style"):
            layout_val = self.seg_layout.current_value() or "above"
            style_val = self.combo_style.currentData() or "compact"
            self.mockup_widget.set_configuration(
                platform=self.platform,
                alert_type=self.alert_type,
                layout=layout_val,
                style=style_val,
                text_template=self.edit_template.text().strip(),
                media_path=self.edit_media.text().strip()
            )

    def _create_config(self, **kwargs):
        cls = self._config_cls or AlertConfigData
        try:
            return cls(**kwargs)
        except TypeError:
            return AlertConfigData(**kwargs)

    def load_config(self, cfg: Any):
        self._is_loading = True
        self._config_cls = cfg.__class__
        self._saved_config = cfg
        self._current_config = self._create_config(
            platform=cfg.platform,
            alert_type=cfg.alert_type,
            enabled=cfg.enabled,
            sound_path=cfg.sound_path,
            media_path=cfg.media_path,
            text_template=cfg.text_template,
            duration_ms=cfg.duration_ms,
            sound_volume=cfg.sound_volume,
            tts_read=cfg.tts_read,
            layout=getattr(cfg, "layout", "above") or "above",
            style=getattr(cfg, "style", "compact") or "compact",
        )
        self.sw_enabled.setChecked(cfg.enabled)
        self.edit_template.setText(cfg.text_template)
        self.edit_sound.setText(cfg.sound_path)
        self.edit_media.setText(cfg.media_path)
        self.btn_clear_sound.setEnabled(bool(cfg.sound_path))
        self.btn_clear_media.setEnabled(bool(cfg.media_path))
        self.spin_duration.setValue(max(1, cfg.duration_ms // 1000))
        vol_pct = int(cfg.sound_volume * 100)
        self.slider_volume.setValue(vol_pct)
        self.lbl_volume_val.setText(f"{vol_pct}%")
        self.sw_tts.setChecked(cfg.tts_read)

        layout_val = getattr(cfg, "layout", "above") or "above"
        self.seg_layout.set_current_value(layout_val)

        style_val = getattr(cfg, "style", "compact") or "compact"
        idx = self.combo_style.findData(style_val)
        if idx >= 0:
            self.combo_style.setCurrentIndex(idx)

        self._update_mockup()

        self._is_dirty = False
        self.btn_save.setEnabled(False)
        self.btn_discard.setEnabled(False)
        self.lbl_dirty.setVisible(False)
        self._is_loading = False

    def _on_volume_changed(self, val: int):
        self.lbl_volume_val.setText(f"{val}%")
        self._on_field_changed()

    def _clear_sound(self):
        self.edit_sound.clear()

    def _clear_media(self):
        self.edit_media.clear()

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
            self.i18n.get("alerts.fields.media_filter")
        )
        if file_path:
            self.edit_media.setText(file_path)

    def _on_field_changed(self):
        if self._is_loading:
            return

        layout_val = self.seg_layout.current_value() or "above"
        style_val = self.combo_style.currentData() or "compact"

        cfg = self._create_config(
            platform=self.platform,
            alert_type=self.alert_type,
            enabled=self.sw_enabled.isChecked(),
            sound_path=self.edit_sound.text().strip(),
            media_path=self.edit_media.text().strip(),
            text_template=self.edit_template.text().strip(),
            duration_ms=self.spin_duration.value() * 1000,
            sound_volume=round(self.slider_volume.value() / 100.0, 2),
            tts_read=self.sw_tts.isChecked(),
            layout=layout_val,
            style=style_val
        )
        self._current_config = cfg

        self._update_mockup()

        dirty = False
        if self._saved_config:
            dirty = (
                cfg.enabled != self._saved_config.enabled or
                cfg.sound_path != self._saved_config.sound_path or
                cfg.media_path != self._saved_config.media_path or
                cfg.text_template != self._saved_config.text_template or
                cfg.duration_ms != self._saved_config.duration_ms or
                cfg.sound_volume != self._saved_config.sound_volume or
                cfg.tts_read != self._saved_config.tts_read or
                cfg.layout != getattr(self._saved_config, "layout", "above") or
                cfg.style != getattr(self._saved_config, "style", "compact")
            )

        self._is_dirty = dirty
        self.btn_save.setEnabled(dirty)
        self.btn_discard.setEnabled(dirty)
        self.lbl_dirty.setVisible(dirty)
        if hasattr(self, 'btn_clear_sound'):
            self.btn_clear_sound.setEnabled(bool(self.edit_sound.text().strip()))
        if hasattr(self, 'btn_clear_media'):
            self.btn_clear_media.setEnabled(bool(self.edit_media.text().strip()))

        self.config_changed.emit(cfg)

    def _save_changes(self):
        self._saved_config = self._create_config(
            platform=self._current_config.platform,
            alert_type=self._current_config.alert_type,
            enabled=self._current_config.enabled,
            sound_path=self._current_config.sound_path,
            media_path=self._current_config.media_path,
            text_template=self._current_config.text_template,
            duration_ms=self._current_config.duration_ms,
            sound_volume=self._current_config.sound_volume,
            tts_read=self._current_config.tts_read,
            layout=self._current_config.layout,
            style=self._current_config.style,
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
        if self._is_dirty:
            self._save_changes()
        self.test_requested.emit(self.platform, self.alert_type)

    def set_platform_connected(self, connected: bool):
        self._platform_connected = connected
        if hasattr(self, "badge_offline"):
            self.badge_offline.setVisible(not connected)
        if hasattr(self, "sw_enabled"):
            tip = "" if connected else self.i18n.get("alerts.status.platform_offline")
            self.sw_enabled.setToolTip(tip)

    @property
    def btn_clear_sound(self):
        return self.edit_sound.btn_clear

    @property
    def btn_clear_media(self):
        return self.edit_media.btn_clear
