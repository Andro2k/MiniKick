# frontend\components\dialog_parts\log_preview_panel.py
"""Panel de solo lectura que muestra el final del log que se adjuntará al reporte."""

import re

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QSizePolicy
from PySide6.QtCore import Signal
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

from frontend.common import BrandColors, Palette, Size, Typography
from frontend.widgets import ModernButton

_LINE_RE = re.compile(r"^(\[[^\]]+\])(\s+)(\[[A-Za-z0-9_]+\])")


def _level_color(level: str) -> str:
    name = level.strip("[]").upper()
    if name.startswith(("ERR", "CRI")) or "CRASH" in name:
        return BrandColors.RED
    if name.startswith(("WARN", "WRN")):
        return BrandColors.AMBER
    if name.startswith(("INF", "BOOT")):
        return BrandColors.BLUE
    return Palette.NEUTRAL_400


def _format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB"):
        if value < 1024 or unit == "MB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


class LogLevelHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text: str) -> None:
        match = _LINE_RE.match(text)
        if match is None:
            return
        time_fmt = QTextCharFormat()
        time_fmt.setForeground(QColor(Palette.NEUTRAL_500))
        level_fmt = QTextCharFormat()
        level_fmt.setForeground(QColor(_level_color(match.group(3))))
        level_fmt.setFontWeight(700)
        self.setFormat(match.start(1), len(match.group(1)), time_fmt)
        self.setFormat(match.start(3), len(match.group(3)), level_fmt)


class LogPreviewPanel(QFrame):
    refresh_requested = Signal()
    open_folder_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._shown = 0
        self._attached = True
        self.setProperty("role", "card")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Size.Margin.MRG_MED)
        layout.setSpacing(Size.SPACING_SM)

        header = QHBoxLayout()
        header.setSpacing(Size.SPACING_SM)
        titles = QVBoxLayout()
        titles.setSpacing(Size.SPACING_NN)
        self.lbl_title = QLabel(self.i18n.get("dialogs.bug_report.log_preview_title"))
        self.lbl_title.setProperty("role", "text_body")
        self.lbl_title.setProperty("state", "bold")
        self.lbl_meta = QLabel()
        self.lbl_meta.setProperty("role", "text_caption")
        titles.addWidget(self.lbl_title)
        titles.addWidget(self.lbl_meta)

        self.btn_refresh = ModernButton(self.i18n.get("dialogs.bug_report.log_btn_refresh"), role="action_outlined", icon_name="refresh-cw.svg")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        self.btn_folder = ModernButton(self.i18n.get("dialogs.bug_report.log_btn_open"), role="action_outlined", icon_name="folder-open.svg")
        self.btn_folder.clicked.connect(self.open_folder_requested.emit)

        header.addLayout(titles, 1)
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_folder)

        self.viewer = QPlainTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.viewer.setStyleSheet(f"font-family: '{Typography.CHAT_FONT_FAMILY}', 'MesloLGM NF', monospace;")
        self.viewer.setMinimumHeight(180)
        self.viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._highlighter = LogLevelHighlighter(self.viewer.document())

        self.lbl_notice = QLabel()
        self.lbl_notice.setProperty("role", "text_caption")
        self.lbl_notice.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(self.viewer)
        layout.addWidget(self.lbl_notice)
        self.set_attached(True)

    def set_preview(self, preview: dict) -> None:
        if not preview.get("exists"):
            self.viewer.setPlainText("")
            self.lbl_meta.setText(self.i18n.get("dialogs.bug_report.log_empty"))
            return
        self.viewer.setPlainText(preview["text"])
        scroll = self.viewer.verticalScrollBar()
        scroll.setValue(scroll.maximum())
        meta = (self.i18n.get("dialogs.bug_report.log_meta", lines=preview["total_lines"], size=_format_size(preview["size"])))
        self.lbl_meta.setText(meta)
        self._shown = preview["shown_lines"]
        self.set_attached(self._attached)

    def set_attached(self, attached: bool) -> None:
        self._attached = attached
        self.viewer.setEnabled(attached)
        key = "dialogs.bug_report.log_attached_note" if attached else "dialogs.bug_report.log_excluded_note"
        note = self.i18n.get(key, count=self._shown)
        self.lbl_notice.setText(note)
