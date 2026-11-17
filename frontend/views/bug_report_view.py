# frontend\views\bug_report_view.py
"""Vista para enviar reportes de error y sugerencias."""

from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QTextEdit, QCheckBox, QHBoxLayout, QVBoxLayout, QBoxLayout
from PySide6.QtCore import Qt, Signal

from frontend.views.base_view import BaseView
from frontend.widgets import ModernButton, ModernCard, create_labeled_field, create_error_label
from frontend.common import Palette, Size, get_pixmap_colored
from frontend.components.dialog_parts import SeverityCard, ImageDropzone, LogPreviewPanel

_SEND_KEYS = {
    "Low": "dialogs.bug_report.btn_send_low",
    "Medium": "dialogs.bug_report.btn_send_medium",
    "Urgent": "dialogs.bug_report.btn_send_urgent",
}
_STACK_BREAKPOINT = 900


class BugReportView(BaseView):
    submit_requested = Signal(str, str, bool, str, str)
    log_refresh_requested = Signal()
    log_folder_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="settings.feedback.title", subtitle_key="settings.feedback.desc", parent=parent)
        self.selected_severity = "Low"
        self.severity_cards: dict[str, SeverityCard] = {}
        self._flex_rows: list[QBoxLayout] = []
        self._stacked = False
        self._setup_ui()

    def _flex_row(self, *items, spacing: int = Size.SPACING_XL) -> QBoxLayout:
        row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        row.setContentsMargins(*Size.Margin.MRG_NON)
        row.setSpacing(spacing)
        for item in items:
            if isinstance(item, QBoxLayout):
                row.addLayout(item, 1)
            else:
                row.addWidget(item, 1)
        self._flex_rows.append(row)
        return row

    def _bold_label(self, key: str) -> QLabel:
        lbl = QLabel(self.i18n.get(key))
        lbl.setProperty("role", "text_body")
        lbl.setProperty("state", "bold")
        return lbl

    def _build_card_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(Size.SPACING_MD)
        icon = QLabel()
        icon.setPixmap(get_pixmap_colored("bug.svg", Palette.NEUTRAL_400, 24))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles = QVBoxLayout()
        titles.setSpacing(Size.SPACING_NN)
        title = self._bold_label("dialogs.bug_report.form_title")
        subtitle = QLabel(self.i18n.get("dialogs.bug_report.form_subtitle"))
        subtitle.setProperty("role", "text_caption")
        subtitle.setWordWrap(True)
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addWidget(icon)
        header.addLayout(titles, 1)
        return header

    def _build_severity_row(self) -> QBoxLayout:
        cards = []
        for key in _SEND_KEYS:
            name = key.lower()
            sev_card = SeverityCard(key, self.i18n.get(f"dialogs.bug_report.severity_{name}"),
                                    self.i18n.get(f"dialogs.bug_report.severity_{name}_desc"))
            sev_card.clicked.connect(self._on_severity_selected)
            self.severity_cards[key] = sev_card
            cards.append(sev_card)
        self.severity_cards["Low"].set_selected(True)
        return self._flex_row(*cards, spacing=Size.SPACING_MD)

    def _build_contact_row(self) -> QBoxLayout:
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_contact"))
        contact_col, _ = create_labeled_field(
            self.i18n.get("dialogs.bug_report.lbl_contact"), self.txt_username,
            role="text_body", spacing=Size.SPACING_SM)

        self.chk_logs = QCheckBox(self.i18n.get("dialogs.bug_report.chk_include_logs"))
        self.chk_logs.setChecked(True)
        self.chk_logs.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_logs.toggled.connect(self._on_include_logs_toggled)
        logs_col = QVBoxLayout()
        logs_col.setSpacing(Size.SPACING_SM)
        logs_col.addWidget(self._bold_label("dialogs.bug_report.lbl_diagnostics"))
        logs_col.addWidget(self.chk_logs)
        logs_col.addStretch()
        return self._flex_row(contact_col, logs_col)

    def _build_body_row(self) -> QBoxLayout:
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(self.i18n.get("dialogs.bug_report.placeholder_desc"))
        self.txt_desc.setMinimumHeight(200)
        desc_col, _ = create_labeled_field(
            self.i18n.get("dialogs.bug_report.lbl_description"), self.txt_desc,
            role="text_body", spacing=Size.SPACING_SM)
        self.dropzone = ImageDropzone(self.i18n)
        image_col, _ = create_labeled_field(
            self.i18n.get("dialogs.bug_report.lbl_image"), self.dropzone,
            role="text_body", spacing=Size.SPACING_SM)
        return self._flex_row(desc_col, image_col)

    def _build_footer(self) -> QHBoxLayout:
        self.btn_reset = ModernButton(self.i18n.get("dialogs.bug_report.btn_reset"), role="action_outlined")
        self.btn_reset.clicked.connect(self.reset_form)
        self.btn_send = ModernButton(self.i18n.get(_SEND_KEYS["Low"]), role="action_accent_solid")
        self.btn_send.clicked.connect(self._on_send_clicked)
        footer = QHBoxLayout()
        footer.setSpacing(Size.SPACING_MD)
        footer.addWidget(self.btn_reset)
        footer.addStretch()
        footer.addWidget(self.btn_send)
        return footer

    def _setup_ui(self):
        card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_MD)
        card.addLayout(self._build_card_header())
        card.add_separator()
        card.addWidget(self._bold_label("dialogs.bug_report.severity_title"))
        card.addLayout(self._build_severity_row())
        card.addLayout(self._build_contact_row())
        card.addLayout(self._build_body_row())

        self.log_panel = LogPreviewPanel(self.i18n)
        self.log_panel.refresh_requested.connect(self.log_refresh_requested.emit)
        self.log_panel.open_folder_requested.connect(self.log_folder_requested.emit)
        card.addWidget(self.log_panel)

        self.lbl_error = create_error_label(self)
        card.addWidget(self.lbl_error)
        card.add_separator()
        card.addLayout(self._build_footer())
        self.main_layout.addWidget(card)
        self.main_layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        stacked = self.width() < _STACK_BREAKPOINT
        if stacked == self._stacked:
            return
        self._stacked = stacked
        direction = QBoxLayout.Direction.TopToBottom if stacked else QBoxLayout.Direction.LeftToRight
        for row in self._flex_rows:
            row.setDirection(direction)

    def set_contact(self, contact: str) -> None:
        if contact and not self.txt_username.text():
            self.txt_username.setText(contact)

    def set_log_preview(self, preview: dict) -> None:
        self.log_panel.set_preview(preview)

    def set_loading(self, loading: bool) -> None:
        for widget in (self.btn_send, self.btn_reset, self.txt_username, self.txt_desc, self.chk_logs, self.dropzone, *self.severity_cards.values()):
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

    def _on_include_logs_toggled(self, checked: bool) -> None:
        self.log_panel.set_attached(checked)

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
