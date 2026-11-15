# frontend\views\bug_report_view.py
"""Vista para enviar reportes de error y sugerencias."""

from PySide6.QtWidgets import QLabel, QLineEdit, QTextEdit, QCheckBox, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt, Signal

from frontend.views.base_view import BaseView
from frontend.widgets import ModernButton, ModernCard, create_row_layout, create_labeled_field, create_error_label
from frontend.common import Size
from frontend.components.dialog_parts import SeverityCard, ImageDropzone

_SEND_KEYS = {
    "Low": "dialogs.bug_report.btn_send_low",
    "Medium": "dialogs.bug_report.btn_send_medium",
    "Urgent": "dialogs.bug_report.btn_send_urgent",
}


class BugReportView(BaseView):
    submit_requested = Signal(str, str, bool, str, str)

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="settings.feedback.title", subtitle_key="settings.feedback.desc", parent=parent)
        self.selected_severity = "Low"
        self.severity_cards: dict[str, SeverityCard] = {}
        self._setup_ui()

    def _setup_ui(self):
        card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_MD)

        lbl_sev = QLabel(self.i18n.get("dialogs.bug_report.severity_title"))
        lbl_sev.setProperty("role", "text_body")
        lbl_sev.setProperty("state", "bold")
        sev_layout = QHBoxLayout()
        sev_layout.setSpacing(Size.SPACING_MD)
        for key in _SEND_KEYS:
            name = key.lower()
            sev_card = SeverityCard(key, self.i18n.get(f"dialogs.bug_report.severity_{name}"),
                                    self.i18n.get(f"dialogs.bug_report.severity_{name}_desc"))
            sev_card.clicked.connect(self._on_severity_selected)
            self.severity_cards[key] = sev_card
            sev_layout.addWidget(sev_card, 1)
        self.severity_cards["Low"].set_selected(True)

        row_contact = create_row_layout(spacing=Size.SPACING_XL)
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_contact"))
        contact_col, _ = create_labeled_field(
            self.i18n.get("dialogs.bug_report.lbl_contact"), self.txt_username,
            role="text_body", spacing=Size.SPACING_SM)

        logs_col = QVBoxLayout()
        logs_col.setSpacing(Size.SPACING_SM)
        lbl_logs = QLabel(self.i18n.get("dialogs.bug_report.lbl_diagnostics"))
        lbl_logs.setProperty("role", "text_body")
        self.chk_logs = QCheckBox(self.i18n.get("dialogs.bug_report.chk_include_logs"))
        self.chk_logs.setChecked(True)
        self.chk_logs.setCursor(Qt.CursorShape.PointingHandCursor)
        chk_wrapper = QHBoxLayout()
        chk_wrapper.setContentsMargins(*Size.Margin.MRG_VXS)
        chk_wrapper.addWidget(self.chk_logs)
        chk_wrapper.addStretch()
        logs_col.addWidget(lbl_logs)
        logs_col.addLayout(chk_wrapper)
        row_contact.addLayout(contact_col, 1)
        row_contact.addLayout(logs_col, 1)

        row_body = create_row_layout(spacing=Size.SPACING_XL)
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_desc"))
        self.txt_desc.setMinimumHeight(180)
        desc_col, _ = create_labeled_field(
            self.i18n.get("dialogs.bug_report.lbl_description"), self.txt_desc,
            role="text_body", spacing=Size.SPACING_SM)
        self.dropzone = ImageDropzone(self.i18n)
        image_col, _ = create_labeled_field(
            self.i18n.get("dialogs.bug_report.lbl_image"), self.dropzone,
            role="text_body", spacing=Size.SPACING_SM)
        row_body.addLayout(desc_col, 1)
        row_body.addLayout(image_col, 1)

        self.lbl_error = create_error_label(self)

        self.btn_send = ModernButton(self.i18n.get(_SEND_KEYS["Low"]), role="action_outlined")
        self.btn_send.clicked.connect(self._on_send_clicked)
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(self.btn_send)

        card.addWidget(lbl_sev)
        card.addLayout(sev_layout)
        card.addLayout(row_contact)
        card.addLayout(row_body)
        card.addWidget(self.lbl_error)
        card.addLayout(footer)
        self.main_layout.addWidget(card)
        self.main_layout.addStretch()

    def set_contact(self, contact: str) -> None:
        if contact and not self.txt_username.text():
            self.txt_username.setText(contact)

    def set_loading(self, loading: bool) -> None:
        for widget in (self.btn_send, self.txt_username, self.txt_desc, self.chk_logs, self.dropzone, *self.severity_cards.values()):
            widget.setEnabled(not loading)
        if loading:
            self.btn_send.setText(self.i18n.get("dialogs.bug_report.btn_sending"))
        else:
            self._refresh_send_text()

    def show_error(self, message: str) -> None:
        self.lbl_error.setText(message)
        self.lbl_error.show()

    def reset_form(self) -> None:
        self.txt_desc.clear()
        self.dropzone.clear_image()
        self.lbl_error.hide()
        self._on_severity_selected("Low")

    def _on_severity_selected(self, key: str) -> None:
        self.selected_severity = key
        for k, sev_card in self.severity_cards.items():
            sev_card.set_selected(k == key)
        self._refresh_send_text()

    def _refresh_send_text(self) -> None:
        self.btn_send.setText(self.i18n.get(_SEND_KEYS[self.selected_severity]))

    def _on_send_clicked(self) -> None:
        desc = self.txt_desc.toPlainText().strip()
        if not desc:
            self.show_error(self.i18n.get("dialogs.bug_report.err_empty_desc"))
            return
        self.lbl_error.hide()
        self.submit_requested.emit(self.txt_username.text(), desc, self.chk_logs.isChecked(),
                                   self.dropzone.image_path or "", self.selected_severity)
