# frontend\widgets\search_bar.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal, QSize
from frontend.common.utils import get_icon_colored
from frontend.common.theme import COLOR_NEUTRAL_200

class UnifiedSearchBar(QFrame):
    textChanged = Signal(str)
    returnPressed = Signal()
    searchClicked = Signal(str)

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("role", "search_bar")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._icon_search = get_icon_colored("search.svg", COLOR_NEUTRAL_200, 16)
        self._icon_clear = get_icon_colored("x.svg", COLOR_NEUTRAL_200, 16)

        self.txt_input = QLineEdit(self)
        self.txt_input.setPlaceholderText(placeholder)
        self.txt_input.setFrame(False)
        self.txt_input.textChanged.connect(self._on_text_changed)
        self.txt_input.returnPressed.connect(self.returnPressed.emit)

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
