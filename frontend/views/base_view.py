# frontend\views\base_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Qt
from frontend.common import Size
from frontend.widgets.block_widget import ViewHeader, FadingScrollArea

_COLUMN_STRETCH = 100

class BaseView(QWidget):
    def __init__(self, i18n, title_key: str, subtitle_key: str, parent=None, max_content_width: int | None = None, min_content_width: int | None = None):
        super().__init__(parent)
        self.i18n = i18n

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(*Size.Margin.MRG_NON)

        self.scroll_area = FadingScrollArea(parent=self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.content_column = self._build_content_column(max_content_width, min_content_width)
        self.main_layout = QVBoxLayout(self.content_column)
        self.main_layout.setContentsMargins(*Size.Margin.MRG_XLG)
        self.main_layout.setSpacing(Size.SPACING_LG)
        title_text = self.i18n.get(title_key) if hasattr(self.i18n, "get") else title_key
        subtitle_text = self.i18n.get(subtitle_key) if hasattr(self.i18n, "get") else subtitle_key

        self.header = ViewHeader(
            title_text=title_text or "",
            subtitle_text=subtitle_text or ""
        )
        self.main_layout.addWidget(self.header)

        self.scroll_area.setWidget(self.scroll_content)
        base_layout.addWidget(self.scroll_area)

    def _build_content_column(self, max_width: int | None, min_width: int | None) -> QWidget:
        if not max_width:
            return self.scroll_content

        column = QWidget(self.scroll_content)
        column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        column.setMaximumWidth(max_width)
        if min_width:
            column.setMinimumWidth(min_width)

        row = QHBoxLayout(self.scroll_content)
        row.setContentsMargins(*Size.Margin.MRG_NON)
        row.setSpacing(Size.SPACING_NN)
        row.addStretch(1)
        row.addWidget(column, _COLUMN_STRETCH)
        row.addStretch(1)
        return column
