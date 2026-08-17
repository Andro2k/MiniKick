# frontend\dialogs\bug_report_dialog.py

import os
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QTextEdit, QCheckBox, QPushButton,
    QHBoxLayout, QVBoxLayout, QFileDialog, QFrame, QWidget
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from .base_dialog import ModernModal
from frontend.common.utils import get_assets_path, get_icon_colored
from frontend.common.theme import COLOR_RED, COLOR_GREEN
from backend.workers import BugReportWorker

class SeverityCard(QFrame):
    clicked = Signal(str)

    def __init__(self, key: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setProperty("role", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(title)
        self.lbl_title.setProperty("role", "body")
        self.lbl_title.setProperty("state", "bold")

        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setProperty("role", "caption")
        self.lbl_sub.setWordWrap(True)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_sub)
        layout.addLayout(text_layout, 1)

    def set_selected(self, selected: bool):
        if selected:
            self.lbl_title.setProperty("state", "success")
        else:
            self.lbl_title.setProperty("state", "bold")
        self.lbl_title.style().unpolish(self.lbl_title)
        self.lbl_title.style().polish(self.lbl_title)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)

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
        self.setFixedHeight(180)
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_container = QWidget()
        empty_layout = QVBoxLayout(self.empty_container)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setSpacing(4)
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
        preview_layout.setContentsMargins(4, 4, 4, 4)
        preview_layout.setSpacing(8)

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
                scaled = pixmap.scaled(QSize(160, 160), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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

class BugReportDialog(ModernModal):
    def __init__(self, i18n, parent=None):
        title = i18n.get("settings.feedback.title")
        icon_path = get_assets_path("icons/bug.svg")
        super().__init__(title=title, icon_path=icon_path, icon_bg_color="", width=720, parent=parent)
        self.i18n = i18n
        self.worker = None
        self.selected_severity = "Low"
        self.severity_cards = {}
        self._setup_form()

    def _setup_form(self):
        lbl_sev_header = QLabel(self.i18n.get("dialogs.bug_report.severity_title"))
        lbl_sev_header.setProperty("role", "body")
        lbl_sev_header.setProperty("state", "bold")

        sev_layout = QHBoxLayout()
        sev_layout.setSpacing(10)

        card_configs = [
            ("Low", self.i18n.get("dialogs.bug_report.severity_low"), self.i18n.get("dialogs.bug_report.severity_low_desc")),
            ("Medium", self.i18n.get("dialogs.bug_report.severity_medium"), self.i18n.get("dialogs.bug_report.severity_medium_desc")),
            ("Urgent", self.i18n.get("dialogs.bug_report.severity_urgent"), self.i18n.get("dialogs.bug_report.severity_urgent_desc")),
        ]

        for key, title, sub in card_configs:
            card = SeverityCard(key, title, sub)
            card.clicked.connect(self._on_severity_selected)
            self.severity_cards[key] = card
            sev_layout.addWidget(card, 1)

        self.severity_cards["Low"].set_selected(True)

        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(16)

        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        lbl_username = QLabel(self.i18n.get("dialogs.bug_report.lbl_contact"))
        lbl_username.setProperty("role", "body")
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_contact"))
        self.txt_username.setFixedHeight(34)

        lbl_desc = QLabel(self.i18n.get("dialogs.bug_report.lbl_description"))
        lbl_desc.setProperty("role", "body")
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_desc"))
        self.txt_desc.setFixedHeight(150)

        left_col.addWidget(lbl_username)
        left_col.addWidget(self.txt_username)
        left_col.addWidget(lbl_desc)
        left_col.addWidget(self.txt_desc)

        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        lbl_image = QLabel(self.i18n.get("dialogs.bug_report.lbl_image"))
        lbl_image.setProperty("role", "body")

        self.dropzone = ImageDropzone(self.i18n)

        self.chk_logs = QCheckBox(self.i18n.get("dialogs.bug_report.chk_include_logs"))
        self.chk_logs.setChecked(True)

        right_col.addWidget(lbl_image)
        right_col.addWidget(self.dropzone)
        right_col.addWidget(self.chk_logs)
        right_col.addStretch()

        cols_layout.addLayout(left_col, 3)
        cols_layout.addLayout(right_col, 2)

        self.lbl_error = QLabel()
        self.lbl_error.setProperty("state", "error")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        self.content_layout.addWidget(lbl_sev_header)
        self.content_layout.addLayout(sev_layout)
        self.content_layout.addSpacing(6)
        self.content_layout.addLayout(cols_layout)
        self.content_layout.addWidget(self.lbl_error)

        self.btn_cancel = QPushButton(self.i18n.get("common.buttons.cancel"))
        self.btn_cancel.setProperty("role", "action_outlined")
        self.btn_cancel.setFixedHeight(38)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_send = QPushButton(self.i18n.get("dialogs.bug_report.btn_send_low"))
        self.btn_send.setProperty("role", "action_accent")
        self.btn_send.setFixedHeight(38)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self._on_send_clicked)

        self.add_action_buttons(self.btn_cancel, self.btn_send)

    def _on_severity_selected(self, key: str):
        self.selected_severity = key
        for k, card in self.severity_cards.items():
            card.set_selected(k == key)

        btn_key_map = {
            "Low": "dialogs.bug_report.btn_send_low",
            "Medium": "dialogs.bug_report.btn_send_medium",
            "Urgent": "dialogs.bug_report.btn_send_urgent",
        }
        self.btn_send.setText(self.i18n.get(btn_key_map.get(key, "dialogs.bug_report.btn_send")))

    def _on_send_clicked(self):
        desc = self.txt_desc.toPlainText().strip()
        if not desc:
            self.lbl_error.setText(self.i18n.get("dialogs.bug_report.err_empty_desc"))
            self.lbl_error.show()
            return

        self.lbl_error.hide()
        self._set_loading(True)

        self.worker = BugReportWorker(
            username=self.txt_username.text(),
            description=desc,
            include_logs=self.chk_logs.isChecked(),
            image_path=self.dropzone.image_path,
            i18n=self.i18n,
            severity=self.selected_severity
        )
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _set_loading(self, loading: bool):
        self.btn_send.setEnabled(not loading)
        self.btn_cancel.setEnabled(not loading)
        self.txt_username.setEnabled(not loading)
        self.txt_desc.setEnabled(not loading)
        self.chk_logs.setEnabled(not loading)
        self.dropzone.setEnabled(not loading)
        for card in self.severity_cards.values():
            card.setEnabled(not loading)

        if loading:
            self.btn_send.setText(self.i18n.get("dialogs.bug_report.btn_sending"))
        else:
            self._on_severity_selected(self.selected_severity)

    def _on_worker_finished(self, success: bool, message: str):
        self._set_loading(False)
        if success:
            if hasattr(self.parent(), 'toast'):
                self.parent().toast.show_toast(
                    self.i18n.get("dialogs.bug_report.success_title"),
                    self.i18n.get("dialogs.bug_report.success_msg"),
                    "success"
                )
            self.accept()
        else:
            self.lbl_error.setText(message)
            self.lbl_error.show()
