# frontend\dialogs\already_running_dialog.py

from PySide6.QtWidgets import QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from .base_dialog import ModernModal
from frontend.common import get_assets_path, COLOR_GREEN

class AlreadyRunningDialog(ModernModal):
    def __init__(self, i18n, parent=None):
        self.i18n = i18n
        title_str = self.i18n.get("dialogs.already_running.title")
        icon_path = get_assets_path("icons/alert-circle.svg")
        super().__init__(
            title=title_str,
            icon_path=icon_path,
            icon_bg_color=COLOR_GREEN,
            width=440,
            parent=parent
        )
        self.set_dialog_state("accent", QColor(46, 205, 112, 60))
        self.content_layout.setContentsMargins(24, 20, 24, 20)
        self.content_layout.setSpacing(14)

        desc_str = self.i18n.get("dialogs.already_running.desc")
        self.lbl_desc = QLabel(desc_str)
        self.lbl_desc.setProperty("role", "body")
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.lbl_desc)

        exit_str = self.i18n.get("common.buttons.exit")
        btn_close = QPushButton(exit_str)
        btn_close.setProperty("role", "action_outlined")
        btn_close.setFixedHeight(36)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.reject)

        ok_str = self.i18n.get("common.buttons.understood")
        btn_ok = QPushButton(ok_str)
        btn_ok.setProperty("role", "action_accent")
        btn_ok.setFixedHeight(36)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)

        self.add_action_buttons(btn_close, btn_ok)
