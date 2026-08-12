# frontend\dialogs\already_running_dialog.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import os
from frontend.common.utils import get_icon, get_assets_path
from frontend.widgets import ScalableIllustration

class AlreadyRunningDialog(QDialog):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 400)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 10)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.card = QFrame()
        self.card.setProperty("role", "dialog") 
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        illustration_path = get_assets_path(os.path.join("icons", "illustration-thumbs-up.svg"))
        self.lbl_illustration = ScalableIllustration(
            icon_path=illustration_path,
            aspect_ratio=1.0,
            min_size=160,
            max_size=320,
            size_offset=180,
            parent=self
        )
        card_layout.addWidget(self.lbl_illustration, alignment=Qt.AlignmentFlag.AlignCenter)

        card_layout.addSpacing(4)
        title_str = self.i18n.get("dialogs.already_running.title")
        lbl_title = QLabel(title_str)
        lbl_title.setProperty("role", "h1")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_title)

        desc_str = self.i18n.get("dialogs.already_running.desc")
        lbl_desc = QLabel(desc_str)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_desc)

        card_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

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

        btn_layout.addWidget(btn_close, stretch=1)
        btn_layout.addWidget(btn_ok, stretch=1)

        card_layout.addLayout(btn_layout)
        main_layout.addWidget(self.card)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "lbl_illustration"):
            self.lbl_illustration.update_image(self.card.height())

