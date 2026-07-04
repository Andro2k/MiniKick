# frontend\views\spam_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFrame, QScrollArea)
from PySide6.QtCore import Qt, Signal

from frontend.widgets.blocks_component import ViewHeader
from frontend.widgets.expandable_setting_card import ExpandableSettingCard
from frontend.common.theme import COLOR_TEXT_PRIMARY

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
            icon_color=COLOR_TEXT_PRIMARY
        )
        self.main_layout.addWidget(header)
        self.main_layout.addSpacing(10)

        self._add_card("caps_protection", self.i18n.get("spam.filters.caps.title"), self.i18n.get("spam.filters.caps.desc"), "adjustments.svg")
        self._add_card("link_protection", self.i18n.get("spam.filters.link.title"), self.i18n.get("spam.filters.link.desc"), "link.svg", has_amount=False)
        self._add_card("emote_protection", self.i18n.get("spam.filters.emote.title"), self.i18n.get("spam.filters.emote.desc"), "star.svg")
        self._add_card("paragraph_protection", self.i18n.get("spam.filters.paragraph.title"), self.i18n.get("spam.filters.paragraph.desc"), "file-text.svg")
        self._add_card("symbol_protection", self.i18n.get("spam.filters.symbol.title"), self.i18n.get("spam.filters.symbol.desc"), "hash.svg")
        self._add_card("repetition_protection", self.i18n.get("spam.filters.repetition.title"), self.i18n.get("spam.filters.repetition.desc"), "repeat.svg")
        
        self.main_layout.addStretch()
        scroll.setWidget(content)
        base_layout.addWidget(scroll)

    def _add_card(self, f_id, title, desc, icon, has_amount=True):
        card = ExpandableSettingCard(f_id, title, desc, icon, has_amount, self.i18n)
        card.updated.connect(self.filter_updated.emit)
        self.cards[f_id] = card
        self.main_layout.addWidget(card)

    def populate_filters(self, filters_data: dict):
        for f_id, card in self.cards.items():
            if f_id in filters_data:
                card.set_data(filters_data[f_id])