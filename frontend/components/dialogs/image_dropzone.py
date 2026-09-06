# frontend\components\dialogs\image_dropzone.py

import os
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from frontend.common import (
    get_icon_colored, COLOR_RED, COLOR_GREEN,
    MARGIN_MD, MARGIN_NONE, MARGIN_XS, SPACING_XS
)

class ImageDropzone(QFrame):
    image_selected = Signal(str)
    image_cleared = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.image_path = ""
        self.setProperty("role", "card")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(140)
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(*MARGIN_MD)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_container = QWidget()
        empty_layout = QVBoxLayout(self.empty_container)
        empty_layout.setContentsMargins(*MARGIN_NONE)
        empty_layout.setSpacing(SPACING_XS)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(get_icon_colored("file-text.svg", COLOR_GREEN, size=24).pixmap(QSize(24, 24)))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_lbl = QLabel(self.i18n.get("dialogs.bug_report.dropzone_title"))
        self.title_lbl.setProperty("role", "body")
        self.title_lbl.setProperty("state", "bold")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.sub_lbl = QLabel(self.i18n.get("dialogs.bug_report.dropzone_desc"))
        self.sub_lbl.setProperty("role", "caption")
        self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_lbl.setWordWrap(True)

        empty_layout.addWidget(self.icon_lbl)
        empty_layout.addWidget(self.title_lbl)
        empty_layout.addWidget(self.sub_lbl)

        self.preview_container = QWidget()
        preview_layout = QHBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(*MARGIN_XS)
        preview_layout.setSpacing(SPACING_XS)

        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_remove = QPushButton()
        self.btn_remove.setIcon(get_icon_colored("x.svg", COLOR_RED, size=16))
        self.btn_remove.setIconSize(QSize(16, 16))
        self.btn_remove.setFixedSize(28, 28)
        self.btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove.setProperty("role", "action_danger_border")
        self.btn_remove.setToolTip(self.i18n.get("dialogs.bug_report.remove_image_tooltip"))
        self.btn_remove.clicked.connect(self.clear_image)

        preview_layout.addWidget(self.img_lbl, 1)
        preview_layout.addWidget(self.btn_remove, 0, Qt.AlignmentFlag.AlignTop)

        self.layout.addWidget(self.empty_container)
        self.layout.addWidget(self.preview_container)

        self._update_state()

    def _update_state(self):
        if self.image_path and os.path.exists(self.image_path):
            self.empty_container.hide()
            self.preview_container.show()

            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(QSize(120, 120), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.img_lbl.setPixmap(scaled)
        else:
            self.empty_container.show()
            self.preview_container.hide()

    def set_image(self, path: str):
        self.image_path = path
        self._update_state()
        if path:
            self.image_selected.emit(path)

    def clear_image(self):
        self.image_path = ""
        self._update_state()
        self.image_cleared.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.image_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.i18n.get("common.buttons.browse"),
                "",
                "Image files (*.png *.jpg *.jpeg *.webp *.gif *.bmp)"
            )
            if file_path:
                self.set_image(file_path)
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and os.path.exists(file_path):
                self.set_image(file_path)
