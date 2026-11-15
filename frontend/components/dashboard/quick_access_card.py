# frontend\components\dashboard\quick_access_card.py
"""Tarjeta de acceso rápido a un módulo de la aplicación."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy
from frontend.common import Palette, Size, get_pixmap_colored
from frontend.widgets import ClickableFrame, create_col_layout, create_row_layout


class QuickAccessCard(ClickableFrame):
    def __init__(self, view_name: str, icon_name: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.view_name = view_name
        self.setProperty("role", "quick_access_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = create_col_layout(spacing=Size.SPACING_SM, margins=Size.Margin.MRG_MED, parent=self)
        header = create_row_layout(spacing=Size.SPACING_SM)
        icon = QLabel(self)
        icon.setPixmap(get_pixmap_colored(icon_name, Palette.NEUTRAL_050))
        self.lbl_title = QLabel(title, self)
        self.lbl_title.setProperty("role", "text_h2")
        header.addWidget(icon)
        header.addWidget(self.lbl_title, 1)
        layout.addLayout(header)

        self.lbl_description = QLabel(description, self)
        self.lbl_description.setProperty("role", "text_caption")
        self.lbl_description.setWordWrap(True)
        layout.addWidget(self.lbl_description)
        layout.addStretch(1)
