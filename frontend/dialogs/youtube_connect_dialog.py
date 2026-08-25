# frontend\dialogs\youtube_connect_dialog.py

from PySide6.QtWidgets import QLabel, QLineEdit, QHBoxLayout, QWidget
from .base_dialog import ModernModal
from frontend.widgets import ModernButton
from frontend.common import get_assets_path
from frontend.common.theme import COLOR_RED

class YouTubeConnectDialog(ModernModal):
    def __init__(self, i18n, initial_target: str = "", parent=None):
        self.i18n = i18n
        self._is_cleared = False
        super().__init__(
            title=self.i18n.get("dialogs.youtube_connect.title"),
            icon_path=get_assets_path("icons/brand-youtube.svg"),
            icon_bg_color=COLOR_RED,
            width=480,
            parent=parent
        )
        self._setup_ui(initial_target)

    def _setup_ui(self, initial_target: str):
        lbl_desc = QLabel(self.i18n.get("dialogs.youtube_connect.desc"))
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        self.content_layout.addWidget(lbl_desc)

        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.txt_target = QLineEdit()
        self.txt_target.setClearButtonEnabled(True)
        self.txt_target.setPlaceholderText(self.i18n.get("dialogs.youtube_connect.placeholder"))
        if initial_target:
            self.txt_target.setText(initial_target)
        self.txt_target.textChanged.connect(self._validate_input)

        self.btn_clear = ModernButton(self.i18n.get("dialogs.youtube_connect.btn_clear"), role="action_danger_border")
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.btn_clear.setVisible(bool(initial_target))

        input_layout.addWidget(self.txt_target)
        input_layout.addWidget(self.btn_clear)
        self.content_layout.addWidget(input_container)

        self.btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_connect = ModernButton(self.i18n.get("dialogs.youtube_connect.btn_connect"), role="action_youtube")
        self.btn_connect.clicked.connect(self.accept)
        self.btn_connect.setEnabled(bool(self.txt_target.text().strip()))

        self.add_action_buttons(self.btn_cancel, self.btn_connect)

    def _on_clear_clicked(self):
        self._is_cleared = True
        self.txt_target.clear()
        self.btn_clear.setVisible(False)
        self.btn_connect.setEnabled(False)

    def _validate_input(self, text: str):
        has_text = bool(text.strip())
        self.btn_connect.setEnabled(has_text)
        self.btn_clear.setVisible(has_text)
        if has_text:
            self._is_cleared = False

    def is_cleared(self) -> bool:
        return self._is_cleared or not bool(self.txt_target.text().strip())

    def get_target(self) -> str:
        return self.txt_target.text().strip()

