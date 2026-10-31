# frontend\widgets\action_line_edit.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLineEdit, QPushButton
from frontend.common import get_icon_colored, Size
from .controls_widget import configure_icon_only_button
from .layout_helpers import create_row_layout
from .style_utils import sync_focus_state

class ActionLineEdit(QFrame):
    textChanged = Signal(str)
    returnPressed = Signal()
    textCleared = Signal()
    searchClicked = Signal(str)

    def __init__(self, placeholder: str = "", search_when_empty: bool = False, parent=None):
        super().__init__(parent)
        self.setProperty("role", "search_bar")
        self._search_when_empty = search_when_empty
        self._icon_search = get_icon_colored("search-filled.svg")
        self._icon_delete = get_icon_colored("x-filled.svg")

        self.txt_input = QLineEdit(self)
        self.txt_input.setFrame(False)
        self.txt_input.setPlaceholderText(placeholder)
        self.txt_input.textChanged.connect(self._on_text_changed)
        self.txt_input.returnPressed.connect(self.returnPressed.emit)
        self.txt_input.installEventFilter(self)

        self.btn_action = QPushButton(self)
        configure_icon_only_button(self.btn_action)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self._on_action_clicked)

        layout = create_row_layout(spacing=Size.SPACING_NN, parent=self)
        layout.addWidget(self.txt_input, stretch=1)
        layout.addWidget(self.btn_action)
        self._sync_action_button()

    def _has_text(self) -> bool:
        return bool(self.txt_input.text().strip())

    def _sync_action_button(self) -> None:
        shows_search = self._search_when_empty and not self._has_text()
        self.btn_action.setIcon(self._icon_search if shows_search else self._icon_delete)
        usable = (self._has_text() or self._search_when_empty) and not self.txt_input.isReadOnly()
        self.btn_action.setVisible(usable)
        self.btn_action.setEnabled(usable)

    def _on_text_changed(self, text: str) -> None:
        self._sync_action_button()
        self.textChanged.emit(text)

    def _on_action_clicked(self) -> None:
        if self._has_text():
            self.clear()
            self.txt_input.setFocus()
            self.textCleared.emit()
        else:
            self.searchClicked.emit(self.txt_input.text())

    def text(self) -> str:
        return self.txt_input.text()

    def setText(self, text: str) -> None:
        self.txt_input.setText(text)
        self._sync_action_button()

    def clear(self) -> None:
        self.txt_input.clear()
        self._sync_action_button()

    def placeholderText(self) -> str:
        return self.txt_input.placeholderText()

    def setPlaceholderText(self, text: str) -> None:
        self.txt_input.setPlaceholderText(text)

    def setReadOnly(self, read_only: bool) -> None:
        self.txt_input.setReadOnly(read_only)
        self._sync_action_button()

    def isReadOnly(self) -> bool:
        return self.txt_input.isReadOnly()

    def setToolTip(self, text: str) -> None:
        super().setToolTip(text)
        self.txt_input.setToolTip(text)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.txt_input.setEnabled(enabled)
        self._sync_action_button()

    def setFocus(self) -> None:
        self.txt_input.setFocus()

    def eventFilter(self, watched, event):
        if watched is self.txt_input:
            sync_focus_state(self, event.type())
        return super().eventFilter(watched, event)
