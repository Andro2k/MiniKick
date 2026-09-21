# frontend\widgets\blocks.py

from PySide6.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, 
                               QGridLayout, QLabel, QFrame, QScrollArea, QPushButton, QLineEdit)
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QPainter, QLinearGradient, QColor
from frontend.common import (
    get_icon_colored, get_pixmap_colored, COLOR_NEUTRAL_400, COLOR_NEUTRAL_950,
    SPACING_NONE, SPACING_2XS, SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    MARGIN_NONE, MARGIN_MD, MARGIN_LG, MARGIN_H_SM, MARGIN_H_MD, MARGIN_XS,
    MARGIN_SECTION_HEADER, MARGIN_SECTION_HEADER_FIRST, MARGIN_SETTING_ROW
)
from .no_wheel import NoWheelComboBox, NoWheelSpinBox
from .controls_widget import ModernSwitch

class ViewHeader(QFrame):
    def __init__(self, title_text: str, subtitle_text: str, title_color: str = None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*MARGIN_XS)
        layout.setSpacing(SPACING_XS)

        title = QLabel(title_text, parent=self)
        title.setProperty("role", "h1")
        if title_color:
            color_state = "danger" if title_color in ("#EF4444", "#ff4444", "red") else ("success" if title_color in ("#2EC570", "#22c55e", "green") else "normal")
            title.setProperty("state", color_state)
        
        subtitle = QLabel(subtitle_text, parent=self)
        subtitle.setProperty("role", "body")
        subtitle.setWordWrap(True)
        subtitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)

class SectionHeader(QWidget):
    def __init__(self, text: str = "", parent=None, first: bool = False):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        margins = MARGIN_SECTION_HEADER_FIRST if first else MARGIN_SECTION_HEADER
        layout.setContentsMargins(*margins)
        layout.setSpacing(SPACING_NONE)
        self.lbl = QLabel(text, parent=self)
        self.lbl.setProperty("role", "section_header")
        layout.addWidget(self.lbl)

    def setText(self, text: str):
        self.lbl.setText(text)

class SettingRow(QWidget):
    def __init__(
        self,
        icon_name: str = "",
        title_text: str = "",
        desc_text: str = "",
        right_widget: QWidget = None,
        icon_color: str = COLOR_NEUTRAL_400,
        title_color: str = None,
        contents_margins: tuple = MARGIN_SETTING_ROW,
        parent=None
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*contents_margins)
        layout.setSpacing(SPACING_MD)

        if icon_name:
            icon_lbl = QLabel(parent=self)
            icon_lbl.setPixmap(get_pixmap_colored(icon_name, icon_color, size=18))
            icon_lbl.setFixedWidth(20)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(SPACING_2XS)
        
        lbl_title = QLabel(title_text, parent=self)
        lbl_title.setProperty("role", "h3")
        lbl_title.setWordWrap(True)
        if title_color:
            color_state = "danger" if title_color in ("#EF4444", "#ff4444", "red") else ("success" if title_color in ("#2EC570", "#22c55e", "green") else "normal")
            lbl_title.setProperty("state", color_state)
        
        self.lbl_desc = QLabel(desc_text, parent=self)
        self.lbl_desc.setProperty("role", "body")
        self.lbl_desc.setWordWrap(True)
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(self.lbl_desc)
        
        layout.addLayout(text_layout, stretch=1)
        if right_widget:
            layout.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

    def set_description(self, text: str):
        if hasattr(self, 'lbl_desc') and self.lbl_desc:
            self.lbl_desc.setText(text)

