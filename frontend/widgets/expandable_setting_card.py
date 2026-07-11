# frontend\widgets\expandable_setting_card.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QSpinBox, QPushButton)
from PySide6.QtCore import Qt, Signal

from frontend.widgets.controls_component import ModernSwitch
from frontend.common.theme import COLOR_NEUTRAL_400
from frontend.common.utils import get_icon_colored, NoWheelComboBox

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
        self.spin_dur.setRange(10, 86400)
        self.spin_dur.setValue(300)
        self.spin_dur.valueChanged.connect(self._emit_update)
        col_right.addWidget(lbl_dur)
        col_right.addWidget(self.spin_dur)
        
        if self.has_amount:
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
            "max_amount": self.spin_amt.value() if self.has_amount else 0
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
        if self.has_amount:
            self.spin_amt.setValue(config.get("max_amount", 10))
        self._is_loading = False
