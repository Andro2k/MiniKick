# frontend\widgets\blocks.py

from PySide6.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSpinBox, QPushButton, QLineEdit
from PySide6.QtCore import Qt, Signal
from frontend.common.utils import get_icon_colored, NoWheelComboBox
from frontend.common.theme import COLOR_NEUTRAL_200, COLOR_NEUTRAL_400
from .controls import ModernSwitch

class ViewHeader(QFrame):
    def __init__(self, title_text: str, subtitle_text: str, title_color: str = None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(4)

        title = QLabel(title_text)
        title.setProperty("role", "h1")
        if title_color:
            title.setStyleSheet(f"color: {title_color};")
        
        subtitle = QLabel(subtitle_text)
        subtitle.setProperty("role", "body")
        subtitle.setWordWrap(True)
        subtitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)

class SettingRow(QWidget):
    def __init__(self, icon_name: str, title_text: str, desc_text: str, right_widget: QWidget, icon_color: str = COLOR_NEUTRAL_200, title_color: str = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=18).pixmap(18, 18))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        lbl_title = QLabel(title_text)
        lbl_title.setProperty("role", "h3")
        lbl_title.setWordWrap(True)
        if title_color:
            lbl_title.setStyleSheet(f"color: {title_color};")
        
        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)

        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

class SliderRow(QWidget):
    def __init__(self, icon_name: str, title_text: str, desc_text: str, slider_widget: QWidget, value_label: QLabel, icon_color: str = COLOR_NEUTRAL_200, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, icon_color, size=18).pixmap(18, 18))

        lbl_title = QLabel(title_text)
        lbl_title.setProperty("role", "h3")

        header_row.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_row.addStretch()
        header_row.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        lbl_desc = QLabel(desc_text)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)

        layout.addLayout(header_row)
        layout.addWidget(lbl_desc)
        layout.addWidget(slider_widget)

class StatCard(QFrame):
    def __init__(self, title_text: str, icon_name: str, initial_value: str = "-", parent=None):
        super().__init__(parent)
        self.setProperty("role", "card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.setMinimumWidth(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon_colored(icon_name, COLOR_NEUTRAL_200, size=14).pixmap(14, 14))

        self.lbl_title = QLabel(title_text)
        self.lbl_title.setProperty("role", "h3")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.lbl_value = QLabel(initial_value)
        self.lbl_value.setProperty("role", "body")
        self.lbl_value.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_value)
        layout.addStretch()

    def set_value(self, value: str):
        self.lbl_value.setText(str(value))

class ModernCard(QFrame):
    def __init__(self, parent=None, margin=8, spacing=6, orientation="vertical"):
        super().__init__(parent)
        self.setProperty("role", "card")
        
        if orientation == "horizontal":
            self.card_layout = QHBoxLayout(self)
        else:
            self.card_layout = QVBoxLayout(self)
            
        self.card_layout.setContentsMargins(margin, margin, margin, margin)
        self.card_layout.setSpacing(spacing)
        
    def addWidget(self, widget, *args, **kwargs):
        self.card_layout.addWidget(widget, *args, **kwargs)
        
    def addLayout(self, layout, *args, **kwargs):
        self.card_layout.addLayout(layout, *args, **kwargs)

    def addSpacing(self, spacing: int):
        self.card_layout.addSpacing(spacing)

    def addStretch(self, stretch: int = 0):
        self.card_layout.addStretch(stretch)

