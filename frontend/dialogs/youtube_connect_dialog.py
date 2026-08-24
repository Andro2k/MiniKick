# frontend\dialogs\youtube_connect_dialog.py

from PySide6.QtWidgets import QLabel, QLineEdit
from .base_dialog import ModernModal
from frontend.widgets import ModernButton
from frontend.common import get_assets_path
from frontend.common.theme import COLOR_RED

class YouTubeConnectDialog(ModernModal):
    def __init__(self, i18n, initial_target: str = "", parent=None):
        self.i18n = i18n
        super().__init__(
            title=self.i18n.get("dialogs.youtube_connect.title"),
            icon_path=get_assets_path("icons/brand-youtube.svg"),
            icon_bg_color=COLOR_RED,
            width=460,
            parent=parent
        )
        self._setup_ui(initial_target)

    def _setup_ui(self, initial_target: str):
        lbl_desc = QLabel(self.i18n.get("dialogs.youtube_connect.desc"))
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        self.content_layout.addWidget(lbl_desc)

        self.txt_target = QLineEdit()
        self.txt_target.setPlaceholderText(self.i18n.get("dialogs.youtube_connect.placeholder"))
        if initial_target:
            self.txt_target.setText(initial_target)
        self.txt_target.textChanged.connect(self._validate_input)
        self.content_layout.addWidget(self.txt_target)

        self.btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_connect = ModernButton(self.i18n.get("dialogs.youtube_connect.btn_connect"), role="action_youtube")
        self.btn_connect.clicked.connect(self.accept)
        self.btn_connect.setEnabled(bool(self.txt_target.text().strip()))

        self.add_action_buttons(self.btn_cancel, self.btn_connect)

    def _validate_input(self, text: str):
        self.btn_connect.setEnabled(bool(text.strip()))

    def get_target(self) -> str:
        return self.txt_target.text().strip()
