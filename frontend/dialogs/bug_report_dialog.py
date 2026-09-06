# frontend\dialogs\bug_report_dialog.py

from PySide6.QtWidgets import QLabel, QLineEdit, QTextEdit, QCheckBox, QHBoxLayout, QVBoxLayout

from .base_dialog import ModernModal
from frontend.widgets import ModernButton
from frontend.common import get_assets_path
from frontend.components.dialogs import SeverityCard, ImageDropzone

class BugReportDialog(ModernModal):
    def __init__(self, i18n, worker_class=None, initial_contact: str = "", parent=None):
        title = i18n.get("settings.feedback.title")
        icon_path = get_assets_path("icons/bug.svg")
        super().__init__(title=title, icon_path=icon_path, icon_bg_color="", width=720, parent=parent)
        self.i18n = i18n
        self.worker_class = worker_class
        self.worker = None

        self.initial_contact = initial_contact or ""

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
        if self.initial_contact:
            self.txt_username.setText(self.initial_contact)

        lbl_desc = QLabel(self.i18n.get("dialogs.bug_report.lbl_description"))
        lbl_desc.setProperty("role", "body")
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_desc"))

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

        self.btn_cancel = ModernButton(self.i18n.get("common.buttons.cancel"), role="action_outlined")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_send = ModernButton(self.i18n.get("dialogs.bug_report.btn_send_low"), role="action_accent")
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

        worker_cls = self.worker_class
        if not worker_cls:
            self._set_loading(False)
            return

        self.worker = worker_cls(
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