class ModernScrollArea(QScrollArea):
    def __init__(self, widget: QWidget, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(widget)

class ExpandableSettingCard(QFrame):
    updated = Signal(str, dict)

    def __init__(self, card_id: str, title: str, desc: str, icon_name: str, has_amount: bool = True, i18n=None):
        super().__init__()
        self.i18n = i18n
        self.card_id = card_id
        self.has_amount = has_amount
        self._is_loading = True
        
        self.setProperty("role", "card")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._build_header(title, desc, icon_name)
        self._build_body()
        
        self.body_widget.hide() 
        self._is_loading = False

    def _build_header(self, title: str, desc: str, icon_name: str):
        self.header_widget = QWidget()
        self.header_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        h_layout = QHBoxLayout(self.header_widget)
        h_layout.setContentsMargins(8, 8, 8, 8)
        h_layout.setSpacing(6)
        
        lbl_icon = QLabel()
        lbl_icon.setPixmap(get_icon_colored(icon_name, COLOR_NEUTRAL_400, 24).pixmap(24, 24))
        h_layout.addWidget(lbl_icon)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "h3")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)
        h_layout.addLayout(text_layout, stretch=1)
        
        self.switch = ModernSwitch()
        self.switch.toggled.connect(self._emit_update)
        h_layout.addWidget(self.switch)
        
        self.btn_expand = QPushButton()
        self.btn_expand.setIcon(get_icon_colored("chevron-down.svg", COLOR_NEUTRAL_400, 20))
        self.btn_expand.setFixedSize(30, 30)
        self.btn_expand.setProperty("role", "btn_ghost")
        self.btn_expand.clicked.connect(self.toggle_expand)
        h_layout.addWidget(self.btn_expand)
        
        self.main_layout.addWidget(self.header_widget)

    def _build_body(self):
        self.body_widget = QWidget()
        b_layout = QVBoxLayout(self.body_widget)
        b_layout.setContentsMargins(12, 12, 12, 12)
        b_layout.setSpacing(8)
        
        lbl_gen = QLabel(self.i18n.get("spam.card.config_title"))
        lbl_gen.setProperty("role", "h3")
        b_layout.addWidget(lbl_gen)
        
        options_layout = QHBoxLayout()
        options_layout.setSpacing(16)
        
        col_left = QVBoxLayout()
        col_left.setSpacing(8)
        col_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        col_right = QVBoxLayout()
        col_right.setSpacing(8)
        col_right.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lbl_pen = QLabel(self.i18n.get("spam.card.action"))
        lbl_pen.setProperty("role", "body")
        self.combo_penalty = NoWheelComboBox()
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_timeout"), "timeout")
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_delete"), "delete")
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_ban"), "ban")
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_warn_delete"), "warn_delete")
        self.combo_penalty.currentIndexChanged.connect(self._emit_update)
        col_left.addWidget(lbl_pen)
        col_left.addWidget(self.combo_penalty)
        
        col_left.addSpacing(4)
        
        lbl_exc = QLabel(self.i18n.get("spam.card.exclude"))
        lbl_exc.setProperty("role", "body")
        self.combo_exclude = NoWheelComboBox()
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_none"), "none")
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_mod"), "moderator")
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_sub"), "subscriber")
        self.combo_exclude.currentIndexChanged.connect(self._emit_update)
        col_left.addWidget(lbl_exc)
        col_left.addWidget(self.combo_exclude)
        
        lbl_dur = QLabel(self.i18n.get("spam.card.duration"))
        lbl_dur.setProperty("role", "body")
        self.spin_dur = QSpinBox()
        self.spin_dur.setRange(1, 10080)
        self.spin_dur.setValue(5)
        self.spin_dur.valueChanged.connect(self._emit_update)
        col_right.addWidget(lbl_dur)
        col_right.addWidget(self.spin_dur)
        
        if self.card_id == "link_protection":
            col_right.addSpacing(4)
            lbl_allow = QLabel(self.i18n.get("spam.card.allowlist"))
            lbl_allow.setProperty("role", "body")
            self.txt_allowlist = QLineEdit()
            self.txt_allowlist.setPlaceholderText(self.i18n.get("spam.card.allowlist_placeholder"))
            self.txt_allowlist.textChanged.connect(self._emit_update)
            col_right.addWidget(lbl_allow)
            col_right.addWidget(self.txt_allowlist)
        elif self.has_amount:
            col_right.addSpacing(4)
            
            lbl_amt = QLabel(self.i18n.get("spam.card.max_amount"))
            lbl_amt.setProperty("role", "body")
            self.spin_amt = QSpinBox()
            self.spin_amt.setRange(1, 500)
            self.spin_amt.setValue(10)
            self.spin_amt.valueChanged.connect(self._emit_update)
            col_right.addWidget(lbl_amt)
            col_right.addWidget(self.spin_amt)
            
        options_layout.addLayout(col_left, stretch=1)
        options_layout.addLayout(col_right, stretch=1)
        b_layout.addLayout(options_layout)

        self.main_layout.addWidget(self.body_widget)

    def toggle_expand(self):
        is_visible = self.body_widget.isVisible()
        self.body_widget.setVisible(not is_visible)
        icon_name = "chevron-up.svg" if not is_visible else "chevron-down.svg"
        self.btn_expand.setIcon(get_icon_colored(icon_name, COLOR_NEUTRAL_400, 20))

    def _emit_update(self, *args):
        if self._is_loading: return
        config = {
            "is_active": self.switch.isChecked(),
            "penalty": self.combo_penalty.currentData(),
            "duration": self.spin_dur.value(),
            "exclude_group": self.combo_exclude.currentData(),
            "max_amount": self.spin_amt.value() if (self.has_amount and self.card_id != "link_protection") else 0,
            "allowlist": self.txt_allowlist.text() if self.card_id == "link_protection" else ""
        }
        self.updated.emit(self.card_id, config)

    def set_data(self, config: dict):
        self._is_loading = True
        self.switch.setChecked(config.get("is_active", False))
        index_pen = self.combo_penalty.findData(config.get("penalty", "timeout"))
        if index_pen >= 0: self.combo_penalty.setCurrentIndex(index_pen)
        self.spin_dur.setValue(config.get("duration", 300))
        index_exc = self.combo_exclude.findData(config.get("exclude_group", "none"))
        if index_exc >= 0: self.combo_exclude.setCurrentIndex(index_exc)
        if self.card_id == "link_protection":
            self.txt_allowlist.setText(config.get("allowlist", ""))
        elif self.has_amount:
            self.spin_amt.setValue(config.get("max_amount", 10))
        self._is_loading = False
