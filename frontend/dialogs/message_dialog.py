# frontend\dialogs\message_editor_dialog.py

from PySide6.QtGui import QColor
from .base_dialog import ModernModal
from frontend.widgets import ModernButton, VariableTextEdit
from frontend.common import get_assets_path, COLOR_GREEN

class MessageEditorDialog(ModernModal):
    def __init__(self, current_text: str, i18n, parent=None):
        super().__init__(
            title=i18n.get("timer.dialog.editor_title"),
            icon_path=get_assets_path("icons/clock-circle-duotone.svg"),
            icon_bg_color=COLOR_GREEN,
            width=500,
            parent=parent
        )
        self.i18n = i18n
        self.set_dialog_state("accent", QColor(46, 205, 112, 60))

        self.text_edit = VariableTextEdit()
        self.text_edit.setPlaceholderText(self.i18n.get("timer.dialog.response_placeholder"))
        self.text_edit.setPlainText(current_text)
        self.text_edit.setMinimumHeight(150)
        self.text_edit.setAcceptRichText(False)
        self.content_layout.addWidget(self.text_edit)

        btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        btn_cancel.clicked.connect(self.reject)

        self.btn_save = ModernButton(self.i18n.get("common.buttons.save"), role="action_accent")
        self.btn_save.clicked.connect(self.accept)

        self.add_action_buttons(btn_cancel, self.btn_save)

        self.text_edit.textChanged.connect(self._validate_text_length)
        self._validate_text_length()

    def _validate_text_length(self):
        text = self.text_edit.toPlainText()
        is_invalid = len(text) > 492
        self.text_edit.setProperty("state", "error" if is_invalid else "normal")
        self.text_edit.style().unpolish(self.text_edit)
        self.text_edit.style().polish(self.text_edit)
        self.btn_save.setEnabled(not is_invalid)

    def get_text(self) -> str:
        return self.text_edit.toPlainText().replace("\n", " ").strip()
