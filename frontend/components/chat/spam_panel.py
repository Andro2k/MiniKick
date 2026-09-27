# frontend\components\chat\spam_panel.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from frontend.widgets import ExpandableSettingCard, SectionHeader
from frontend.common import MARGIN_TAB_PANEL, SPACING_MD

_SPAM_FILTER_SPECS: tuple[tuple[str, str, str, str, bool], ...] = (
    ("caps_protection", "spam.filters.caps.title", "spam.filters.caps.desc", "text-filled.svg", True),
    ("link_protection", "spam.filters.link.title", "spam.filters.link.desc", "link-filled.svg", False),
    ("emote_protection", "spam.filters.emote.title", "spam.filters.emote.desc", "star-filled.svg", True),
    ("paragraph_protection", "spam.filters.paragraph.title", "spam.filters.paragraph.desc", "file-text-filled.svg", True),
    ("symbol_protection", "spam.filters.symbol.title", "spam.filters.symbol.desc", "hashtag-filled.svg", True),
    ("repetition_protection", "spam.filters.repetition.title", "spam.filters.repetition.desc", "repeat-filled.svg", True),
)

class ChatSpamPanel(QWidget):
    filter_updated = Signal(str, object)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.setProperty("role", "tab_panel")
        self.i18n = i18n
        self.cards: dict[str, ExpandableSettingCard] = {}
        self.connected_platforms: dict[str, bool] = {}
        self._setup_ui()

    def _setup_ui(self):
        panel = QVBoxLayout(self)
        panel.setContentsMargins(*MARGIN_TAB_PANEL)
        panel.setSpacing(SPACING_MD)
        self.panel_layout = panel

        header_widget = SectionHeader(self.i18n.get("spam.header.title"), parent=self, first=True)
        panel.addWidget(header_widget)

        subtitle_lbl = QLabel(self.i18n.get("spam.header.subtitle"), parent=self)
        subtitle_lbl.setProperty("role", "caption")
        subtitle_lbl.setWordWrap(True)
        panel.addWidget(subtitle_lbl)

        for f_id, title_key, desc_key, icon, has_amount in _SPAM_FILTER_SPECS:
            self._add_card(
                f_id,
                self.i18n.get(title_key),
                self.i18n.get(desc_key),
                icon,
                has_amount=has_amount
            )

        panel.addStretch(1)

    def _add_card(self, f_id: str, title: str, desc: str, icon: str, has_amount: bool = True):
        card = ExpandableSettingCard(f_id, title, desc, icon, has_amount, self.i18n, parent=self)
        if self.connected_platforms:
            card.set_connected_platforms(self.connected_platforms)
        card.updated.connect(self.filter_updated.emit)
        self.cards[f_id] = card
        self.panel_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

    def set_connected_platforms(self, connected_platforms: dict[str, bool]):
        self.connected_platforms = connected_platforms or {}
        for card in self.cards.values():
            card.set_connected_platforms(self.connected_platforms)

    def populate_filters(self, filters_data: dict):
        self.setUpdatesEnabled(False)
        try:
            for f_id, card in self.cards.items():
                if f_id in filters_data:
                    card.set_data(filters_data[f_id])
        finally:
            self.setUpdatesEnabled(True)
