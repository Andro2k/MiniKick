# frontend\widgets\clearable_line_edit.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal, QSize
from frontend.common import get_icon_colored, MARGIN_NONE, SPACING_NONE

class ClearableLineEdit(QFrame):
    textChanged = Signal(str)
    returnPressed = Signal()
    textCleared = Signal()

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("role", "search_bar")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*MARGIN_NONE)
        layout.setSpacing(SPACING_NONE)

        self._icon_clear = get_icon_colored("x.svg")

        self.txt_input = QLineEdit(self)
        self.txt_input.setPlaceholderText(placeholder)
        self.txt_input.setFrame(False)
        self.txt_input.textChanged.connect(self._on_text_changed)
        self.txt_input.returnPressed.connect(self.returnPressed.emit)

        self.btn_clear = QPushButton(self)
        self.btn_clear.setIcon(self._icon_clear)
        self.btn_clear.setIconSize(QSize(16, 16))
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.btn_clear.setVisible(False)
        self.btn_clear.setEnabled(False)

        layout.addWidget(self.txt_input, stretch=1)
        layout.addWidget(self.btn_clear)

    def _on_text_changed(self, text: str):
        has_text = bool(text.strip())
        self.btn_clear.setVisible(has_text)
        self.btn_clear.setEnabled(has_text)
        self.textChanged.emit(text)

    def _on_clear_clicked(self):
        self.txt_input.clear()
        self.btn_clear.setVisible(False)
        self.btn_clear.setEnabled(False)
        self.txt_input.setFocus()
        self.textCleared.emit()

    def text(self) -> str:
        return self.txt_input.text()

    def setText(self, text: str):
        self.txt_input.setText(text)
        has_text = bool(text.strip())
        self.btn_clear.setVisible(has_text)
        self.btn_clear.setEnabled(has_text)

    def clear(self):
        self.txt_input.clear()
        self.btn_clear.setVisible(False)
        self.btn_clear.setEnabled(False)

    def setPlaceholderText(self, text: str):
        self.txt_input.setPlaceholderText(text)

    def placeholderText(self) -> str:
        return self.txt_input.placeholderText()

    def setFocus(self):
        self.txt_input.setFocus()

    def setToolTip(self, text: str):
        super().setToolTip(text)
        self.txt_input.setToolTip(text)

    def toolTip(self) -> str:
        return self.txt_input.toolTip()

    def setMinimumWidth(self, width: int):
        super().setMinimumWidth(width)
        self.txt_input.setMinimumWidth(width)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.txt_input.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled and bool(self.txt_input.text().strip()))

    def setReadOnly(self, ro: bool):
        self.txt_input.setReadOnly(ro)
        has_text = not ro and bool(self.txt_input.text().strip())
        self.btn_clear.setVisible(has_text)
        self.btn_clear.setEnabled(has_text)

    def isReadOnly(self) -> bool:
        return self.txt_input.isReadOnly()
