# frontend\components\dialogs\severity_card.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from frontend.common import MARGIN_MD, MARGIN_NONE, SPACING_MD, SPACING_2XS

class SeverityCard(QFrame):
    clicked = Signal(str)

    def __init__(self, key: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setProperty("role", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_MD)
        layout.setSpacing(SPACING_MD)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(SPACING_2XS)
        text_layout.setContentsMargins(*MARGIN_NONE)

        self.lbl_title = QLabel(title)
        self.lbl_title.setProperty("role", "body")
        self.lbl_title.setProperty("state", "bold")

        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setProperty("role", "caption")
        self.lbl_sub.setWordWrap(True)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_sub)
        layout.addLayout(text_layout, 1)

    def set_selected(self, selected: bool):
        if selected:
            self.lbl_title.setProperty("state", "success")
        else:
            self.lbl_title.setProperty("state", "bold")
        self.lbl_title.style().unpolish(self.lbl_title)
        self.lbl_title.style().polish(self.lbl_title)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)
