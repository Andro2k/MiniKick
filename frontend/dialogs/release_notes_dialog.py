# frontend\dialogs\release_notes_dialog.py

from PySide6.QtWidgets import (
    QLabel, QTextBrowser, QPushButton, QHBoxLayout, 
    QWidget, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont
from .base_dialog import ModernModal
from frontend.common import (
    get_assets_path, COLOR_GREEN, COLOR_NEUTRAL_400, COLOR_RED,
    markdown_to_github_html, SPACING_MD, MARGIN_V_XS
)

class ReleaseNotesDialog(ModernModal):
    def __init__(self, i18n, worker_class=None, browser_service=None, parent=None):
        self.i18n = i18n
        self.worker_class = worker_class
        self.browser_service = browser_service
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
        meta_layout.setContentsMargins(*MARGIN_V_XS)
        meta_layout.setSpacing(SPACING_MD)
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
            return

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
            url_str = url.toString()
            if self.browser_service and hasattr(self.browser_service, "open_url"):
                self.browser_service.open_url(url_str)
            else:
                QDesktopServices.openUrl(url)

    def _open_github_release(self):
        if self._release_url:
            if self.browser_service and hasattr(self.browser_service, "open_url"):
                self.browser_service.open_url(self._release_url)
            else:
                QDesktopServices.openUrl(QUrl(self._release_url))

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.blockSignals(True)
            self._worker.quit()
            self._worker.wait(1000)
        super().closeEvent(event)