class FormField(QWidget):
    def __init__(
        self,
        label_text: str,
        control_widget: QWidget,
        hint_text: str = "",
        is_horizontal: bool = False,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.control_widget = control_widget
        self._initial_hint = hint_text

        if is_horizontal:
            self.layout = QHBoxLayout(self)
            self.layout.setContentsMargins(*MARGIN_NONE)
            self.layout.setSpacing(SPACING_LG)

            self.lbl_title = QLabel(label_text, parent=self)
            self.lbl_title.setProperty("role", "h3")
            self.layout.addWidget(self.lbl_title)
            self.layout.addWidget(control_widget, stretch=1)
            self.lbl_hint = None
        else:
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(*MARGIN_NONE)
            self.layout.setSpacing(SPACING_XS)

            self.lbl_title = QLabel(label_text, parent=self)
            self.lbl_title.setProperty("role", "h3")
            self.layout.addWidget(self.lbl_title)
            self.layout.addWidget(control_widget)

            self.lbl_hint = QLabel(hint_text, parent=self) if hint_text else None
            if self.lbl_hint:
                self.lbl_hint.setProperty("role", "caption")
                self.lbl_hint.setWordWrap(True)
                self.layout.addWidget(self.lbl_hint)

    def set_label(self, text: str):
        self.lbl_title.setText(text)

    def set_hint(self, text: str):
        if not self.lbl_hint and text:
            self.lbl_hint = QLabel(text, parent=self)
            self.lbl_hint.setProperty("role", "caption")
            self.lbl_hint.setWordWrap(True)
            self.layout.addWidget(self.lbl_hint)
        elif self.lbl_hint:
            self.lbl_hint.setText(text)
            self.lbl_hint.setVisible(bool(text))

    def set_error(self, error_text: str):
        if not self.lbl_hint:
            self.lbl_hint = QLabel(parent=self)
            self.lbl_hint.setWordWrap(True)
            self.layout.addWidget(self.lbl_hint)
        self.lbl_hint.setText(error_text)
        self.lbl_hint.setProperty("role", "caption")
        self.lbl_hint.setProperty("state", "danger")
        self.lbl_hint.style().unpolish(self.lbl_hint)
        self.lbl_hint.style().polish(self.lbl_hint)
        self.lbl_hint.setVisible(bool(error_text))

    def clear_error(self):
        if self.lbl_hint:
            if self._initial_hint:
                self.lbl_hint.setText(self._initial_hint)
                self.lbl_hint.setProperty("role", "caption")
                self.lbl_hint.setProperty("state", "normal")
                self.lbl_hint.style().unpolish(self.lbl_hint)
                self.lbl_hint.style().polish(self.lbl_hint)
                self.lbl_hint.setVisible(True)
            else:
                self.lbl_hint.setText("")
                self.lbl_hint.setVisible(False)

class ModernDivider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("role", "divider")

class SliderRow(QWidget):
    def __init__(
        self,
        icon_name: str,
        title_text: str,
        desc_text: str,
        slider_widget: QWidget,
        value_label: QLabel,
        icon_color: str = COLOR_NEUTRAL_400,
        parent=None,
        contents_margins: tuple = MARGIN_SETTING_ROW
    ):
        super().__init__(parent)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(*contents_margins)
        main_layout.setSpacing(SPACING_SM)

        if icon_name:
            icon_lbl = QLabel(parent=self)
            icon_lbl.setPixmap(get_pixmap_colored(icon_name, icon_color, size=18))
            icon_lbl.setFixedWidth(20)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            main_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(SPACING_SM)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING_SM)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(SPACING_2XS)

        lbl_title = QLabel(title_text, parent=self)
        lbl_title.setProperty("role", "h3")

        self.lbl_desc = QLabel(desc_text, parent=self)
        self.lbl_desc.setProperty("role", "body")
        self.lbl_desc.setWordWrap(True)

        text_layout.addWidget(lbl_title)
        text_layout.addWidget(self.lbl_desc)

        header_layout.addLayout(text_layout, stretch=1)
        if value_label:
            header_layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        content_layout.addLayout(header_layout)
        content_layout.addWidget(slider_widget)

        main_layout.addLayout(content_layout, stretch=1)

    def set_description(self, text: str):
        if hasattr(self, 'lbl_desc') and self.lbl_desc:
            self.lbl_desc.setText(text)

class StatCard(QFrame):
    def __init__(self, title_text: str, icon_name: str, initial_value: str = "-", parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.setMinimumWidth(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*MARGIN_MD)
        layout.setSpacing(SPACING_SM)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING_SM)

        icon_lbl = QLabel(parent=self)
        icon_lbl.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_400, size=14))

        self.lbl_title = QLabel(title_text, parent=self)
        self.lbl_title.setProperty("role", "h3")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.lbl_value = QLabel(initial_value, parent=self)
        self.lbl_value.setProperty("role", "body")
        self.lbl_value.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_value)
        layout.addStretch()

    def set_value(self, value: str):
        self.lbl_value.setText(str(value))

