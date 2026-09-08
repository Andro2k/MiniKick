# frontend\components\alerts\event_card.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel,
    QFileDialog, QSizePolicy
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
    text_color: str = "#FFFFFF"
    highlight_color: str = ""
    font_family: str = "Outfit"
    font_size: int = 24
    text_align: str = "center"

from frontend.widgets import (
    ModernCard, ModernButton, ModernSwitch,
    NoWheelSlider, NoWheelSpinBox, ModernDivider,
    ModernSegmentedControl, NoWheelComboBox, SettingRow,
    create_badge, ClearableLineEdit, ModernColorPicker
)
from frontend.common import (
    get_pixmap_colored, COLOR_GREEN, COLOR_PURPLE, COLOR_NEUTRAL_400,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    MARGIN_NONE, MARGIN_XS, MARGIN_H_XS, MARGIN_SM
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

        self.body_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.body_row.setContentsMargins(*MARGIN_NONE)
        self.body_row.setSpacing(SPACING_LG)

        col_controls = QVBoxLayout()
        col_controls.setContentsMargins(*MARGIN_NONE)
        col_controls.setSpacing(SPACING_SM)

        self.seg_layout = ModernSegmentedControl(self)
        self.seg_layout.add_option("above", "arrow-up-filled.svg", self.i18n.get("alerts.layout.above"))
        self.seg_layout.add_option("side", "arrow-left-filled.svg", self.i18n.get("alerts.layout.side"))
        self.seg_layout.add_option("side_right", "arrow-right-filled.svg", self.i18n.get("alerts.layout.side_right"))
        self.seg_layout.add_option("below", "arrow-down-filled.svg", self.i18n.get("alerts.layout.below"))
        self.seg_layout.add_option("overlay", "box-multiple-2.svg", self.i18n.get("alerts.layout.overlay"))
        self.seg_layout.value_changed.connect(lambda _: self._on_field_changed())

        row_layout = SettingRow(
            "arrows-vertical.svg",
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
        self.combo_style.addItem(self.i18n.get("alerts.style.sticker"), "sticker")
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

        self.combo_font = NoWheelComboBox(self)
        for f_name in ["Outfit", "Inter", "Roboto", "Montserrat", "Poppins"]:
            self.combo_font.addItem(f_name, f_name)
        self.combo_font.currentIndexChanged.connect(lambda _: self._on_field_changed())

        row_font = SettingRow(
            "file-text.svg",
            self.i18n.get("alerts.fields.font_family"),
            self.i18n.get("alerts.fields.font_family_desc"),
            self.combo_font,
            icon_color=COLOR_NEUTRAL_400,
            parent=self
        )
        col_controls.addWidget(row_font)

        self.spin_font_size = NoWheelSpinBox(parent=self)
        self.spin_font_size.setRange(14, 48)
        self.spin_font_size.setValue(24)
        self.spin_font_size.setSuffix(" px")
        self.spin_font_size.setFixedWidth(142)
        self.spin_font_size.valueChanged.connect(self._on_field_changed)

        row_size = SettingRow(
            "text-size.svg",
            self.i18n.get("alerts.fields.font_size"),
            self.i18n.get("alerts.fields.font_size_desc"),
            self.spin_font_size,
            icon_color=COLOR_NEUTRAL_400,
            parent=self
        )
        col_controls.addWidget(row_size)

        self.combo_align = NoWheelComboBox(self)
        self.combo_align.addItem(self.i18n.get("alerts.align.left"), "left")
        self.combo_align.addItem(self.i18n.get("alerts.align.center"), "center")
        self.combo_align.addItem(self.i18n.get("alerts.align.right"), "right")
        self.combo_align.setCurrentIndex(1)
        self.combo_align.setFixedWidth(120)
        self.combo_align.currentIndexChanged.connect(lambda _: self._on_field_changed())

        row_align = SettingRow(
            "align-left-2.svg",
            self.i18n.get("alerts.fields.text_align"),
            self.i18n.get("alerts.fields.text_align_desc"),
            self.combo_align,
            icon_color=COLOR_NEUTRAL_400,
            parent=self
        )
        col_controls.addWidget(row_align)

        self.spin_duration = NoWheelSpinBox(parent=self)
        self.spin_duration.setRange(1, 60)
        self.spin_duration.setValue(5)
        self.spin_duration.setSuffix(" s")
        self.spin_duration.setFixedWidth(142)
        self.spin_duration.valueChanged.connect(self._on_field_changed)

        row_duration = SettingRow(
            "clock.svg",
            self.i18n.get("alerts.fields.duration"),
            self.i18n.get("alerts.fields.duration_desc"),
            self.spin_duration,
            icon_color=COLOR_NEUTRAL_400,
            parent=self
        )
        col_controls.addWidget(row_duration)

        self.colors_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.colors_row.setContentsMargins(*MARGIN_NONE)
        self.colors_row.setSpacing(SPACING_LG)

        col_tc = QVBoxLayout()
        col_tc.setContentsMargins(*MARGIN_SM)
        col_tc.setSpacing(SPACING_XS)

        header_tc = QHBoxLayout()
        header_tc.setSpacing(SPACING_SM)
        icon_tc = QLabel(parent=self)
        icon_tc.setPixmap(get_pixmap_colored("palette.svg", COLOR_NEUTRAL_400, size=18))
        lbl_tc_title = QLabel(self.i18n.get("alerts.fields.text_color"), parent=self)
        lbl_tc_title.setProperty("role", "h3")
        lbl_tc_title.setWordWrap(True)
        header_tc.addWidget(icon_tc)
        header_tc.addWidget(lbl_tc_title, 1)

        lbl_tc_desc = QLabel(self.i18n.get("alerts.fields.text_color_desc"), parent=self)
        lbl_tc_desc.setProperty("role", "body")
        lbl_tc_desc.setWordWrap(True)

        self.picker_text_color = ModernColorPicker(
            initial_color="#FFFFFF",
            tooltip=self.i18n.get("alerts.fields.text_color"),
            presets=["#FFFFFF", "#F8FAFC", "#E2E8F0", "#94A3B8", "#FBBF24", "#F43F5E"],
            is_vertical=True,
            parent=self
        )
        self.picker_text_color.color_changed.connect(lambda _: self._on_field_changed())

        col_tc.addLayout(header_tc)
        col_tc.addWidget(lbl_tc_desc)
        col_tc.addWidget(self.picker_text_color)

        col_hl = QVBoxLayout()
        col_hl.setContentsMargins(*MARGIN_SM)
        col_hl.setSpacing(SPACING_XS)

        header_hl = QHBoxLayout()
        header_hl.setSpacing(SPACING_SM)
        icon_hl = QLabel(parent=self)
        icon_hl.setPixmap(get_pixmap_colored("star.svg", COLOR_NEUTRAL_400, size=18))
        lbl_hl_title = QLabel(self.i18n.get("alerts.fields.highlight_color"), parent=self)
        lbl_hl_title.setProperty("role", "h3")
        lbl_hl_title.setWordWrap(True)
        header_hl.addWidget(icon_hl)
        header_hl.addWidget(lbl_hl_title, 1)

        lbl_hl_desc = QLabel(self.i18n.get("alerts.fields.highlight_color_desc"), parent=self)
        lbl_hl_desc.setProperty("role", "body")
        lbl_hl_desc.setWordWrap(True)

        default_highlight = "#53FC18" if self.platform == "kick" else "#9146FF"
        self.picker_highlight_color = ModernColorPicker(
            initial_color=default_highlight,
            tooltip=self.i18n.get("alerts.fields.highlight_color"),
            presets=["#53FC18", "#9146FF", "#00D2FF", "#FFB800", "#FF4655", "#FFFFFF"],
            is_vertical=True,
            parent=self
        )
        self.picker_highlight_color.color_changed.connect(lambda _: self._on_field_changed())

        col_hl.addLayout(header_hl)
        col_hl.addWidget(lbl_hl_desc)
        col_hl.addWidget(self.picker_highlight_color)

        self.colors_row.addLayout(col_tc, stretch=1)
        self.colors_row.addLayout(col_hl, stretch=1)
        col_controls.addLayout(self.colors_row)

        col_preview = QVBoxLayout()
        col_preview.setContentsMargins(*MARGIN_NONE)
        col_preview.setSpacing(SPACING_SM)
        col_preview.addStretch(1)

        lbl_preview = QLabel(self.i18n.get("alerts.preview.title"), parent=self)
        lbl_preview.setProperty("role", "caption")
        lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col_preview.addWidget(lbl_preview)

        self.mockup_widget = AlertOverlayMockupWidget(self.i18n, parent=self)
        self.mockup_widget.setMinimumSize(160, 160)
        self.mockup_widget.setMaximumSize(380, 380)
        self.mockup_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        col_preview.addWidget(self.mockup_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        col_preview.addStretch(1)

        self.body_row.addLayout(col_controls, stretch=3)
        self.body_row.addLayout(col_preview, stretch=2)

        card_appearance.addLayout(self.body_row)
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

        self.sw_enabled = ModernSwitch(parent=self)
        self.sw_enabled.setVisible(False)
        self.sw_enabled.toggled.connect(self._on_field_changed)

        template_row = QHBoxLayout()
        template_row.setContentsMargins(*MARGIN_H_XS)
        template_row.setSpacing(SPACING_XL)

        col_template = QVBoxLayout()
        col_template.setSpacing(SPACING_XS)

        lbl_template = QLabel(self.i18n.get("alerts.fields.template"), parent=self)
        lbl_template.setProperty("role", "caption")

        self.edit_template = ClearableLineEdit(parent=self)
        self.edit_template.setToolTip(self.i18n.get("alerts.fields.template_hint"))
        self.edit_template.textChanged.connect(self._on_field_changed)

        lbl_template_hint = QLabel(self.i18n.get("alerts.fields.template_hint"), parent=self)
        lbl_template_hint.setProperty("role", "caption")
        lbl_template_hint.setWordWrap(True)

        col_template.addWidget(lbl_template)
        col_template.addWidget(self.edit_template)
        col_template.addWidget(lbl_template_hint)

        col_tts = QVBoxLayout()
        col_tts.setSpacing(SPACING_SM)

        lbl_tts_title = QLabel(self.i18n.get("alerts.fields.tts"), parent=self)
        lbl_tts_title.setProperty("role", "caption")

        self.sw_tts = ModernSwitch(parent=self)
        self.sw_tts.toggled.connect(self._on_field_changed)

        col_tts.addWidget(lbl_tts_title)
        col_tts.addWidget(self.sw_tts, alignment=Qt.AlignmentFlag.AlignLeft)
        col_tts.addStretch()

        template_row.addLayout(col_template, stretch=1)
        template_row.addLayout(col_tts, stretch=0)

        card_config.addLayout(template_row)
        card_config.addWidget(ModernDivider(self))

        self.media_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.media_row.setContentsMargins(*MARGIN_H_XS)
        self.media_row.setSpacing(SPACING_XL)

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

        self.media_row.addLayout(col_video, stretch=1)
        self.media_row.addLayout(col_audio, stretch=1)
        card_config.addLayout(self.media_row)

        main_layout.addWidget(card_config)
        main_layout.addStretch()

        self._is_loading = False

    def _update_mockup(self):
        if (
            hasattr(self, "mockup_widget")
            and hasattr(self, "seg_layout")
            and hasattr(self, "combo_style")
        ):
            layout_val = self.seg_layout.current_value() or "above"
            style_val = self.combo_style.currentData() or "compact"
            font_family = self.combo_font.currentData() if hasattr(self, "combo_font") else "Outfit"
            font_size = self.spin_font_size.value() if hasattr(self, "spin_font_size") else 24
            text_align = self.combo_align.currentData() if hasattr(self, "combo_align") else "center"
            text_color = self.picker_text_color.color() if hasattr(self, "picker_text_color") else "#FFFFFF"
            highlight_color = self.picker_highlight_color.color() if hasattr(self, "picker_highlight_color") else ""

            self.mockup_widget.set_configuration(
                platform=self.platform,
                alert_type=self.alert_type,
                layout=layout_val,
                style=style_val,
                text_template=self.edit_template.text().strip() if hasattr(self, "edit_template") else "",
                media_path=self.edit_media.text().strip() if hasattr(self, "edit_media") else "",
                text_color=text_color,
                highlight_color=highlight_color,
                font_family=font_family,
                font_size=font_size,
                text_align=text_align
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
            text_color=getattr(cfg, "text_color", "#FFFFFF") or "#FFFFFF",
            highlight_color=getattr(cfg, "highlight_color", "") or "",
            font_family=getattr(cfg, "font_family", "Outfit") or "Outfit",
            font_size=int(getattr(cfg, "font_size", 24) or 24),
            text_align=getattr(cfg, "text_align", "center") or "center",
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

        font_val = getattr(cfg, "font_family", "Outfit") or "Outfit"
        idx_f = self.combo_font.findData(font_val)
        if idx_f >= 0:
            self.combo_font.setCurrentIndex(idx_f)

        self.spin_font_size.setValue(int(getattr(cfg, "font_size", 24) or 24))

        align_val = getattr(cfg, "text_align", "center") or "center"
        idx_a = self.combo_align.findData(align_val)
        if idx_a >= 0:
            self.combo_align.setCurrentIndex(idx_a)

        self.picker_text_color.set_color(getattr(cfg, "text_color", "#FFFFFF") or "#FFFFFF")

        default_hl = "#53FC18" if self.platform == "kick" else "#9146FF"
        self.picker_highlight_color.set_color(getattr(cfg, "highlight_color", "") or default_hl)

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
        font_family = self.combo_font.currentData() or "Outfit"
        font_size = self.spin_font_size.value()
        text_align = self.combo_align.currentData() or "center"
        text_color = self.picker_text_color.color()
        highlight_color = self.picker_highlight_color.color()

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
            style=style_val,
            text_color=text_color,
            highlight_color=highlight_color,
            font_family=font_family,
            font_size=font_size,
            text_align=text_align
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
                cfg.style != getattr(self._saved_config, "style", "compact") or
                cfg.text_color != getattr(self._saved_config, "text_color", "#FFFFFF") or
                cfg.highlight_color != getattr(self._saved_config, "highlight_color", "") or
                cfg.font_family != getattr(self._saved_config, "font_family", "Outfit") or
                cfg.font_size != getattr(self._saved_config, "font_size", 24) or
                cfg.text_align != getattr(self._saved_config, "text_align", "center")
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
            text_color=self._current_config.text_color,
            highlight_color=self._current_config.highlight_color,
            font_family=self._current_config.font_family,
            font_size=self._current_config.font_size,
            text_align=self._current_config.text_align,
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

    def set_enabled(self, enabled: bool):
        self.sw_enabled.blockSignals(True)
        self.sw_enabled.setChecked(enabled)
        self.sw_enabled.blockSignals(False)
        self._current_config.enabled = enabled

    def save_enabled_change(self, enabled: bool):
        self.set_enabled(enabled)
        self._saved_config.enabled = enabled
        self.save_requested.emit(self._saved_config)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()

        if hasattr(self, "body_row"):
            body_dir = QBoxLayout.Direction.TopToBottom if width < 620 else QBoxLayout.Direction.LeftToRight
            if body_dir != self.body_row.direction():
                self.body_row.setDirection(body_dir)

        if hasattr(self, "colors_row"):
            colors_dir = QBoxLayout.Direction.TopToBottom if width < 500 else QBoxLayout.Direction.LeftToRight
            if colors_dir != self.colors_row.direction():
                self.colors_row.setDirection(colors_dir)

        if hasattr(self, "media_row"):
            media_dir = QBoxLayout.Direction.TopToBottom if width < 550 else QBoxLayout.Direction.LeftToRight
            if media_dir != self.media_row.direction():
                self.media_row.setDirection(media_dir)
