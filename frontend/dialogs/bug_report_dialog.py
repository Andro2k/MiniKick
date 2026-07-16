# frontend\dialogs\bug_report_dialog.py

from PySide6.QtWidgets import (
    QLabel, QLineEdit, QTextEdit, QCheckBox, QPushButton, QHBoxLayout, QFileDialog
)
from PySide6.QtCore import Qt

from .base_dialog import ModernModal
from frontend.common.utils import get_assets_path, get_icon_colored
from frontend.common.theme import COLOR_RED
from backend.workers import BugReportWorker

class BugReportDialog(ModernModal):
    def __init__(self, i18n, parent=None):
        title = i18n.get("settings.feedback.title")
        icon_path = get_assets_path("icons/bug.svg")
        
        super().__init__(
            title=title, 
            icon_path=icon_path, 
            icon_bg_color="", 
            width=500, 
            parent=parent
        )
        self.i18n = i18n
        self.worker = None

        self._setup_form()

    def _setup_form(self):
        lbl_username = QLabel(self.i18n.get("dialogs.bug_report.lbl_contact"))
        lbl_username.setProperty("role", "body")
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_contact"))
        self.txt_username.setFixedHeight(32)

        lbl_desc = QLabel(self.i18n.get("dialogs.bug_report.lbl_description"))
        lbl_desc.setProperty("role", "body")
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_desc"))
        self.txt_desc.setFixedHeight(120)

        lbl_image = QLabel(self.i18n.get("dialogs.bug_report.lbl_image"))
        lbl_image.setProperty("role", "body")

        image_layout = QHBoxLayout()
        self.txt_image_path = QLineEdit()
        self.txt_image_path.setReadOnly(True)
        self.txt_image_path.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_image"))
        self.txt_image_path.setFixedHeight(32)

        self.btn_browse_image = QPushButton(self.i18n.get("common.buttons.browse"))
        self.btn_browse_image.setProperty("role", "action_outlined")
        self.btn_browse_image.setFixedHeight(32)
        self.btn_browse_image.clicked.connect(self._browse_image)

        self.btn_clear_image = QPushButton()
        self.btn_clear_image.setIcon(get_icon_colored("x.svg", COLOR_RED, size=16))
        self.btn_clear_image.setProperty("role", "action_danger_border")
        self.btn_clear_image.setFixedHeight(32)
        self.btn_clear_image.setFixedWidth(32)
        self.btn_clear_image.clicked.connect(self._clear_image)

        image_layout.addWidget(self.txt_image_path, stretch=1)
        image_layout.addWidget(self.btn_browse_image)
        image_layout.addWidget(self.btn_clear_image)

        self.chk_logs = QCheckBox(self.i18n.get("dialogs.bug_report.chk_include_logs"))
        self.chk_logs.setChecked(True)
        self.chk_logs.setProperty("role", "checkbox")
        
        self.lbl_error = QLabel()
        self.lbl_error.setProperty("state", "error")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        self.content_layout.addWidget(lbl_username)
        self.content_layout.addWidget(self.txt_username)
        self.content_layout.addWidget(lbl_desc)
        self.content_layout.addWidget(self.txt_desc)
        self.content_layout.addWidget(lbl_image)
        self.content_layout.addLayout(image_layout)
        self.content_layout.addWidget(self.chk_logs)
        self.content_layout.addWidget(self.lbl_error)

        self.btn_cancel = QPushButton(self.i18n.get("common.buttons.cancel"))
        self.btn_cancel.setProperty("role", "action_outlined")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_send = QPushButton(self.i18n.get("dialogs.bug_report.btn_send"))
        self.btn_send.setProperty("role", "action_accent")
        self.btn_send.setFixedHeight(36)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self._on_send_clicked)

        self.add_action_buttons(self.btn_cancel, self.btn_send)

    def _browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.get("common.buttons.browse"),
            "",
            "Image files (*.png *.jpg *.jpeg *.webp *.gif *.bmp)"
        )
        if file_path:
            self.txt_image_path.setText(file_path)

    def _clear_image(self):
        self.txt_image_path.clear()

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
            image_path=self.txt_image_path.text(),
            i18n=self.i18n
        )
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _set_loading(self, loading: bool):
        self.btn_send.setEnabled(not loading)
        self.btn_cancel.setEnabled(not loading)
        self.txt_username.setEnabled(not loading)
        self.txt_desc.setEnabled(not loading)
        self.chk_logs.setEnabled(not loading)
        self.btn_browse_image.setEnabled(not loading)
        self.btn_clear_image.setEnabled(not loading)
        
        if loading:
            self.btn_send.setText(self.i18n.get("dialogs.bug_report.btn_sending"))
        else:
            self.btn_send.setText(self.i18n.get("dialogs.bug_report.btn_send"))

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
