# frontend\dialogs\release_notes_dialog.py

import re
from functools import lru_cache
from PySide6.QtWidgets import (
    QLabel, QTextBrowser, QPushButton, QHBoxLayout, 
    QWidget, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont
from .base_dialog import ModernModal
from frontend.common import get_assets_path
from frontend.common.theme import (
    COLOR_GREEN, COLOR_NEUTRAL_900, COLOR_NEUTRAL_850, COLOR_NEUTRAL_800, COLOR_NEUTRAL_400, COLOR_NEUTRAL_200, COLOR_WHITE, COLOR_RED
)

_RE_LATEX_O     = re.compile(r'\$\\mathcal\{O\}\((.*?)\)\$')
_RE_LATEX_MATH  = re.compile(r'\$(.*?)\$')
_RE_FILE_LINKS  = re.compile(r'\[([^\]]+)\]\((?:file:///[^\)]+|[a-zA-Z0-9_\-/\\\.]+\.(?:py|json|md|html))\)')
_RE_HTTP_LINKS  = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
_RE_INLINE_CODE = re.compile(r'`([^`]+)`')
_RE_BOLD        = re.compile(r'\*\*([^\*]+)\*\*')
_RE_ITALIC      = re.compile(r'(?<!\*)\*([^\*]+)\*(?!\*)')
_RE_CALLOUT     = re.compile(r'^>\s*\[!(NOTE|IMPORTANT|WARNING|TIP|CAUTION)\]', re.IGNORECASE)
_RE_TABLE_DIV   = re.compile(r'^[\s\-:]+$')
_NERD_FONT_FAMILY = "'GoogleSansCode Nerd Font', 'GoogleSansCode NF', Consolas, monospace"
_CALLOUT_STYLES = {
    'NOTE': ('#3b82f6', '#60a5fa', '\udb80\udefc', 'Note', 'rgba(59, 130, 246, 0.08)'),
    'IMPORTANT': ('#a855f7', '#c084fc', '\udb80\udf61', 'Important', 'rgba(168, 85, 247, 0.08)'),
    'WARNING': ('#eab308', '#facc15', '\uf40c', 'Warning', 'rgba(234, 179, 8, 0.08)'),
    'TIP': ('#22c55e', '#4ade80', '\udb81\udee8', 'Tip', 'rgba(34, 197, 94, 0.08)'),
    'CAUTION': ('#ef4444', '#f87171', '\udb80\udc29', 'Caution', 'rgba(239, 68, 68, 0.08)')
}
_CODE_SPAN = f'<code style="font-family: {_NERD_FONT_FAMILY}; background-color: {COLOR_NEUTRAL_800}; color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-size: 11px;">\\1</code>'
_CODE_INLINE_SPAN = f'<code style="font-family: {_NERD_FONT_FAMILY}; background-color: {COLOR_NEUTRAL_800}; color: {COLOR_NEUTRAL_200}; padding: 2px 6px; border-radius: 4px; font-size: 11px;">\\1</code>'

@lru_cache(maxsize=16)
def markdown_to_github_html(md: str) -> str:
    if not md:
        return ""

    text = _RE_LATEX_O.sub(f'<span style="font-family: {_NERD_FONT_FAMILY}; color: #a5b4fc; font-weight: bold;">O(\\1)</span>', md)
    text = _RE_LATEX_MATH.sub(f'<span style="font-family: {_NERD_FONT_FAMILY}; color: #a5b4fc;">\\1</span>', text)
    text = _RE_FILE_LINKS.sub(_CODE_SPAN, text)
    text = _RE_HTTP_LINKS.sub(r'<a href="\2" style="color: #38bdf8; text-decoration: underline;">\1</a>', text)
    text = _RE_INLINE_CODE.sub(_CODE_INLINE_SPAN, text)
    text = _RE_BOLD.sub(r'<b>\1</b>', text)
    text = _RE_ITALIC.sub(r'<i>\1</i>', text)

    lines = text.splitlines()
    html_out = []

    in_table = False
    table_rows = []

    in_callout = False
    callout_type = ''
    callout_lines = []

    def flush_callout():
        nonlocal in_callout, callout_type, callout_lines
        if in_callout and callout_type in _CALLOUT_STYLES:
            border_c, title_c, icon_glyph, label, bg_c = _CALLOUT_STYLES[callout_type]
            body_content = "<br/>".join(callout_lines)
            icon_span = f'<span style="font-family: {_NERD_FONT_FAMILY}; font-size: 13px;">{icon_glyph}</span>'
            html_out.append(
                f'<div style="border-left: 3px solid {border_c}; background-color: {bg_c}; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0;">'
                f'<div style="color: {title_c}; font-weight: bold; margin-bottom: 6px; font-size: 13px;">{icon_span} {label}</div>'
                f'<div style="color: {COLOR_NEUTRAL_200}; font-size: 13px; line-height: 1.5;">{body_content}</div>'
                f'</div>'
            )
        in_callout = False
        callout_type = ''
        callout_lines = []

    def flush_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html_out.append('<table style="border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 12px;">')
            for r_idx, row in enumerate(table_rows):
                bg_row = COLOR_NEUTRAL_850 if r_idx == 0 else COLOR_NEUTRAL_900
                html_out.append(f'<tr style="background-color: {bg_row};">')
                cell_tag = 'th' if r_idx == 0 else 'td'
                cell_color = COLOR_NEUTRAL_400 if r_idx == 0 else COLOR_NEUTRAL_200
                weight = "font-weight: bold;" if r_idx == 0 else ""
                for cell in row:
                    html_out.append(f'<{cell_tag} style="border: 1px solid {COLOR_NEUTRAL_800}; padding: 7px 10px; color: {cell_color}; text-align: left; {weight}">{cell}</{cell_tag}>')
                html_out.append('</tr>')
            html_out.append('</table>')
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()

        callout_match = _RE_CALLOUT.match(stripped)
        if callout_match:
            flush_table()
            flush_callout()
            in_callout = True
            callout_type = callout_match.group(1).upper()
            continue

        if in_callout:
            if stripped.startswith('>'):
                callout_lines.append(stripped.lstrip('>').strip())
                continue
            flush_callout()

        if stripped.startswith('|') and stripped.endswith('|'):
            flush_callout()
            cols = [c.strip() for c in stripped.strip('|').split('|')]
            if all(_RE_TABLE_DIV.match(c) for c in cols):
                continue
            in_table = True
            table_rows.append(cols)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        if stripped.startswith('# '):
            html_out.append(f'<h1 style="color: {COLOR_WHITE}; font-size: 18px; font-weight: bold; border-bottom: 1px solid {COLOR_NEUTRAL_800}; padding-bottom: 6px; margin: 16px 0 10px 0;">{stripped[2:]}</h1>')
        elif stripped.startswith('## '):
            html_out.append(f'<h2 style="color: {COLOR_WHITE}; font-size: 16px; font-weight: bold; border-bottom: 1px solid {COLOR_NEUTRAL_800}; padding-bottom: 4px; margin: 14px 0 8px 0;">{stripped[3:]}</h2>')
        elif stripped.startswith('### '):
            html_out.append(f'<h3 style="color: {COLOR_NEUTRAL_200}; font-size: 14px; font-weight: bold; margin: 10px 0 6px 0;">{stripped[4:]}</h3>')
        elif stripped in ('---', '***'):
            html_out.append(f'<hr style="border: none; border-top: 1px solid {COLOR_NEUTRAL_800}; margin: 14px 0;" />')
        elif stripped.startswith(('- ', '* ')):
            html_out.append(f'<div style="color: {COLOR_NEUTRAL_200}; font-size: 13px; margin: 4px 0 4px 16px; line-height: 1.5;">• {stripped[2:]}</div>')
        elif stripped.startswith(('• ', '◦ ')):
            html_out.append(f'<div style="color: {COLOR_NEUTRAL_200}; font-size: 13px; margin: 4px 0 4px 16px; line-height: 1.5;">{stripped}</div>')
        else:
            html_out.append(f'<p style="color: {COLOR_NEUTRAL_200}; font-size: 13px; margin: 6px 0; line-height: 1.5;">{stripped}</p>')

    flush_callout()
    flush_table()

    body = "\n".join(html_out)
    return (
        f'<html><head><style>'
        f'body {{ font-family: "Google Sans", "Segoe UI", sans-serif; color: {COLOR_NEUTRAL_200}; font-size: 13px; }}'
        f'code {{ font-family: {_NERD_FONT_FAMILY}; }}'
        f'</style></head>'
        f'<body style="font-family: \'Google Sans\', \'Segoe UI\', sans-serif; color: {COLOR_NEUTRAL_200}; background-color: transparent;">{body}</body></html>'
    )


class ReleaseNotesDialog(ModernModal):
    def __init__(self, i18n, worker_class=None, parent=None):
        self.i18n = i18n
        self.worker_class = worker_class
        super().__init__(
            title=self.i18n.get("dialogs.release_notes.title"),
            icon_path=get_assets_path("icons/file-text.svg"),
            icon_bg_color=COLOR_GREEN,
            width=700,
            parent=parent
        )
        self.set_dialog_state("accent", QColor(46, 205, 112, 60))
        self._release_url = "https://github.com/Andro2k/MiniKick/releases/latest"
        self._worker = None

        self._setup_ui()
        self._fetch_release_notes()

    def _setup_ui(self):
        self.lbl_subtitle = QLabel(self.i18n.get("dialogs.release_notes.subtitle"))
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setWordWrap(True)
        self.lbl_subtitle.setProperty("role", "body")
        self.content_layout.addWidget(self.lbl_subtitle)

        self.meta_container = QWidget(self.container)
        meta_layout = QHBoxLayout(self.meta_container)
        meta_layout.setContentsMargins(0, 4, 0, 4)
        meta_layout.setSpacing(8)
        meta_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_tag_badge = QLabel("", parent=self.meta_container)
        self.lbl_tag_badge.setProperty("role", "badge_kick")

        self.lbl_published = QLabel("", parent=self.meta_container)
        self.lbl_published.setProperty("role", "caption")

        self.lbl_author = QLabel("", parent=self.meta_container)
        self.lbl_author.setProperty("role", "caption")

        meta_layout.addWidget(self.lbl_tag_badge)
        meta_layout.addWidget(self.lbl_published)
        meta_layout.addWidget(self.lbl_author)

        self.content_layout.addWidget(self.meta_container)
        self.meta_container.hide()

        self.txt_content = QTextBrowser(self.container)
        self.txt_content.setOpenExternalLinks(False)
        self.txt_content.anchorClicked.connect(self._handle_anchor_clicked)
        self.txt_content.setReadOnly(True)
        self.txt_content.setProperty("role", "release_notes_browser")
        self.txt_content.setFixedHeight(480)
        self.txt_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Fixed)

        base_font = QFont("Google Sans", 10)
        base_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.txt_content.setFont(base_font)

        loading_msg = self.i18n.get('dialogs.release_notes.loading')
        self.txt_content.setHtml(
            f'<html><body style="font-family: \'Google Sans\', sans-serif; color: {COLOR_NEUTRAL_400}; text-align: center; margin-top: 180px;">'
            f'<i>{loading_msg}</i></body></html>'
        )
        self.content_layout.addWidget(self.txt_content)
        self.content_layout.addStretch()

        self.btn_github = QPushButton(self.i18n.get("dialogs.release_notes.btn_github"))
        self.btn_github.setProperty("role", "action_accent")
        self.btn_github.clicked.connect(self._open_github_release)

        self.btn_close = QPushButton(self.i18n.get("common.buttons.close"))
        self.btn_close.setProperty("role", "action_outlined")
        self.btn_close.clicked.connect(self.reject)

        self.add_action_buttons(self.btn_close, self.btn_github, stretch_center=False)

    def showEvent(self, event):
        super().showEvent(event)
        self._center_on_parent()

    def _center_on_parent(self):
        parent = self.parentWidget() or (self.parent() if isinstance(self.parent(), QWidget) else None)
        if parent:
            p_geo = parent.geometry()
            x = p_geo.x() + (p_geo.width() - self.width()) // 2
            y = p_geo.y() + (p_geo.height() - self.height()) // 2
            self.move(max(0, x), max(0, y))
        else:
            screen = self.screen() or QApplication.primaryScreen()
            if screen:
                s_geo = screen.availableGeometry()
                x = s_geo.x() + (s_geo.width() - self.width()) // 2
                y = s_geo.y() + (s_geo.height() - self.height()) // 2
                self.move(max(0, x), max(0, y))

    def _fetch_release_notes(self):
        worker_cls = self.worker_class
        if not worker_cls:
            from backend.workers import ReleaseNotesWorker
            worker_cls = ReleaseNotesWorker

        self._worker = worker_cls(parent=self)
        self._worker.release_fetched.connect(self._on_release_fetched)
        self._worker.error_occurred.connect(self._on_error_occurred)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_release_fetched(self, data: dict):
        tag_name = data.get("tag_name", "")
        release_name = data.get("name", "") or tag_name
        published_raw = data.get("published_at", "")
        published_date = published_raw.split("T")[0] if "T" in published_raw else published_raw
        author_raw = data.get("author", "")
        author = author_raw.get("login", "") if isinstance(author_raw, dict) else str(author_raw or "")
        body_text = data.get("body", "")
        self._release_url = data.get("html_url", self._release_url)

        if release_name:
            self.title_lbl.setText(release_name)

        if tag_name:
            self.lbl_tag_badge.setText(tag_name)
            self.lbl_tag_badge.show()

        if published_date:
            pub_text = self.i18n.get("dialogs.release_notes.lbl_published").replace("{date}", published_date)
            self.lbl_published.setText(pub_text)
            self.lbl_published.show()

        if author:
            auth_text = self.i18n.get("dialogs.release_notes.lbl_author").replace("{author}", author)
            self.lbl_author.setText(auth_text)
            self.lbl_author.show()

        self.meta_container.show()

        if body_text:
            cleaned_html = markdown_to_github_html(body_text)
            self.txt_content.setHtml(cleaned_html)
        
        self._center_on_parent()

    def _on_error_occurred(self, err: str):
        error_msg = self.i18n.get('dialogs.release_notes.error')
        err_html = (
            f'<html><body style="font-family: \'Google Sans\', sans-serif; color: {COLOR_RED}; text-align: center; margin-top: 180px;">'
            f'⚠️ <i>{error_msg}</i></body></html>'
        )
        self.txt_content.setHtml(err_html)

    def _handle_anchor_clicked(self, url: QUrl):
        if url.scheme() in ("http", "https"):
            QDesktopServices.openUrl(url)

    def _open_github_release(self):
        if self._release_url:
            QDesktopServices.openUrl(QUrl(self._release_url))

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.blockSignals(True)
            self._worker.quit()
            self._worker.wait(1000)
        super().closeEvent(event)
