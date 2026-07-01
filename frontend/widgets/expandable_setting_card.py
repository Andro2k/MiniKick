# frontend\widgets\expandable_setting_card.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QComboBox, QSpinBox, QPushButton)
from PySide6.QtCore import Qt, Signal

from frontend.widgets.controls_component import ModernSwitch
from frontend.common.theme import COLOR_TEXT_SECONDARY
from frontend.common.utils import get_icon_colored

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
        lbl_icon.setPixmap(get_icon_colored(icon_name, COLOR_TEXT_SECONDARY, 24).pixmap(24, 24))
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
        self.btn_expand.setIcon(get_icon_colored("chevron-down.svg", COLOR_TEXT_SECONDARY, 20))
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
        
        lbl_gen = QLabel(self.i18n.get("spam.card.config_title") if self.i18n else "Configuration")
        lbl_gen.setProperty("role", "h3")
        b_layout.addWidget(lbl_gen)
        
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        
        col_pen = QVBoxLayout()
        lbl_pen = QLabel(self.i18n.get("spam.card.action") if self.i18n else "Action")
        lbl_pen.setProperty("role", "subtitle")
        self.combo_penalty = QComboBox()
        if self.i18n:
            self.combo_penalty.addItem(self.i18n.get("spam.card.action_timeout"), "timeout")
            self.combo_penalty.addItem(self.i18n.get("spam.card.action_delete"), "delete")
        else:
            self.combo_penalty.addItem("Timeout", "timeout")
            self.combo_penalty.addItem("Delete", "delete")
        self.combo_penalty.currentIndexChanged.connect(self._emit_update)
        col_pen.addWidget(lbl_pen)
        col_pen.addWidget(self.combo_penalty)
        
        col_dur = QVBoxLayout()
        lbl_dur = QLabel(self.i18n.get("spam.card.duration") if self.i18n else "Duration")
        lbl_dur.setProperty("role", "subtitle")
        self.spin_dur = QSpinBox()
        self.spin_dur.setRange(10, 86400)
        self.spin_dur.setValue(300)
        self.spin_dur.valueChanged.connect(self._emit_update)
        col_dur.addWidget(lbl_dur)
        col_dur.addWidget(self.spin_dur)
        
        row1.addLayout(col_pen, stretch=1)
        row1.addLayout(col_dur, stretch=1)
        b_layout.addLayout(row1)
        
        col_exc = QVBoxLayout()
        lbl_exc = QLabel(self.i18n.get("spam.card.exclude") if self.i18n else "Exclude")
        lbl_exc.setProperty("role", "subtitle")
        self.combo_exclude = QComboBox()
        if self.i18n:
            self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_none"), "none")
            self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_mod"), "moderator")
            self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_sub"), "subscriber")
        else:
            self.combo_exclude.addItem("None", "none")
            self.combo_exclude.addItem("Moderators", "moderator")
            self.combo_exclude.addItem("Subscribers", "subscriber")
        self.combo_exclude.currentIndexChanged.connect(self._emit_update)
        col_exc.addWidget(lbl_exc)
        col_exc.addWidget(self.combo_exclude)
        b_layout.addLayout(col_exc)
        
        if self.has_amount:
            col_amt = QVBoxLayout()
            lbl_amt = QLabel(self.i18n.get("spam.card.max_amount") if self.i18n else "Max Amount")
            lbl_amt.setProperty("role", "subtitle")
            self.spin_amt = QSpinBox()
            self.spin_amt.setRange(1, 500)
            self.spin_amt.setValue(10)
            self.spin_amt.valueChanged.connect(self._emit_update)
            col_amt.addWidget(lbl_amt)
            col_amt.addWidget(self.spin_amt)
            b_layout.addLayout(col_amt)

        self.main_layout.addWidget(self.body_widget)

    def toggle_expand(self):
        is_visible = self.body_widget.isVisible()
        self.body_widget.setVisible(not is_visible)
        icon_name = "chevron-up.svg" if not is_visible else "chevron-down.svg"
        self.btn_expand.setIcon(get_icon_colored(icon_name, COLOR_TEXT_SECONDARY, 20))

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