class ModernCard(QFrame):
    def __init__(self, parent=None, margin=MARGIN_MD, spacing=SPACING_SM, orientation="vertical"):
        super().__init__(parent)
        self.setProperty("role", "card")
        
        if orientation == "horizontal":
            self.card_layout = QHBoxLayout(self)
        else:
            self.card_layout = QVBoxLayout(self)
            
        if isinstance(margin, (tuple, list)):
            self.card_layout.setContentsMargins(*margin)
        else:
            self.card_layout.setContentsMargins(margin, margin, margin, margin)
        self.card_layout.setSpacing(spacing)
        
    def addWidget(self, widget, *args, **kwargs):
        self.card_layout.addWidget(widget, *args, **kwargs)
        
    def addLayout(self, layout, *args, **kwargs):
        self.card_layout.addLayout(layout, *args, **kwargs)

    def addSpacing(self, spacing: int):
        self.card_layout.addSpacing(spacing)

    def add_separator(self):
        divider = ModernDivider(parent=self)
        self.card_layout.addWidget(divider)

    def addStretch(self, stretch: int = 0):
        self.card_layout.addStretch(stretch)

class FadingScrollArea(QScrollArea):
    def __init__(self, widget: QWidget = None, parent=None, fade_height: int = 28, fade_color: str | QColor = COLOR_NEUTRAL_950):
        super().__init__(parent)
        self.fade_height = fade_height
        self._fade_color = QColor(fade_color) if isinstance(fade_color, str) else fade_color
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if widget:
            self.setWidget(widget)
        self.verticalScrollBar().valueChanged.connect(lambda _: self.viewport().update())

    @property
    def fade_size(self) -> int:
        return self.fade_height

    def set_fade_size(self, size: int):
        self.fade_height = size
        if self.viewport():
            self.viewport().update()

    def viewportEvent(self, event):
        res = super().viewportEvent(event)
        if event.type() == QEvent.Type.Paint:
            self._paint_fade()
        return res

    def _paint_fade(self):
        v_bar = self.verticalScrollBar()
        if not v_bar or v_bar.maximum() == 0:
            return

        w = self.viewport().width()
        h = self.viewport().height()
        if w <= 0 or h <= 0:
            return

        painter = QPainter(self.viewport())
        fade_h = min(self.fade_height, h // 4)

        if v_bar.value() > 0:
            top_grad = QLinearGradient(0, 0, 0, fade_h)
            top_grad.setColorAt(0.0, self._fade_color)
            transparent_color = QColor(self._fade_color)
            transparent_color.setAlpha(0)
            top_grad.setColorAt(1.0, transparent_color)
            painter.fillRect(0, 0, w, fade_h, top_grad)

        if v_bar.value() < v_bar.maximum():
            bottom_grad = QLinearGradient(0, h - fade_h, 0, h)
            transparent_color = QColor(self._fade_color)
            transparent_color.setAlpha(0)
            bottom_grad.setColorAt(0.0, transparent_color)
            bottom_grad.setColorAt(1.0, self._fade_color)
            painter.fillRect(0, h - fade_h, w, fade_h, bottom_grad)

        painter.end()

class ModernScrollArea(FadingScrollArea):
    def __init__(self, widget: QWidget, parent=None, fade_height: int = 28, fade_color: str | QColor = COLOR_NEUTRAL_950):
        super().__init__(widget=widget, parent=parent, fade_height=fade_height, fade_color=fade_color)

class ExpandableCard(QFrame):
    def __init__(self, title: str, desc: str = "", icon_name: str = "", parent=None, switch_enabled: bool = True, description: str = ""):
        super().__init__(parent)
        final_desc = description if description else desc
        self.setProperty("role", "card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(*MARGIN_NONE)
        self.main_layout.setSpacing(SPACING_NONE)

        self._icon_up = get_icon_colored("chevron-up-filled.svg", COLOR_NEUTRAL_400, 20)
        self._icon_down = get_icon_colored("chevron-down-filled.svg", COLOR_NEUTRAL_400, 20)
        self._is_expanded = False

        self.header_widget = QWidget(self)
        self.header_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.header_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        h_layout = QHBoxLayout(self.header_widget)
        h_layout.setContentsMargins(*MARGIN_MD)
        h_layout.setSpacing(SPACING_SM)

        if icon_name:
            self.lbl_icon = QLabel(self.header_widget)
            self.lbl_icon.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_400, 24))
            h_layout.addWidget(self.lbl_icon, alignment=Qt.AlignmentFlag.AlignTop)
        else:
            self.lbl_icon = None

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(*MARGIN_NONE)
        text_layout.setSpacing(SPACING_2XS)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_title = QLabel(title, self.header_widget)
        self.lbl_title.setProperty("role", "h3")

        self.lbl_desc = QLabel(final_desc, self.header_widget)
        self.lbl_desc.setProperty("role", "body")
        self.lbl_desc.setWordWrap(True)
        if not final_desc:
            self.lbl_desc.hide()

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_desc)
        h_layout.addLayout(text_layout, stretch=1)

        self.switch = ModernSwitch(self.header_widget)
        self.switch_enable = self.switch
        if not switch_enabled:
            self.switch.hide()
        h_layout.addWidget(self.switch, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.btn_expand = QPushButton(self.header_widget)
        self.btn_expand.setIcon(self._icon_down)
        self.btn_expand.setIconSize(QSize(20, 20))
        self.btn_expand.setFixedSize(30, 30)
        self.btn_expand.setProperty("role", "btn_ghost")
        self.btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expand.clicked.connect(self.toggle_expand)
        h_layout.addWidget(self.btn_expand, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.header_widget.mousePressEvent = self._handle_header_click

        self.main_layout.addWidget(self.header_widget)

        self.divider = ModernDivider(self)
        self.divider.hide()
        self.main_layout.addWidget(self.divider)
        self.body_widget = QWidget(self)
        self.body_layout = QVBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(*MARGIN_MD)
        self.body_layout.setSpacing(SPACING_MD)
        self.body_widget.hide()
        self.main_layout.addWidget(self.body_widget)

    def add_widget(self, widget: QWidget, *args, **kwargs):
        self.body_layout.addWidget(widget, *args, **kwargs)

    def add_layout(self, layout, *args, **kwargs):
        self.body_layout.addLayout(layout, *args, **kwargs)

    def _handle_header_click(self, event):
        child = self.header_widget.childAt(event.pos())
        if child not in (self.switch, self.btn_expand) and not self.switch.isAncestorOf(child):
            self.toggle_expand()
        event.accept()

    def is_expanded(self) -> bool:
        return self._is_expanded

    def toggle_expand(self):
        self.set_expanded(not self._is_expanded)

    def set_expanded(self, expanded: bool):
        self._is_expanded = bool(expanded)
        self.body_widget.setVisible(self._is_expanded)
        self.divider.setVisible(self._is_expanded)
        self.btn_expand.setIcon(self._icon_up if self._is_expanded else self._icon_down)
        if self._is_expanded:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        else:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

class ExpandableSettingCard(ExpandableCard):
    updated = Signal(str, object)

    def __init__(self, card_id: str, title: str, desc: str, icon_name: str, has_amount: bool = True, i18n=None, parent=None):
        super().__init__(title=title, desc=desc, icon_name=icon_name, parent=parent, switch_enabled=True)
        self.i18n = i18n
        self.card_id = card_id
        self.has_amount = has_amount
        self._is_loading = True

        self.switch.toggled.connect(self._emit_update)
        self._build_body()
        self._is_loading = False

    def _build_body(self):
        b_layout = self.body_layout
        
        lbl_gen = QLabel(self.i18n.get("spam.card.config_title"))
        lbl_gen.setProperty("role", "h3")
        b_layout.addWidget(lbl_gen)
        
        platforms_layout = QHBoxLayout()
        platforms_layout.setSpacing(SPACING_XL)
        lbl_platforms = QLabel(self.i18n.get("spam.card.platforms"))
        lbl_platforms.setProperty("role", "body")
        platforms_layout.addWidget(lbl_platforms)

        kick_layout = QHBoxLayout()
        kick_layout.setSpacing(SPACING_SM)
        lbl_kick = QLabel(self.i18n.get("spam.card.platform_kick"))
        lbl_kick.setProperty("role", "body")
        self.switch_kick = ModernSwitch()
        self.switch_kick.setChecked(True)
        self.switch_kick.toggled.connect(self._emit_update)
        kick_layout.addWidget(lbl_kick)
        kick_layout.addWidget(self.switch_kick)

        twitch_layout = QHBoxLayout()
        twitch_layout.setSpacing(SPACING_SM)
        lbl_twitch = QLabel(self.i18n.get("spam.card.platform_twitch"))
        lbl_twitch.setProperty("role", "body")
        self.switch_twitch = ModernSwitch()
        self.switch_twitch.setChecked(True)
        self.switch_twitch.toggled.connect(self._emit_update)
        twitch_layout.addWidget(lbl_twitch)
        twitch_layout.addWidget(self.switch_twitch)

        platforms_layout.addLayout(kick_layout)
        platforms_layout.addLayout(twitch_layout)
        platforms_layout.addStretch()
        b_layout.addLayout(platforms_layout)
        
        options_layout = QGridLayout()
        options_layout.setHorizontalSpacing(SPACING_XL)
        options_layout.setVerticalSpacing(SPACING_XS)
        
        lbl_pen = QLabel(self.i18n.get("spam.card.action"), parent=self)
        lbl_pen.setProperty("role", "body")
        self.combo_penalty = NoWheelComboBox(self)
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_timeout"), "timeout")
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_delete"), "delete")
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_ban"), "ban")
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_warn_delete"), "warn_delete")
        self.combo_penalty.currentIndexChanged.connect(self._on_penalty_changed)
        
        self.lbl_dur = QLabel(self.i18n.get("spam.card.duration"))
        self.lbl_dur.setProperty("role", "body")
        self.spin_dur = NoWheelSpinBox(self)
        self.spin_dur.setRange(1, 10080)
        self.spin_dur.setValue(5)
        self.spin_dur.valueChanged.connect(self._emit_update)
        
        options_layout.addWidget(lbl_pen, 0, 0)
        options_layout.addWidget(self.lbl_dur, 0, 1)
        options_layout.addWidget(self.combo_penalty, 1, 0)
        options_layout.addWidget(self.spin_dur, 1, 1)
        
        lbl_exc = QLabel(self.i18n.get("spam.card.exclude"), parent=self)
        lbl_exc.setProperty("role", "body")
        self.combo_exclude = NoWheelComboBox(self)
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_none"), "none")
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_mod"), "moderator")
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_sub"), "subscriber")
        self.combo_exclude.currentIndexChanged.connect(self._emit_update)
        
        options_layout.addWidget(lbl_exc, 2, 0)
        options_layout.addWidget(self.combo_exclude, 3, 0)
        
        if self.card_id == "link_protection":
            lbl_allow = QLabel(self.i18n.get("spam.card.allowlist"))
            lbl_allow.setProperty("role", "body")
            self.txt_allowlist = QLineEdit()
            self.txt_allowlist.setPlaceholderText(self.i18n.get("spam.card.allowlist_placeholder"))
            self.txt_allowlist.textChanged.connect(self._emit_update)
            options_layout.addWidget(lbl_allow, 2, 1)
            options_layout.addWidget(self.txt_allowlist, 3, 1)
        elif self.has_amount:
            amt_label_key = "spam.card.max_amount"
            min_val, max_val, default_val = 1, 500, 10
            if self.card_id == "paragraph_protection":
                amt_label_key = "spam.card.max_characters"
                min_val, max_val, default_val = 50, 2000, 300
            elif self.card_id == "symbol_protection":
                amt_label_key = "spam.card.max_symbols"
                min_val, max_val, default_val = 3, 100, 15

            lbl_amt = QLabel(self.i18n.get(amt_label_key))
            lbl_amt.setProperty("role", "body")
            self.spin_amt = NoWheelSpinBox(self)
            self.spin_amt.setRange(min_val, max_val)
            self.spin_amt.setValue(default_val)
            self.spin_amt.valueChanged.connect(self._emit_update)
            options_layout.addWidget(lbl_amt, 2, 1)
            options_layout.addWidget(self.spin_amt, 3, 1)
            
        options_layout.setColumnStretch(0, 1)
        options_layout.setColumnStretch(1, 1)
        b_layout.addLayout(options_layout)

        self._update_duration_state()

    def _on_penalty_changed(self, *args):
        self._update_duration_state()
        self._emit_update()

    def _update_duration_state(self):
        is_timeout = (self.combo_penalty.currentData() == "timeout")
        if hasattr(self, 'lbl_dur'):
            self.lbl_dur.setEnabled(is_timeout)
        if hasattr(self, 'spin_dur'):
            self.spin_dur.setEnabled(is_timeout)

    def _emit_update(self, *args):
        if self._is_loading: return
        config = {
            "is_active": self.switch.isChecked(),
            "apply_kick": self.switch_kick.isChecked() if hasattr(self, 'switch_kick') else True,
            "apply_twitch": self.switch_twitch.isChecked() if hasattr(self, 'switch_twitch') else True,
            "penalty": self.combo_penalty.currentData(),
            "duration": self.spin_dur.value(),
            "exclude_group": self.combo_exclude.currentData(),
            "max_amount": self.spin_amt.value() if (self.has_amount and self.card_id != "link_protection") else 0,
            "allowlist": self.txt_allowlist.text() if self.card_id == "link_protection" else ""
        }
        self.updated.emit(self.card_id, config)

    def set_connected_platforms(self, connected_platforms: dict[str, bool]):
        self.connected_platforms = connected_platforms or {}
        kick_on = self.connected_platforms.get("kick", False)
        twitch_on = self.connected_platforms.get("twitch", False)
        off_tip = self.i18n.get("spam.card.platform_offline") if self.i18n else ""

        if hasattr(self, "switch_kick"):
            self.switch_kick.setEnabled(kick_on)
            if not kick_on:
                self.switch_kick.setChecked(False)
                self.switch_kick.setToolTip(off_tip)
            else:
                self.switch_kick.setToolTip("")

        if hasattr(self, "switch_twitch"):
            self.switch_twitch.setEnabled(twitch_on)
            if not twitch_on:
                self.switch_twitch.setChecked(False)
                self.switch_twitch.setToolTip(off_tip)
            else:
                self.switch_twitch.setToolTip("")

    def set_data(self, config: dict):
        self._is_loading = True
        self.switch.setChecked(config.get("is_active", False))
        kick_on = getattr(self, "connected_platforms", {}).get("kick", True)
        twitch_on = getattr(self, "connected_platforms", {}).get("twitch", True)
        if hasattr(self, 'switch_kick'):
            self.switch_kick.setChecked(config.get("apply_kick", True) if kick_on else False)
        if hasattr(self, 'switch_twitch'):
            self.switch_twitch.setChecked(config.get("apply_twitch", True) if twitch_on else False)
        index_pen = self.combo_penalty.findData(config.get("penalty", "timeout"))
        if index_pen >= 0: self.combo_penalty.setCurrentIndex(index_pen)
        self.spin_dur.setValue(config.get("duration", 300))
        index_exc = self.combo_exclude.findData(config.get("exclude_group", "none"))
        if index_exc >= 0: self.combo_exclude.setCurrentIndex(index_exc)
        if self.card_id == "link_protection":
            self.txt_allowlist.setText(config.get("allowlist", ""))
        elif self.has_amount:
            default_amt = 300 if self.card_id == "paragraph_protection" else (15 if self.card_id == "symbol_protection" else 10)
            self.spin_amt.setValue(config.get("max_amount", default_amt))
        self._update_duration_state()
        self._is_loading = False

def create_badge(text: str, state: str = "everyone", parent=None) -> QWidget:
    container = QWidget(parent)
    layout = QHBoxLayout(container)
    layout.setContentsMargins(*MARGIN_H_MD)
    layout.setSpacing(SPACING_NONE)
    layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    tag = QFrame(container)
    tag.setProperty("role", "badge")
    tag.setProperty("state", state)

    tag_layout = QHBoxLayout(tag)
    tag_layout.setContentsMargins(*MARGIN_H_SM)
    tag_layout.setSpacing(SPACING_NONE)

    lbl_txt = QLabel(text, tag)
    lbl_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tag_layout.addWidget(lbl_txt)

    layout.addWidget(tag)
    return container

