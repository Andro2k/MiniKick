# frontend\widgets\clearable_line_edit.py

from PySide6.QtWidgets import QPushButton
from .action_line_edit import ActionLineEdit

class ClearableLineEdit(ActionLineEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(placeholder, search_when_empty=False, parent=parent)

    @property
    def btn_clear(self) -> QPushButton:
        return self.btn_action

    def setMinimumWidth(self, width: int) -> None:
        super().setMinimumWidth(width)
        self.txt_input.setMinimumWidth(width)
