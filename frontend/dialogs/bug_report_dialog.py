# frontend\dialogs\bug_report_dialog.py

import logging
import os
from PySide6.QtWidgets import (
    QLabel, QLineEdit, 
    QTextEdit, QCheckBox, QPushButton,
    QHBoxLayout, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal

from frontend.dialogs.base_dialog import ModernModal
from frontend.common.utils import get_assets_path, get_icon_colored
from frontend.common.theme import COLOR_RED
from backend.config.api_keys import DISCORD_WEBHOOK_URL
from backend.config.version import APP_VERSION
import requests

class BugReportWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, username: str, description: str, include_logs: bool, image_path: str, i18n):
        super().__init__()
        self.username = username
        self.description = description
        self.include_logs = include_logs
        self.image_path = image_path
        self.i18n = i18n

    def run(self):
        if not DISCORD_WEBHOOK_URL:
            self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_no_webhook"))
            return

        try:
            user_text = self.username.strip() or "Anónimo"
            content = (
                f"**REPORTE DE BUG**\n"
                f"**Usuario/Discord:** {user_text}\n"
                f"**Versión de MiniKick:** {APP_VERSION}\n"
                f"**Descripción:**\n{self.description}\n"
                f"----------------------------------------"
            )
            data = {
                "content": content
            }
            
            files = {}
            if self.include_logs:
                app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
                log_file_path = os.path.join(app_data_dir, '.Minikick', 'logs', 'minikick.log')
                if os.path.exists(log_file_path):
                    try:
                        with open(log_file_path, "rb") as f:
                            files["file"] = ("minikick.log", f.read(), "text/plain")
                    except Exception as e:
                        logging.error("[BugReportWorker] Error reading log file: %s", e)

            if self.image_path and os.path.exists(self.image_path):
                try:
                    filename = os.path.basename(self.image_path)
                    mime_type = "image/png"
                    if filename.lower().endswith((".jpg", ".jpeg")):
                        mime_type = "image/jpeg"
                    elif filename.lower().endswith(".gif"):
                        mime_type = "image/gif"
                    elif filename.lower().endswith(".webp"):
                        mime_type = "image/webp"

                    with open(self.image_path, "rb") as f:
                        files["image"] = (filename, f.read(), mime_type)
                except Exception as e:
                    logging.error("[BugReportWorker] Error reading image file: %s", e)

            if files:
                resp = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=15)
            else:
                resp = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=15)

            if resp.status_code in (200, 204):
                self.finished.emit(True, self.i18n.get("dialogs.bug_report.success_send"))
            else:
                self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_discord").replace("{code}", str(resp.status_code)))
        except Exception as e:
            self.finished.emit(False, self.i18n.get("dialogs.bug_report.err_send").replace("{error}", str(e)))


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
