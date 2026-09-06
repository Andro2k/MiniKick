# frontend\dialogs\bug_report_dialog.py

from PySide6.QtWidgets import QLabel, QLineEdit, QTextEdit, QCheckBox, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt

from .base_dialog import ModernModal
from frontend.widgets import ModernButton
from frontend.common import get_assets_path, SPACING_SM, SPACING_MD, SPACING_XL, MARGIN_V_XS
from frontend.components.dialogs import SeverityCard, ImageDropzone

class BugReportDialog(ModernModal):
    def __init__(self, i18n, worker_class=None, initial_contact: str = "", parent=None):
        title = i18n.get("settings.feedback.title")
        icon_path = get_assets_path("icons/bug.svg")
        super().__init__(title=title, icon_path=icon_path, icon_bg_color="", width=660, parent=parent)
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
        sev_layout.setSpacing(SPACING_MD)

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

        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(SPACING_XL)

        contact_col = QVBoxLayout()
        contact_col.setSpacing(SPACING_SM)
        lbl_username = QLabel(self.i18n.get("dialogs.bug_report.lbl_contact"))
        lbl_username.setProperty("role", "body")
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_contact"))
        if self.initial_contact:
            self.txt_username.setText(self.initial_contact)
        contact_col.addWidget(lbl_username)
        contact_col.addWidget(self.txt_username)

        logs_col = QVBoxLayout()
        logs_col.setSpacing(SPACING_SM)
        lbl_logs = QLabel(self.i18n.get("dialogs.bug_report.lbl_diagnostics"))
        lbl_logs.setProperty("role", "body")
        self.chk_logs = QCheckBox(self.i18n.get("dialogs.bug_report.chk_include_logs"))
        self.chk_logs.setChecked(True)
        self.chk_logs.setCursor(Qt.CursorShape.PointingHandCursor)
        
        chk_wrapper = QHBoxLayout()
        chk_wrapper.setContentsMargins(*MARGIN_V_XS)
        chk_wrapper.addWidget(self.chk_logs)
        chk_wrapper.addStretch()

        logs_col.addWidget(lbl_logs)
        logs_col.addLayout(chk_wrapper)

        row1_layout.addLayout(contact_col, 1)
        row1_layout.addLayout(logs_col, 1)

        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(SPACING_XL)

        desc_col = QVBoxLayout()
        desc_col.setSpacing(SPACING_SM)
        lbl_desc = QLabel(self.i18n.get("dialogs.bug_report.lbl_description"))
        lbl_desc.setProperty("role", "body")
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_desc"))
        self.txt_desc.setFixedHeight(140)
        desc_col.addWidget(lbl_desc)
        desc_col.addWidget(self.txt_desc)

        image_col = QVBoxLayout()
        image_col.setSpacing(SPACING_SM)
        lbl_image = QLabel(self.i18n.get("dialogs.bug_report.lbl_image"))
        lbl_image.setProperty("role", "body")
        self.dropzone = ImageDropzone(self.i18n)
        image_col.addWidget(lbl_image)
        image_col.addWidget(self.dropzone)

        row2_layout.addLayout(desc_col, 1)
        row2_layout.addLayout(image_col, 1)

        self.lbl_error = QLabel()
        self.lbl_error.setProperty("state", "error")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        self.content_layout.addWidget(lbl_sev_header)
        self.content_layout.addLayout(sev_layout)
        self.content_layout.addSpacing(SPACING_SM)
        self.content_layout.addLayout(row1_layout)
        self.content_layout.addSpacing(SPACING_SM)
        self.content_layout.addLayout(row2_layout)
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
