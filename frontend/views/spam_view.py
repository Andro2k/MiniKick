# frontend\views\spam_view.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QBoxLayout, QWidget, QVBoxLayout
from frontend.widgets import BaseView, ExpandableSettingCard

class SpamView(BaseView):
    filter_updated = Signal(str, dict)

    def __init__(self, i18n):
        super().__init__(
            i18n=i18n,
            title_key="spam.header.title",
            subtitle_key="spam.header.subtitle"
        )
        self.cards = {}
        self._setup_ui()

    def _setup_ui(self):
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(16)

        self.columns_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        self.columns_layout.setSpacing(16)

        col1 = QWidget()
        self.col1_layout = QVBoxLayout(col1)
        self.col1_layout.setContentsMargins(0, 0, 0, 0)
        self.col1_layout.setSpacing(16)
        self.col1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        col2 = QWidget()
        self.col2_layout = QVBoxLayout(col2)
        self.col2_layout.setContentsMargins(0, 0, 0, 0)
        self.col2_layout.setSpacing(16)
        self.col2_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.columns_layout.addWidget(col1, stretch=1)
        self.columns_layout.addWidget(col2, stretch=1)

        self.body_layout.addLayout(self.columns_layout)

        self._add_card("caps_protection", self.i18n.get("spam.filters.caps.title"), self.i18n.get("spam.filters.caps.desc"), "adjustments.svg", column=1)
        self._add_card("link_protection", self.i18n.get("spam.filters.link.title"), self.i18n.get("spam.filters.link.desc"), "link.svg", has_amount=False, column=1)
        self._add_card("emote_protection", self.i18n.get("spam.filters.emote.title"), self.i18n.get("spam.filters.emote.desc"), "star.svg", column=1)
        
        self._add_card("paragraph_protection", self.i18n.get("spam.filters.paragraph.title"), self.i18n.get("spam.filters.paragraph.desc"), "file-text.svg", column=2)
        self._add_card("symbol_protection", self.i18n.get("spam.filters.symbol.title"), self.i18n.get("spam.filters.symbol.desc"), "hash.svg", column=2)
        self._add_card("repetition_protection", self.i18n.get("spam.filters.repetition.title"), self.i18n.get("spam.filters.repetition.desc"), "repeat.svg", column=2)

        self.main_layout.addWidget(self.body_container)
        self.main_layout.addStretch()

    def _add_card(self, f_id, title, desc, icon, has_amount=True, column=1):
        card = ExpandableSettingCard(f_id, title, desc, icon, has_amount, self.i18n)
        card.updated.connect(self.filter_updated.emit)
        self.cards[f_id] = card
        
        if column == 1:
            self.col1_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)
        else:
            self.col2_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

    def populate_filters(self, filters_data: dict):
        for f_id, card in self.cards.items():
            if f_id in filters_data:
                card.set_data(filters_data[f_id])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        if hasattr(self, 'columns_layout'):
            if width < 900:
                self.columns_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            else:
                self.columns_layout.setDirection(QBoxLayout.Direction.LeftToRight)
