# frontend\dialogs\platform_connect_dialog.py

from PySide6.QtWidgets import QLabel
from .base_dialog import ModernModal
from frontend.widgets import ModernButton, ClearableLineEdit

class PlatformConnectDialog(ModernModal):
    def __init__(
        self,
        i18n,
        title_key: str,
        desc_key: str,
        placeholder_key: str,
        btn_connect_key: str,
        icon_path: str = "",
        icon_bg_color: str = "",
        btn_role: str = "",
        initial_target: str = "",
        width: int = 480,
        parent=None
    ):
        self.i18n = i18n
        self._is_cleared = False
        super().__init__(
            title=self.i18n.get(title_key),
            icon_path=icon_path,
            icon_bg_color=icon_bg_color,
            width=width,
            parent=parent
        )
        self._setup_ui(desc_key, placeholder_key, btn_connect_key, btn_role, initial_target)

    def _setup_ui(self, desc_key: str, placeholder_key: str, btn_connect_key: str, btn_role: str, initial_target: str):
        lbl_desc = QLabel(self.i18n.get(desc_key))
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        self.content_layout.addWidget(lbl_desc)

        self.txt_target = ClearableLineEdit(placeholder=self.i18n.get(placeholder_key), parent=self)
        if initial_target:
            self.txt_target.setText(initial_target)
        self.txt_target.textChanged.connect(self._validate_input)
        self.txt_target.returnPressed.connect(self._on_return_pressed)
        self.txt_target.textCleared.connect(self._on_text_cleared)

        self.content_layout.addWidget(self.txt_target)

        self.btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_connect = ModernButton(self.i18n.get(btn_connect_key), role=btn_role)
        self.btn_connect.clicked.connect(self.accept)
        self.btn_connect.setEnabled(bool(self.txt_target.text().strip()))

        self.add_action_buttons(self.btn_cancel, self.btn_connect)

    def _on_text_cleared(self):
        self._is_cleared = True
        self._validate_input("")

    def _on_return_pressed(self):
        if self.btn_connect.isEnabled():
            self.accept()

    def _validate_input(self, text: str):
        has_text = bool(text.strip())
        self.btn_connect.setEnabled(has_text)
        if has_text:
            self._is_cleared = False

    def is_cleared(self) -> bool:
        return self._is_cleared or not bool(self.txt_target.text().strip())

    def get_target(self) -> str:
        return self.txt_target.text().strip()

