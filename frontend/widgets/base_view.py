# frontend\widgets\base_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PySide6.QtCore import Qt
from .blocks import ViewHeader

class BaseView(QWidget):
    def __init__(self, i18n, title_key: str, subtitle_key: str, parent=None):
        super().__init__(parent)
        self.i18n = i18n

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.main_layout = QVBoxLayout(self.scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)
        title_text = self.i18n.get(title_key) if hasattr(self.i18n, "get") else title_key
        subtitle_text = self.i18n.get(subtitle_key) if hasattr(self.i18n, "get") else subtitle_key

        self.header = ViewHeader(
            title_text=title_text or "",
            subtitle_text=subtitle_text or ""
        )
        self.main_layout.addWidget(self.header)

        self.scroll_area.setWidget(self.scroll_content)
        base_layout.addWidget(self.scroll_area)
