# frontend/views/spam_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QComboBox, QSpinBox, QScrollArea, QPushButton)
from PySide6.QtCore import Qt, Signal

from frontend.components.blocks import ViewHeader
from frontend.components.controls import ModernSwitch
from frontend.theme import COLOR_ACCENT, COLOR_TEXT_SECONDARY
from frontend.utils import get_icon_colored

class SpamFilterCard(QFrame):
    """Tarjeta individual expandible (Acordeón) para cada filtro."""
    updated = Signal(str, dict)

    def __init__(self, filter_id: str, title: str, desc: str, icon_name: str, has_amount: bool = True, i18n=None):
        super().__init__()
        self.i18n = i18n
        self.filter_id = filter_id
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
        h_layout.setContentsMargins(10, 10, 10, 10)
        h_layout.setSpacing(10)
        
        lbl_icon = QLabel()
        lbl_icon.setPixmap(get_icon_colored(icon_name, COLOR_TEXT_SECONDARY, 24).pixmap(24, 24))
        h_layout.addWidget(lbl_icon)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "h3")
        lbl_desc = QLabel(desc)
        lbl_desc.setProperty("role", "body")
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)
        h_layout.addLayout(text_layout, stretch=1)
        
        self.switch = ModernSwitch()
        self.switch.toggled.connect(self._emit_update)
        h_layout.addWidget(self.switch)
        
        self.btn_expand = QPushButton()
        self.btn_expand.setIcon(get_icon_colored("chevron-right-pipe.svg", COLOR_TEXT_SECONDARY, 20))
        self.btn_expand.setFixedSize(30, 30)
        self.btn_expand.setProperty("role", "btn_ghost")
        self.btn_expand.clicked.connect(self.toggle_expand)
        h_layout.addWidget(self.btn_expand)
        
        self.main_layout.addWidget(self.header_widget)

    def _build_body(self):
        self.body_widget = QWidget()
        self.body_widget.setObjectName("SpamCardBody")
        b_layout = QVBoxLayout(self.body_widget)
        b_layout.setContentsMargins(12, 12, 12, 12)
        b_layout.setSpacing(12)
        
        lbl_gen = QLabel(self.i18n.get("spam.card.config_title"))
        lbl_gen.setProperty("role", "h3")
        b_layout.addWidget(lbl_gen)
        
        row1 = QHBoxLayout()
        row1.setSpacing(20)
        
        col_pen = QVBoxLayout()
        lbl_pen = QLabel(self.i18n.get("spam.card.action"))
        lbl_pen.setProperty("role", "subtitle")
        self.combo_penalty = QComboBox()
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_timeout"), "timeout")
        self.combo_penalty.addItem(self.i18n.get("spam.card.action_delete"), "delete")
        self.combo_penalty.currentIndexChanged.connect(self._emit_update)
        col_pen.addWidget(lbl_pen)
        col_pen.addWidget(self.combo_penalty)
        
        col_dur = QVBoxLayout()
        lbl_dur = QLabel(self.i18n.get("spam.card.duration"))
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
        lbl_exc = QLabel(self.i18n.get("spam.card.exclude"))
        lbl_exc.setProperty("role", "subtitle")
        self.combo_exclude = QComboBox()
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_none"), "none")
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_mod"), "moderator")
        self.combo_exclude.addItem(self.i18n.get("spam.card.exclude_sub"), "subscriber")
        self.combo_exclude.currentIndexChanged.connect(self._emit_update)
        col_exc.addWidget(lbl_exc)
        col_exc.addWidget(self.combo_exclude)
        b_layout.addLayout(col_exc)
        
        if self.has_amount:
            col_amt = QVBoxLayout()
            lbl_amt = QLabel(self.i18n.get("spam.card.max_amount"))
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
        icon_name = "chevron-up.svg" if not is_visible else "chevron-right-pipe.svg"
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
        self.updated.emit(self.filter_id, config)

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

class SpamView(QWidget):
    filter_updated = Signal(str, dict)

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self.cards = {}
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        header = ViewHeader(
            title_text=self.i18n.get("spam.header.title"),
            subtitle_text=self.i18n.get("spam.header.subtitle"),
            icon_name="shield-half.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(header)
        self.main_layout.addSpacing(10)

        self._add_card("caps_protection", self.i18n.get("spam.filters.caps.title"), self.i18n.get("spam.filters.caps.desc"), "adjustments-alt.svg")
        self._add_card("link_protection", self.i18n.get("spam.filters.link.title"), self.i18n.get("spam.filters.link.desc"), "link.svg", has_amount=False)
        self._add_card("emote_protection", self.i18n.get("spam.filters.emote.title"), self.i18n.get("spam.filters.emote.desc"), "star.svg")
        self._add_card("paragraph_protection", self.i18n.get("spam.filters.paragraph.title"), self.i18n.get("spam.filters.paragraph.desc"), "file-text.svg")
        self._add_card("symbol_protection", self.i18n.get("spam.filters.symbol.title"), self.i18n.get("spam.filters.symbol.desc"), "hash.svg")
        
        self.main_layout.addStretch()
        scroll.setWidget(content)
        base_layout.addWidget(scroll)

    def _add_card(self, f_id, title, desc, icon, has_amount=True):
        card = SpamFilterCard(f_id, title, desc, icon, has_amount, self.i18n)
        card.updated.connect(self.filter_updated.emit)
        self.cards[f_id] = card
        self.main_layout.addWidget(card)

    def populate_filters(self, filters_data: dict):
        for f_id, card in self.cards.items():
            if f_id in filters_data:
                card.set_data(filters_data[f_id])