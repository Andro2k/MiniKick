# frontend\dialogs\crash_report_dialog.py

from PySide6.QtWidgets import (
    QLabel, QLineEdit, QTextEdit, QApplication,
    QHBoxLayout, QVBoxLayout, QFrame
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor

from .base_dialog import ModernModal
from frontend.widgets import ModernButton
from frontend.common import get_assets_path, COLOR_RED

class CrashReportDialog(ModernModal):
    def __init__(self, traceback_text: str, i18n, webhook_url: str = "", worker_class=None, initial_contact: str = "", parent=None):
        self.traceback_text = traceback_text
        self.i18n = i18n
        self.webhook_url = webhook_url
        self.worker_class = worker_class
        self.worker = None

        self.initial_contact = initial_contact or ""

        self.title_text = self.i18n.get("crash.title")
        self.lbl_contact_text = self.i18n.get("crash.lbl_contact")
        self.placeholder_contact_text = self.i18n.get("crash.placeholder_contact")
        self.lbl_desc_text = self.i18n.get("crash.lbl_desc")
        self.placeholder_desc_text = self.i18n.get("crash.placeholder_desc")
        self.lbl_traceback_text = self.i18n.get("crash.lbl_traceback")
        self.btn_send_text = self.i18n.get("crash.btn_send")
        self.btn_copy_text = self.i18n.get("crash.btn_copy_traceback")
        self.copied_toast_text = self.i18n.get("crash.traceback_copied")
        self.err_send_text = self.i18n.get("crash.err_send")
        self.err_no_webhook_text = self.i18n.get("crash.err_no_webhook")
        self.subtitle_text = self.i18n.get("crash.subtitle")

        icon_path = get_assets_path("icons/bug.svg")
        super().__init__(title=self.title_text, icon_path=icon_path, icon_bg_color=COLOR_RED, width=580, parent=parent)
        self.set_dialog_state("danger", QColor(239, 68, 68, 80))
        self._setup_crash_form()

    def _setup_crash_form(self):
        header_card = QFrame()
        header_card.setProperty("role", "banner_danger")
        card_layout = QVBoxLayout(header_card)
        card_layout.setContentsMargins(12, 10, 12, 10)

        lbl_subtitle = QLabel(self.subtitle_text)
        lbl_subtitle.setProperty("role", "body")
        lbl_subtitle.setWordWrap(True)
        card_layout.addWidget(lbl_subtitle)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)

        lbl_contact = QLabel(self.lbl_contact_text)
        lbl_contact.setProperty("role", "body")
        self.txt_contact = QLineEdit()
        self.txt_contact.setPlaceholderText(self.placeholder_contact_text)
        if self.initial_contact:
            self.txt_contact.setText(self.initial_contact)

        lbl_desc = QLabel(self.lbl_desc_text)
        lbl_desc.setProperty("role", "body")
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.placeholder_desc_text)

        form_layout.addWidget(lbl_contact)
        form_layout.addWidget(self.txt_contact)
        form_layout.addWidget(lbl_desc)
        form_layout.addWidget(self.txt_desc)

        tb_header_layout = QHBoxLayout()
        lbl_traceback = QLabel(self.lbl_traceback_text)
        lbl_traceback.setProperty("role", "body")

        self.btn_copy_tb = ModernButton(self.btn_copy_text, role="action_outlined", icon_name="clipboard-text.svg", icon_color="#FFFFFF", icon_size=14)
        self.btn_copy_tb.clicked.connect(self._copy_traceback)

        tb_header_layout.addWidget(lbl_traceback)
        tb_header_layout.addStretch()
        tb_header_layout.addWidget(self.btn_copy_tb)

        self.txt_traceback = QTextEdit()
        self.txt_traceback.setReadOnly(True)
        self.txt_traceback.setPlainText(self.traceback_text)

        self.lbl_error = QLabel()
        self.lbl_error.setProperty("state", "error")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        self.content_layout.addWidget(header_card)
        self.content_layout.addSpacing(4)
        self.content_layout.addLayout(form_layout)
        self.content_layout.addSpacing(4)
        self.content_layout.addLayout(tb_header_layout)
        self.content_layout.addWidget(self.txt_traceback)
        self.content_layout.addWidget(self.lbl_error)

        self.btn_send = ModernButton(self.btn_send_text, role="action_danger_border")
        self.btn_send.clicked.connect(self._send_and_close)

        self.add_action_buttons(None, self.btn_send)

    def _copy_traceback(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.traceback_text)
        self.btn_copy_tb.setText(self.copied_toast_text)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.btn_copy_tb.setText(self.btn_copy_text))

    @Slot()
    def _send_and_close(self):
        webhook_url = self.webhook_url
        worker_cls = self.worker_class

        if not webhook_url or not worker_cls:
            self.lbl_error.setText(self.err_no_webhook_text)
            self.lbl_error.show()
            return

        self.btn_send.setEnabled(False)
        self.btn_send.setText(self.i18n.get("crash.btn_sending"))
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        self.worker = worker_cls(
            traceback_text=self.traceback_text,
            contact=self.txt_contact.text(),
            description=self.txt_desc.toPlainText(),
            i18n=self.i18n
        )
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self, success: bool, message: str):
        QApplication.restoreOverrideCursor()
        self.btn_send.setEnabled(True)
        self.btn_send.setText(self.btn_send_text)

        if success:
            self.accept()
        else:
            self.lbl_error.setText(message)
            self.lbl_error.show()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.wait(1000)
        super().closeEvent(event)
