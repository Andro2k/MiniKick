# frontend\widgets\search_bar.py

from PySide6.QtWidgets import QFrame, QPushButton
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from frontend.common import get_icon_colored, MARGIN_NONE, SPACING_NONE
from .layout_helpers import create_row_layout, create_frameless_input

class UnifiedSearchBar(QFrame):
    textChanged = Signal(str)
    returnPressed = Signal()
    searchClicked = Signal(str)

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("role", "search_bar")
        
        layout = create_row_layout(spacing=SPACING_NONE, margins=MARGIN_NONE, parent=self)

        self._icon_search = get_icon_colored("search-filled.svg")
        self._icon_clear = get_icon_colored("x-filled.svg")

        self.txt_input = create_frameless_input(
            self,
            placeholder=placeholder,
            on_text_changed=self._on_text_changed,
            on_return_pressed=self.returnPressed.emit,
            event_filter_parent=self
        )

        self.btn_search = QPushButton(self)
        self.btn_search.setIcon(self._icon_search)
        self.btn_search.setIconSize(QSize(16, 16))
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self._on_btn_clicked)

        layout.addWidget(self.txt_input, stretch=1)
        layout.addWidget(self.btn_search)

    def _on_text_changed(self, text: str):
        if text.strip():
            self.btn_search.setIcon(self._icon_clear)
        else:
            self.btn_search.setIcon(self._icon_search)
        self.textChanged.emit(text)

    def _on_btn_clicked(self):
        if self.txt_input.text().strip():
            self.txt_input.clear()
            self.txt_input.setFocus()
        else:
            self.searchClicked.emit(self.txt_input.text())

    def text(self) -> str:
        return self.txt_input.text()

    def setText(self, text: str):
        self.txt_input.setText(text)

    def setPlaceholderText(self, text: str):
        self.txt_input.setPlaceholderText(text)

    def clear(self):
        self.txt_input.clear()

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.txt_input.setEnabled(enabled)
        self.btn_search.setEnabled(enabled)

    def setFocus(self):
        self.txt_input.setFocus()

    def eventFilter(self, watched, event):
        if watched == self.txt_input:
            if event.type() == QEvent.Type.FocusIn:
                self.setProperty("state", "focused")
                self.style().unpolish(self)
                self.style().polish(self)
            elif event.type() == QEvent.Type.FocusOut:
                self.setProperty("state", "")
                self.style().unpolish(self)
                self.style().polish(self)
        return super().eventFilter(watched, event)
