# frontend\dialogs\whats_new_dialog.py

from typing import List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from frontend.dialogs.base_dialog import ModernModal
from frontend.widgets import ModernButton, ModernCard
from frontend.common import (
    get_assets_path, get_pixmap_colored,
    COLOR_ORANGE, COLOR_WHITE,
    MARGIN_NONE, MARGIN_MD, SPACING_XS, SPACING_SM
)

class WhatsNewDialog(ModernModal):
    def __init__(
        self,
        i18n,
        highlights: List[Dict[str, str]],
        is_first_launch: bool = False,
        app_version: str = "",
        parent=None
    ):
        self.i18n = i18n
        self.highlights = highlights or []
        self.is_first_launch = is_first_launch
        self.app_version = app_version

        if self.is_first_launch:
            dialog_title = self.i18n.get("whats_new.dialog.title_welcome")
            self._subtitle_text = self.i18n.get("whats_new.dialog.subtitle_welcome")
            self._btn_text = self.i18n.get("whats_new.dialog.btn_start")
        else:
            title_tpl = self.i18n.get("whats_new.dialog.title_update")
            clean_ver = self.app_version.lstrip("vV") if self.app_version else ""
            dialog_title = title_tpl.replace("{version}", clean_ver)
            self._subtitle_text = self.i18n.get("whats_new.dialog.subtitle_update")
            self._btn_text = self.i18n.get("whats_new.dialog.btn_got_it")

        super().__init__(
            title=dialog_title,
            icon_path=get_assets_path("icons/star-filled.svg"),
            icon_bg_color=COLOR_ORANGE,
            width=540,
            parent=parent
        )
        self.set_dialog_state("accent", QColor(255, 107, 53, 50))
        self._setup_content()

    def _setup_content(self):
        lbl_subtitle = QLabel(self._subtitle_text, parent=self.container)
        lbl_subtitle.setProperty("role", "body")
        lbl_subtitle.setWordWrap(True)
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(lbl_subtitle)

        scroll_area = QScrollArea(parent=self.container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(380)

        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(*MARGIN_NONE)
        cards_layout.setSpacing(SPACING_SM)

        for item in self.highlights:
            card = self._create_highlight_card(item, parent=cards_container)
            cards_layout.addWidget(card)

        scroll_area.setWidget(cards_container)
        self.content_layout.addWidget(scroll_area)

        btn_action = ModernButton(
            self._btn_text,
            role="action_accent_solid",
            icon_name="check-filled.svg",
            icon_color=COLOR_WHITE,
            parent=self.container
        )
        btn_action.setFixedHeight(40)
        btn_action.clicked.connect(self.accept)
        self.content_layout.addWidget(btn_action)

    def _create_highlight_card(self, item: Dict[str, str], parent: QWidget) -> ModernCard:
        card = ModernCard(parent=parent, margin=MARGIN_MD, spacing=SPACING_SM, orientation="horizontal")
        card.setProperty("role", "whats_new_card")

        icon_name = item.get("icon", "star-filled.svg")
        lbl_icon = QLabel(parent=card)
        lbl_icon.setPixmap(get_pixmap_colored(icon_name, COLOR_ORANGE, size=24))
        lbl_icon.setFixedSize(28, 28)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.addWidget(lbl_icon)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(*MARGIN_NONE)
        text_col.setSpacing(SPACING_XS)

        title_key = item.get("title_key", "")
        desc_key = item.get("desc_key", "")

        title_text = item.get("title") or (self.i18n.get(title_key) if title_key else "")
        desc_text = item.get("desc") or (self.i18n.get(desc_key) if desc_key else "")

        lbl_title = QLabel(title_text, parent=card)
        lbl_title.setProperty("role", "h3")

        lbl_desc = QLabel(desc_text, parent=card)
        lbl_desc.setProperty("role", "caption")
        lbl_desc.setWordWrap(True)

        text_col.addWidget(lbl_title)
        text_col.addWidget(lbl_desc)
        card.addLayout(text_col, stretch=1)

        return card
