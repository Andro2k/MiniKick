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
    animation_in: str = "fade_in"
    animation_in_duration: float = 1.0
    animation_out: str = "fade_out"
    animation_out_duration: float = 1.0
    bg_color: str = "#121317"
    bg_opacity: int = 88
    border_radius: int = 20
    padding_px: int = 24
    spacing_px: int = 16
    box_shadow: bool = True
    font_weight: str = "bold"
    text_shadow: bool = True
    card_width: int = 560
    card_height: int = 0

from frontend.widgets import (
    ModernCard, ModernButton, ModernSwitch, ExpandableCard,
    NoWheelSlider, NoWheelSpinBox, NoWheelDoubleSpinBox,
    ModernSegmentedControl, NoWheelComboBox, create_badge, ClearableLineEdit, ModernColorPicker,
    InspectorPropertyRow
)
from frontend.common import (
    get_pixmap_colored, COLOR_GREEN, COLOR_PURPLE, COLOR_NEUTRAL_400,
    SPACING_NONE, SPACING_SM, SPACING_MD, MARGIN_NONE, MARGIN_MD
)
from .alert_mockup import AlertOverlayMockupWidget

class AlertEventCard(QWidget):
    config_changed = Signal(object)
    save_requested = Signal(object)
    test_requested = Signal(str, str)
    duplicate_requested = Signal(object)

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

        header_card = ModernCard(parent=self, margin=MARGIN_MD, spacing=SPACING_SM)
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
            text="",
            role="action_outlined",
            icon_name="x-filled.svg",
            icon_size=13,
            parent=self
        )
        self.btn_discard.setToolTip(self.i18n.get("alerts.buttons.discard_tooltip"))
        self.btn_discard.setEnabled(False)
        self.btn_discard.clicked.connect(self._discard_changes)

        self.btn_duplicate = ModernButton(
            text="",
            role="action_outlined",
            icon_name="copy-filled.svg",
            icon_size=13,
            parent=self
        )
        self.btn_duplicate.setToolTip(self.i18n.get("alerts.buttons.duplicate_tooltip"))
        self.btn_duplicate.clicked.connect(self._on_duplicate_clicked)

        self.btn_test = ModernButton(
            text=self.i18n.get("alerts.buttons.test_short"),
            role="action_outlined",
            icon_name="play-filled.svg",
            icon_size=14,
            parent=self
        )
        self.btn_test.setToolTip(self.i18n.get("alerts.buttons.test"))
        self.btn_test.clicked.connect(self._on_test_clicked)

        self.btn_save = ModernButton(
            text=self.i18n.get("alerts.buttons.save_short"),
            role=btn_role,
            icon_name="check-filled.svg",
            icon_size=14,
            parent=self
        )
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save_changes)

        header_row.addWidget(self.btn_discard)
        header_row.addWidget(self.btn_duplicate)
        header_row.addWidget(self.btn_test)
        header_row.addWidget(self.btn_save)

        header_card.addLayout(header_row)
        main_layout.addWidget(header_card)

        self.w_col_left = QWidget(self)
        self.w_col_left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        col_left = QVBoxLayout(self.w_col_left)
        col_left.setContentsMargins(*MARGIN_NONE)
        col_left.setSpacing(SPACING_MD)
        col_left.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.w_col_right = QWidget(self)
        self.w_col_right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        col_right = QVBoxLayout(self.w_col_right)
        col_right.setContentsMargins(*MARGIN_NONE)
        col_right.setSpacing(SPACING_MD)
        col_right.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.card_general = ExpandableCard(
            title=self.i18n.get("alerts.sections.general"),
            description=self.i18n.get("alerts.sections.general_desc"),
            icon_name="clock-filled.svg",
            switch_enabled=False,
            parent=self
        )
        self.card_general.set_expanded(True)

        self.spin_duration = NoWheelSpinBox(parent=self)
        self.spin_duration.setRange(1, 99)
        self.spin_duration.setValue(5)
        self.spin_duration.setSuffix(" s")
        self.spin_duration.setMinimumWidth(96)
        self.spin_duration.valueChanged.connect(self._on_field_changed)

        self.card_general.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.duration"),
            self.spin_duration,
            icon_name="clock-filled.svg",
            tooltip=self.i18n.get("alerts.fields.duration_desc"),
            parent=self
        ))

        self.combo_anim_in = NoWheelComboBox(self)
        anim_in_options = [
            ("fade_in", self.i18n.get("alerts.animations.fade_in")),
            ("slide_up", self.i18n.get("alerts.animations.slide_up")),
            ("slide_down", self.i18n.get("alerts.animations.slide_down")),
            ("slide_left", self.i18n.get("alerts.animations.slide_left")),
            ("slide_right", self.i18n.get("alerts.animations.slide_right")),
            ("zoom_in", self.i18n.get("alerts.animations.zoom_in")),
            ("bounce_in", self.i18n.get("alerts.animations.bounce_in")),
        ]
        for key, label in anim_in_options:
            self.combo_anim_in.addItem(label, key)
        self.combo_anim_in.currentIndexChanged.connect(lambda _: self._on_field_changed())

        self.card_general.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.animations.in_label"),
            self.combo_anim_in,
            icon_name="play-filled.svg",
            tooltip=self.i18n.get("alerts.animations.title"),
            parent=self
        ))

        self.spin_anim_in_dur = NoWheelDoubleSpinBox(parent=self)
        self.spin_anim_in_dur.setRange(0.2, 5.0)
        self.spin_anim_in_dur.setSingleStep(0.1)
        self.spin_anim_in_dur.setValue(1.0)
        self.spin_anim_in_dur.setSuffix(" s")
        self.spin_anim_in_dur.setMinimumWidth(96)
        self.spin_anim_in_dur.valueChanged.connect(self._on_field_changed)

        self.card_general.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.animations.in_duration"),
            self.spin_anim_in_dur,
            icon_name="stopwatch-filled.svg",
            tooltip=self.i18n.get("alerts.animations.title"),
            parent=self
        ))

        self.combo_anim_out = NoWheelComboBox(self)
        anim_out_options = [
            ("fade_out", self.i18n.get("alerts.animations.fade_out")),
            ("slide_down", self.i18n.get("alerts.animations.slide_down_out")),
            ("slide_up", self.i18n.get("alerts.animations.slide_up_out")),
            ("slide_left", self.i18n.get("alerts.animations.slide_left_out")),
            ("slide_right", self.i18n.get("alerts.animations.slide_right_out")),
            ("zoom_out", self.i18n.get("alerts.animations.zoom_out")),
            ("bounce_out", self.i18n.get("alerts.animations.bounce_out")),
        ]
        for key, label in anim_out_options:
            self.combo_anim_out.addItem(label, key)
        self.combo_anim_out.currentIndexChanged.connect(lambda _: self._on_field_changed())

        self.card_general.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.animations.out_label"),
            self.combo_anim_out,
            icon_name="stopwatch-filled.svg",
            tooltip=self.i18n.get("alerts.animations.title"),
            parent=self
        ))

        self.spin_anim_out_dur = NoWheelDoubleSpinBox(parent=self)
        self.spin_anim_out_dur.setRange(0.2, 5.0)
        self.spin_anim_out_dur.setSingleStep(0.1)
        self.spin_anim_out_dur.setValue(1.0)
        self.spin_anim_out_dur.setSuffix(" s")
        self.spin_anim_out_dur.setMinimumWidth(96)
        self.spin_anim_out_dur.valueChanged.connect(self._on_field_changed)

        self.card_general.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.animations.out_duration"),
            self.spin_anim_out_dur,
            icon_name="stopwatch-filled.svg",
            tooltip=self.i18n.get("alerts.animations.title"),
            parent=self
        ))
        col_left.addWidget(self.card_general)

        self.card_design = ExpandableCard(
            title=self.i18n.get("alerts.sections.appearance"),
            description=self.i18n.get("alerts.sections.appearance_desc"),
            icon_name="palette-filled.svg",
            switch_enabled=False,
            parent=self
        )
        self.card_design.set_expanded(False)

        self.seg_layout = ModernSegmentedControl(self)
        self.seg_layout.add_option("above", "arrow-up-filled.svg", self.i18n.get("alerts.layout.above"))
        self.seg_layout.add_option("side", "arrow-left-filled.svg", self.i18n.get("alerts.layout.side"))
        self.seg_layout.add_option("side_right", "arrow-right-filled.svg", self.i18n.get("alerts.layout.side_right"))
        self.seg_layout.add_option("below", "arrow-down-filled.svg", self.i18n.get("alerts.layout.below"))
        self.seg_layout.add_option("overlay", "squares-filled.svg", self.i18n.get("alerts.layout.overlay"))
        self.seg_layout.value_changed.connect(lambda _: self._on_field_changed())

        self.card_design.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.layout.title"),
            self.seg_layout,
            icon_name="transfer-v-filled.svg",
            tooltip=self.i18n.get("alerts.layout.desc"),
            parent=self
        ))

        self.picker_bg_color = ModernColorPicker(
            initial_color="#121317",
            tooltip=self.i18n.get("alerts.fields.bg_color"),
            show_presets=False,
            parent=self
        )
        self.picker_bg_color.color_changed.connect(lambda _: self._on_field_changed())

        self.card_design.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.bg_color"),
            self.picker_bg_color,
            icon_name="palette-filled.svg",
            tooltip=self.i18n.get("alerts.fields.bg_color_desc"),
            parent=self
        ))

        box_bg_opacity = QWidget(self)
        layout_bg_op = QHBoxLayout(box_bg_opacity)
        layout_bg_op.setContentsMargins(*MARGIN_NONE)
        layout_bg_op.setSpacing(SPACING_SM)

        self.slider_bg_opacity = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
        self.slider_bg_opacity.setRange(0, 100)
        self.slider_bg_opacity.setValue(88)
        self.slider_bg_opacity.valueChanged.connect(self._on_bg_opacity_changed)

        self.lbl_bg_opacity_val = QLabel("88%", parent=self)
        self.lbl_bg_opacity_val.setProperty("role", "caption")
        self.lbl_bg_opacity_val.setMinimumWidth(36)

        layout_bg_op.addWidget(self.slider_bg_opacity, 1)
        layout_bg_op.addWidget(self.lbl_bg_opacity_val, 0)

        self.card_design.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.bg_opacity"),
            box_bg_opacity,
            icon_name="dark-light-filled.svg",
            tooltip=self.i18n.get("alerts.fields.bg_opacity_desc"),
            parent=self
        ))

        self.spin_padding = NoWheelSpinBox(parent=self)
        self.spin_padding.setRange(0, 64)
        self.spin_padding.setValue(24)
        self.spin_padding.setSuffix(" px")
        self.spin_padding.setMinimumWidth(96)
        self.spin_padding.valueChanged.connect(self._on_field_changed)

        self.card_design.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.padding"),
            self.spin_padding,
            icon_name="minimize-filled.svg",
            tooltip=self.i18n.get("alerts.fields.padding_desc"),
            parent=self
        ))

        self.spin_spacing = NoWheelSpinBox(parent=self)
        self.spin_spacing.setRange(0, 64)
        self.spin_spacing.setValue(16)
        self.spin_spacing.setSuffix(" px")
        self.spin_spacing.setMinimumWidth(96)
        self.spin_spacing.valueChanged.connect(self._on_field_changed)

        self.card_design.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.spacing"),
            self.spin_spacing,
            icon_name="transfer-h-filled.svg",
            tooltip=self.i18n.get("alerts.fields.spacing_desc"),
            parent=self
        ))

        self.spin_border_radius = NoWheelSpinBox(parent=self)
        self.spin_border_radius.setRange(0, 60)
        self.spin_border_radius.setValue(20)
        self.spin_border_radius.setSuffix(" px")
        self.spin_border_radius.setMinimumWidth(96)
        self.spin_border_radius.valueChanged.connect(self._on_field_changed)

        self.card_design.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.border_radius"),
            self.spin_border_radius,
            icon_name="minimize-filled.svg",
            tooltip=self.i18n.get("alerts.fields.border_radius_desc"),
            parent=self
        ))

        self.sw_box_shadow = ModernSwitch(parent=self)
        self.sw_box_shadow.setChecked(True)
        self.sw_box_shadow.toggled.connect(self._on_field_changed)

        self.card_design.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.box_shadow"),
            self.sw_box_shadow,
            icon_name="squares-filled.svg",
            tooltip=self.i18n.get("alerts.fields.box_shadow_desc"),
            parent=self
        ))
        col_left.addWidget(self.card_design)
        col_left.addStretch(1)

        self.card_typography = ExpandableCard(
            title=self.i18n.get("alerts.sections.text_speech"),
            description=self.i18n.get("alerts.sections.text_speech_desc"),
            icon_name="file-text-filled.svg",
            switch_enabled=False,
            parent=self
        )
        self.card_typography.set_expanded(True)

        self.edit_template = ClearableLineEdit(parent=self)
        self.edit_template.setToolTip(self.i18n.get("alerts.fields.template_hint"))
        self.edit_template.setPlaceholderText(self.i18n.get("alerts.fields.template_hint"))
        self.edit_template.textChanged.connect(self._on_field_changed)

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.template"),
            self.edit_template,
            icon_name="edit-filled.svg",
            tooltip=self.i18n.get("alerts.fields.template_hint"),
            stretch_content=True,
            parent=self
        ))

        self.combo_font = NoWheelComboBox(self)
        for f_name in ["Outfit", "Inter", "Roboto", "Montserrat", "Poppins"]:
            self.combo_font.addItem(f_name, f_name)
        self.combo_font.currentIndexChanged.connect(lambda _: self._on_field_changed())

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.font_family"),
            self.combo_font,
            icon_name="text-filled.svg",
            tooltip=self.i18n.get("alerts.fields.font_family_desc"),
            parent=self
        ))

        self.combo_font_weight = NoWheelComboBox(self)
        self.combo_font_weight.addItem(self.i18n.get("alerts.weights.normal"), "normal")
        self.combo_font_weight.addItem(self.i18n.get("alerts.weights.semi_bold"), "semi_bold")
        self.combo_font_weight.addItem(self.i18n.get("alerts.weights.bold"), "bold")
        self.combo_font_weight.addItem(self.i18n.get("alerts.weights.extra_bold"), "extra_bold")
        self.combo_font_weight.setCurrentIndex(2)
        self.combo_font_weight.currentIndexChanged.connect(lambda _: self._on_field_changed())

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.font_weight"),
            self.combo_font_weight,
            icon_name="bold-filled.svg",
            tooltip=self.i18n.get("alerts.fields.font_weight_desc"),
            parent=self
        ))

        self.seg_align = ModernSegmentedControl(self)
        self.seg_align.add_option("left", "textalign-left-filled.svg", self.i18n.get("alerts.align.left"))
        self.seg_align.add_option("center", "textalign-center-filled.svg", self.i18n.get("alerts.align.center"))
        self.seg_align.add_option("right", "textalign-right-filled.svg", self.i18n.get("alerts.align.right"))
        self.seg_align.add_option("justify", "textalign-justifycenter-filled.svg", self.i18n.get("alerts.align.justify"))
        self.seg_align.value_changed.connect(lambda _: self._on_field_changed())

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.text_align"),
            self.seg_align,
            icon_name="textalign-left-filled.svg",
            tooltip=self.i18n.get("alerts.fields.text_align_desc"),
            parent=self
        ))

        self.spin_font_size = NoWheelSpinBox(parent=self)
        self.spin_font_size.setRange(14, 72)
        self.spin_font_size.setValue(24)
        self.spin_font_size.setSuffix(" px")
        self.spin_font_size.setMinimumWidth(96)
        self.spin_font_size.valueChanged.connect(self._on_field_changed)

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.font_size"),
            self.spin_font_size,
            icon_name="text-filled.svg",
            tooltip=self.i18n.get("alerts.fields.font_size_desc"),
            parent=self
        ))

        self.picker_text_color = ModernColorPicker(
            initial_color="#FFFFFF",
            tooltip=self.i18n.get("alerts.fields.text_color"),
            show_presets=False,
            parent=self
        )
        self.picker_text_color.color_changed.connect(lambda _: self._on_field_changed())

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.text_color"),
            self.picker_text_color,
            icon_name="palette-filled.svg",
            tooltip=self.i18n.get("alerts.fields.text_color_desc"),
            parent=self
        ))

        default_highlight = "#53FC18" if self.platform == "kick" else "#9146FF"
        self.picker_highlight_color = ModernColorPicker(
            initial_color=default_highlight,
            tooltip=self.i18n.get("alerts.fields.highlight_color"),
            show_presets=False,
            parent=self
        )
        self.picker_highlight_color.color_changed.connect(lambda _: self._on_field_changed())

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.highlight_color"),
            self.picker_highlight_color,
            icon_name="text-input-filled.svg",
            tooltip=self.i18n.get("alerts.fields.highlight_color_desc"),
            parent=self
        ))

        self.sw_text_shadow = ModernSwitch(parent=self)
        self.sw_text_shadow.setChecked(True)
        self.sw_text_shadow.toggled.connect(self._on_field_changed)

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.text_shadow"),
            self.sw_text_shadow,
            icon_name="eye-filled.svg",
            tooltip=self.i18n.get("alerts.fields.text_shadow_desc"),
            parent=self
        ))

        self.sw_tts = ModernSwitch(parent=self)
        self.sw_tts.toggled.connect(self._on_field_changed)

        self.card_typography.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.tts"),
            self.sw_tts,
            icon_name="megaphone-filled.svg",
            tooltip=self.i18n.get("alerts.fields.tts_section"),
            parent=self
        ))
        col_right.addWidget(self.card_typography)

        self.card_media = ExpandableCard(
            title=self.i18n.get("alerts.sections.media_sound"),
            description=self.i18n.get("alerts.sections.media_sound_desc"),
            icon_name="album-filled.svg",
            switch_enabled=False,
            parent=self
        )
        self.card_media.set_expanded(False)

        media_picker_box = QWidget(self)
        l_mp = QHBoxLayout(media_picker_box)
        l_mp.setContentsMargins(*MARGIN_NONE)
        l_mp.setSpacing(SPACING_SM)

        self.edit_media = ClearableLineEdit(placeholder=self.i18n.get("alerts.fields.media_placeholder"), parent=self)
        self.edit_media.textChanged.connect(self._on_field_changed)

        btn_browse_media = ModernButton(
            text="",
            role="action_outlined",
            icon_name="folder-open-filled.svg",
            icon_size=13,
            parent=self
        )
        btn_browse_media.setToolTip(self.i18n.get("alerts.buttons.browse"))
        btn_browse_media.setFixedSize(30, 30)
        btn_browse_media.clicked.connect(self._browse_media)

        l_mp.addWidget(self.edit_media, 1)
        l_mp.addWidget(btn_browse_media, 0)

        self.card_media.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.media"),
            media_picker_box,
            icon_name="album-filled.svg",
            stretch_content=True,
            parent=self
        ))

        sound_picker_box = QWidget(self)
        l_sp = QHBoxLayout(sound_picker_box)
        l_sp.setContentsMargins(*MARGIN_NONE)
        l_sp.setSpacing(SPACING_SM)

        self.edit_sound = ClearableLineEdit(placeholder=self.i18n.get("alerts.fields.sound_placeholder"), parent=self)
        self.edit_sound.textChanged.connect(self._on_field_changed)

        btn_browse_sound = ModernButton(
            text="",
            role="action_outlined",
            icon_name="folder-open-filled.svg",
            icon_size=13,
            parent=self
        )
        btn_browse_sound.setToolTip(self.i18n.get("alerts.buttons.browse"))
        btn_browse_sound.setFixedSize(30, 30)
        btn_browse_sound.clicked.connect(self._browse_sound)

        l_sp.addWidget(self.edit_sound, 1)
        l_sp.addWidget(btn_browse_sound, 0)

        self.card_media.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.sound"),
            sound_picker_box,
            icon_name="music-notes-filled.svg",
            stretch_content=True,
            parent=self
        ))

        vol_box = QWidget(self)
        l_vol = QHBoxLayout(vol_box)
        l_vol.setContentsMargins(*MARGIN_NONE)
        l_vol.setSpacing(SPACING_SM)

        self.slider_volume = NoWheelSlider(Qt.Orientation.Horizontal, parent=self)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(80)
        self.slider_volume.valueChanged.connect(self._on_volume_changed)

        self.lbl_volume_val = QLabel("80%", parent=self)
        self.lbl_volume_val.setProperty("role", "caption")
        self.lbl_volume_val.setMinimumWidth(36)

        l_vol.addWidget(self.slider_volume, 1)
        l_vol.addWidget(self.lbl_volume_val, 0)

        self.card_media.add_widget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.volume"),
            vol_box,
            icon_name="volume-up-filled.svg",
            parent=self
        ))
        col_right.addWidget(self.card_media)
        col_right.addStretch(1)

        card_preview = ModernCard(parent=self, margin=MARGIN_NONE, spacing=SPACING_NONE)
        card_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        preview_header_w = QWidget(card_preview)
        sec_prev_header = QHBoxLayout(preview_header_w)
        sec_prev_header.setContentsMargins(*MARGIN_MD)
        sec_prev_header.setSpacing(SPACING_SM)
        lbl_sec_prev_icon = QLabel(parent=self)
        lbl_sec_prev_icon.setPixmap(get_pixmap_colored("eye-filled.svg", COLOR_NEUTRAL_400, size=16))
        lbl_sec_prev_title = QLabel(self.i18n.get("alerts.preview.title"), parent=self)
        lbl_sec_prev_title.setProperty("role", "h3")
        sec_prev_header.addWidget(lbl_sec_prev_icon)
        sec_prev_header.addWidget(lbl_sec_prev_title)
        sec_prev_header.addStretch()

        card_preview.addWidget(preview_header_w)
        card_preview.add_separator()

        mockup_container = QWidget(card_preview)
        mockup_layout = QVBoxLayout(mockup_container)
        mockup_layout.setContentsMargins(*MARGIN_MD)
        mockup_layout.setSpacing(SPACING_NONE)

        self.mockup_widget = AlertOverlayMockupWidget(self.i18n, parent=self)
        self.mockup_widget.setMinimumSize(300, 300)
        self.mockup_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mockup_layout.addWidget(self.mockup_widget)

        card_preview.addWidget(mockup_container, stretch=1)
        card_preview.add_separator()

        controls_container = QWidget(card_preview)
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(*MARGIN_MD)
        controls_layout.setSpacing(SPACING_SM)

        self.spin_card_width = NoWheelSpinBox(parent=self)
        self.spin_card_width.setRange(200, 1920)
        self.spin_card_width.setValue(560)
        self.spin_card_width.setSuffix(" px")
        self.spin_card_width.setMinimumWidth(96)
        self.spin_card_width.valueChanged.connect(self._on_field_changed)

        controls_layout.addWidget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.card_width"),
            self.spin_card_width,
            icon_name="transfer-h-filled.svg",
            tooltip=self.i18n.get("alerts.fields.card_width_desc"),
            parent=self
        ))

        self.spin_card_height = NoWheelSpinBox(parent=self)
        self.spin_card_height.setRange(0, 1080)
        self.spin_card_height.setValue(0)
        self.spin_card_height.setSuffix(" px")
        self.spin_card_height.setSpecialValueText(self.i18n.get("alerts.fields.auto"))
        self.spin_card_height.setMinimumWidth(96)
        self.spin_card_height.valueChanged.connect(self._on_field_changed)

        controls_layout.addWidget(InspectorPropertyRow(
            self.i18n.get("alerts.fields.card_height"),
            self.spin_card_height,
            icon_name="transfer-v-filled.svg",
            tooltip=self.i18n.get("alerts.fields.card_height_desc"),
            parent=self
        ))

        card_preview.addWidget(controls_container)
        self.w_preview = card_preview

        self.body_box = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.body_box.setContentsMargins(*MARGIN_NONE)
        self.body_box.setSpacing(SPACING_MD)

        self.body_box.addWidget(self.w_col_left, stretch=4)
        self.body_box.addWidget(self.w_preview, stretch=5)
        self.body_box.addWidget(self.w_col_right, stretch=4)
        main_layout.addLayout(self.body_box)

        self.sw_enabled = ModernSwitch(parent=self)
        self.sw_enabled.setVisible(False)
        self.sw_enabled.toggled.connect(self._on_field_changed)

        main_layout.addStretch()
        self._is_loading = False

    def _on_bg_opacity_changed(self, val: int):
        self.lbl_bg_opacity_val.setText(f"{val}%")
        self._on_field_changed()

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
            self.i18n.get("alerts.fields.media_filter")
        )
        if file_path:
            self.edit_media.setText(file_path)

    def _update_mockup(self):
        if not hasattr(self, "mockup_widget"):
            return

        layout_val = self.seg_layout.current_value() or "above"
        font_family = self.combo_font.currentData() or "Outfit"
        font_weight = self.combo_font_weight.currentData() or "bold"
        font_size = self.spin_font_size.value()
        text_align = self.seg_align.current_value() or "center"
        text_color = self.picker_text_color.color() or "#FFFFFF"
        highlight_color = self.picker_highlight_color.color() or ""
        bg_color = self.picker_bg_color.color() or "#121317"
        bg_opacity = self.slider_bg_opacity.value()
        border_radius = self.spin_border_radius.value()
        card_width = self.spin_card_width.value()
        card_height = self.spin_card_height.value()
        padding_px = self.spin_padding.value()
        spacing_px = self.spin_spacing.value()
        box_shadow = self.sw_box_shadow.isChecked()
        text_shadow = self.sw_text_shadow.isChecked()

        self.mockup_widget.set_configuration(
            platform=self.platform,
            alert_type=self.alert_type,
            layout=layout_val,
            style="compact",
            text_template=self.edit_template.text().strip() if hasattr(self, "edit_template") else "",
            media_path=self.edit_media.text().strip() if hasattr(self, "edit_media") else "",
            text_color=text_color,
            highlight_color=highlight_color,
            font_family=font_family,
            font_size=font_size,
            text_align=text_align,
            bg_color=bg_color,
            bg_opacity=bg_opacity,
            border_radius=border_radius,
            padding_px=padding_px,
            spacing_px=spacing_px,
            box_shadow=box_shadow,
            font_weight=font_weight,
            text_shadow=text_shadow,
            card_width=card_width,
            card_height=card_height
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
            animation_in=getattr(cfg, "animation_in", "fade_in") or "fade_in",
            animation_in_duration=float(getattr(cfg, "animation_in_duration", 1.0) or 1.0),
            animation_out=getattr(cfg, "animation_out", "fade_out") or "fade_out",
            animation_out_duration=float(getattr(cfg, "animation_out_duration", 1.0) or 1.0),
            bg_color=getattr(cfg, "bg_color", "#121317") or "#121317",
            bg_opacity=int(getattr(cfg, "bg_opacity", 88) if getattr(cfg, "bg_opacity", None) is not None else 88),
            border_radius=int(getattr(cfg, "border_radius", 20) if getattr(cfg, "border_radius", None) is not None else 20),
            padding_px=int(getattr(cfg, "padding_px", 24) if getattr(cfg, "padding_px", None) is not None else 24),
            spacing_px=int(getattr(cfg, "spacing_px", 16) if getattr(cfg, "spacing_px", None) is not None else 16),
            box_shadow=bool(getattr(cfg, "box_shadow", True)),
            font_weight=str(getattr(cfg, "font_weight", "bold") or "bold"),
            text_shadow=bool(getattr(cfg, "text_shadow", True)),
            card_width=int(getattr(cfg, "card_width", 560) or 560),
            card_height=int(getattr(cfg, "card_height", 0) if getattr(cfg, "card_height", None) is not None else 0)
        )

        self.sw_enabled.setChecked(cfg.enabled)
        self.edit_template.setText(cfg.text_template)
        self.edit_sound.setText(cfg.sound_path)
        self.edit_media.setText(cfg.media_path)
        self.spin_duration.setValue(max(1, cfg.duration_ms // 1000))

        anim_in = getattr(cfg, "animation_in", "fade_in") or "fade_in"
        idx_in = self.combo_anim_in.findData(anim_in)
        if idx_in >= 0:
            self.combo_anim_in.setCurrentIndex(idx_in)
        self.spin_anim_in_dur.setValue(float(getattr(cfg, "animation_in_duration", 1.0) or 1.0))

        anim_out = getattr(cfg, "animation_out", "fade_out") or "fade_out"
        idx_out = self.combo_anim_out.findData(anim_out)
        if idx_out >= 0:
            self.combo_anim_out.setCurrentIndex(idx_out)
        self.spin_anim_out_dur.setValue(float(getattr(cfg, "animation_out_duration", 1.0) or 1.0))

        layout_val = getattr(cfg, "layout", "above") or "above"
        self.seg_layout.set_current_value(layout_val)

        bg_color = getattr(cfg, "bg_color", "#121317") or "#121317"
        self.picker_bg_color.set_color(bg_color)

        bg_opacity = int(getattr(cfg, "bg_opacity", 88) if getattr(cfg, "bg_opacity", None) is not None else 88)
        self.slider_bg_opacity.setValue(bg_opacity)
        self.lbl_bg_opacity_val.setText(f"{bg_opacity}%")

        self.spin_card_width.setValue(int(getattr(cfg, "card_width", 560) or 560))
        self.spin_card_height.setValue(int(getattr(cfg, "card_height", 0) if getattr(cfg, "card_height", None) is not None else 0))
        self.spin_padding.setValue(int(getattr(cfg, "padding_px", 24) if getattr(cfg, "padding_px", None) is not None else 24))
        self.spin_spacing.setValue(int(getattr(cfg, "spacing_px", 16) if getattr(cfg, "spacing_px", None) is not None else 16))
        self.spin_border_radius.setValue(int(getattr(cfg, "border_radius", 20) if getattr(cfg, "border_radius", None) is not None else 20))
        self.sw_box_shadow.setChecked(bool(getattr(cfg, "box_shadow", True)))

        font_val = getattr(cfg, "font_family", "Outfit") or "Outfit"
        idx_f = self.combo_font.findData(font_val)
        if idx_f >= 0:
            self.combo_font.setCurrentIndex(idx_f)

        weight_val = getattr(cfg, "font_weight", "bold") or "bold"
        idx_w = self.combo_font_weight.findData(weight_val)
        if idx_w >= 0:
            self.combo_font_weight.setCurrentIndex(idx_w)

        self.spin_font_size.setValue(int(getattr(cfg, "font_size", 24) or 24))

        align_val = getattr(cfg, "text_align", "center") or "center"
        self.seg_align.set_current_value(align_val)

        self.picker_text_color.set_color(getattr(cfg, "text_color", "#FFFFFF") or "#FFFFFF")

        default_hl = "#53FC18" if self.platform == "kick" else "#9146FF"
        self.picker_highlight_color.set_color(getattr(cfg, "highlight_color", "") or default_hl)

        self.sw_text_shadow.setChecked(bool(getattr(cfg, "text_shadow", True)))
        self.sw_tts.setChecked(cfg.tts_read)

        vol_pct = int(cfg.sound_volume * 100)
        self.slider_volume.setValue(vol_pct)
        self.lbl_volume_val.setText(f"{vol_pct}%")

        self._update_mockup()

        self._is_dirty = False
        self.btn_save.setEnabled(False)
        self.btn_discard.setEnabled(False)
        self.lbl_dirty.setVisible(False)
        self._is_loading = False

    def _on_field_changed(self):
        if self._is_loading:
            return

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
            layout=self.seg_layout.current_value() or "above",
            style="compact",
            text_color=self.picker_text_color.color(),
            highlight_color=self.picker_highlight_color.color(),
            font_family=self.combo_font.currentData() or "Outfit",
            font_size=self.spin_font_size.value(),
            text_align=self.seg_align.current_value() or "center",
            animation_in=self.combo_anim_in.currentData() or "fade_in",
            animation_in_duration=round(self.spin_anim_in_dur.value(), 2),
            animation_out=self.combo_anim_out.currentData() or "fade_out",
            animation_out_duration=round(self.spin_anim_out_dur.value(), 2),
            bg_color=self.picker_bg_color.color(),
            bg_opacity=self.slider_bg_opacity.value(),
            border_radius=self.spin_border_radius.value(),
            padding_px=self.spin_padding.value(),
            spacing_px=self.spin_spacing.value(),
            box_shadow=self.sw_box_shadow.isChecked(),
            font_weight=self.combo_font_weight.currentData() or "bold",
            text_shadow=self.sw_text_shadow.isChecked(),
            card_width=self.spin_card_width.value(),
            card_height=self.spin_card_height.value()
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
                cfg.text_color != getattr(self._saved_config, "text_color", "#FFFFFF") or
                cfg.highlight_color != getattr(self._saved_config, "highlight_color", "") or
                cfg.font_family != getattr(self._saved_config, "font_family", "Outfit") or
                cfg.font_size != getattr(self._saved_config, "font_size", 24) or
                cfg.text_align != getattr(self._saved_config, "text_align", "center") or
                cfg.animation_in != getattr(self._saved_config, "animation_in", "fade_in") or
                cfg.animation_in_duration != getattr(self._saved_config, "animation_in_duration", 1.0) or
                cfg.animation_out != getattr(self._saved_config, "animation_out", "fade_out") or
                cfg.animation_out_duration != getattr(self._saved_config, "animation_out_duration", 1.0) or
                cfg.bg_color != getattr(self._saved_config, "bg_color", "#121317") or
                cfg.bg_opacity != getattr(self._saved_config, "bg_opacity", 88) or
                cfg.border_radius != getattr(self._saved_config, "border_radius", 20) or
                cfg.padding_px != getattr(self._saved_config, "padding_px", 24) or
                cfg.spacing_px != getattr(self._saved_config, "spacing_px", 16) or
                cfg.box_shadow != getattr(self._saved_config, "box_shadow", True) or
                cfg.font_weight != getattr(self._saved_config, "font_weight", "bold") or
                cfg.text_shadow != getattr(self._saved_config, "text_shadow", True) or
                cfg.card_width != getattr(self._saved_config, "card_width", 560) or
                cfg.card_height != getattr(self._saved_config, "card_height", 0)
            )

        self._is_dirty = dirty
        self.btn_save.setEnabled(dirty)
        self.btn_discard.setEnabled(dirty)
        self.lbl_dirty.setVisible(dirty)

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
            animation_in=self._current_config.animation_in,
            animation_in_duration=self._current_config.animation_in_duration,
            animation_out=self._current_config.animation_out,
            animation_out_duration=self._current_config.animation_out_duration,
            bg_color=self._current_config.bg_color,
            bg_opacity=self._current_config.bg_opacity,
            border_radius=self._current_config.border_radius,
            padding_px=self._current_config.padding_px,
            spacing_px=self._current_config.spacing_px,
            box_shadow=self._current_config.box_shadow,
            font_weight=self._current_config.font_weight,
            text_shadow=self._current_config.text_shadow,
            card_width=self._current_config.card_width,
            card_height=self._current_config.card_height
        )
        self._is_dirty = False
        self.btn_save.setEnabled(False)
        self.btn_discard.setEnabled(False)
        self.lbl_dirty.setVisible(False)
        self.save_requested.emit(self._saved_config)

    def _discard_changes(self):
        if self._saved_config:
            self.load_config(self._saved_config)

    def _on_duplicate_clicked(self):
        self.duplicate_requested.emit(self._current_config)

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
        width = event.size().width() if event else self.width()

        target_dir = QBoxLayout.Direction.TopToBottom if width < 1280 else QBoxLayout.Direction.LeftToRight
        if hasattr(self, "body_box") and self.body_box.direction() != target_dir:
            self.body_box.setDirection(target_dir)

            self.body_box.removeWidget(self.w_preview)
            self.body_box.removeWidget(self.w_col_left)
            self.body_box.removeWidget(self.w_col_right)

            if target_dir == QBoxLayout.Direction.TopToBottom:
                self.body_box.addWidget(self.w_preview, 0)
                self.body_box.addWidget(self.w_col_left, 0)
                self.body_box.addWidget(self.w_col_right, 0)
            else:
                self.body_box.addWidget(self.w_col_left, 4)
                self.body_box.addWidget(self.w_preview, 5)
                self.body_box.addWidget(self.w_col_right, 4)
