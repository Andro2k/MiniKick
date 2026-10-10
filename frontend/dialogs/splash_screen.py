# frontend\dialogs\splash_screen.py

import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QApplication
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtSvg import QSvgRenderer

from frontend.common import (
    resolve_icon_path, resource_path,
    MARGIN_NONE, SPACING_SM
)

logger = logging.getLogger("minikick.splash")


class SplashScreen(QWidget):
    def __init__(self, i18n, app_version: str = "", parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.app_version = app_version
        self._is_finished = False

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("role", "splash_window")

        title = self.i18n.get("splash.title") if hasattr(self.i18n, "get") else "MiniKick"
        self.setWindowTitle(title)

        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

        self._setup_ui()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(*MARGIN_NONE)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame(self)
        self.card.setProperty("role", "splash_card")
        self.card.setFixedWidth(440)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(*MARGIN_NONE)
        card_layout.setSpacing(0)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(*MARGIN_NONE)
        logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_logo = QLabel(self.card)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._render_logo(size=72)
        logo_row.addWidget(self.lbl_logo)
        card_layout.addLayout(logo_row)

        card_layout.addSpacing(20)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(*MARGIN_NONE)
        title_row.setSpacing(SPACING_SM)
        title_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_title = QLabel(self.i18n.get("splash.title"), parent=self.card)
        self.lbl_title.setProperty("role", "h1")
        title_row.addWidget(self.lbl_title)

        if self.app_version:
            clean_ver = self.app_version if self.app_version.startswith("v") else f"v{self.app_version}"
            self.lbl_version = QLabel(clean_ver, parent=self.card)
            self.lbl_version.setProperty("role", "badge_kick")
            title_row.addWidget(self.lbl_version)

        card_layout.addLayout(title_row)
        card_layout.addSpacing(6)

        self.lbl_subtitle = QLabel(self.i18n.get("splash.subtitle"), parent=self.card)
        self.lbl_subtitle.setProperty("role", "caption")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_subtitle, 0, Qt.AlignmentFlag.AlignCenter)

        card_layout.addSpacing(28)

        self.progress_bar = QProgressBar(parent=self.card)
        self.progress_bar.setProperty("role", "splash_progress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setFixedWidth(340)

        progress_row = QHBoxLayout()
        progress_row.setContentsMargins(*MARGIN_NONE)
        progress_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_row.addWidget(self.progress_bar)
        card_layout.addLayout(progress_row)

        card_layout.addSpacing(12)

        self.lbl_status = QLabel(self.i18n.get("splash.loading"), parent=self.card)
        self.lbl_status.setProperty("role", "caption")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_status, 0, Qt.AlignmentFlag.AlignCenter)

        outer_layout.addWidget(self.card)

    def _render_logo(self, size: int = 72):
        logo_path = resolve_icon_path("logo.svg")
        if not logo_path:
            return

        app = QApplication.instance()
        dpr = app.primaryScreen().devicePixelRatio() if app and app.primaryScreen() else 1.0
        physical_size = int(size * dpr)

        try:
            renderer = QSvgRenderer(logo_path)
            pixmap = QPixmap(physical_size, physical_size)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter, QRectF(0, 0, physical_size, physical_size))
            painter.end()

            pixmap.setDevicePixelRatio(dpr)
            self.lbl_logo.setPixmap(pixmap)
            self.lbl_logo.setFixedSize(size, size)
        except Exception as e:
            logger.warning("[SplashScreen] Failed to render logo: %s", e)

    def set_progress(self, value: int, message: str = ""):
        clamped = max(0, min(100, int(value)))
        self.progress_bar.setValue(clamped)
        if message:
            self.lbl_status.setText(message)
        app = QApplication.instance()
        if app and self.isVisible():
            app.processEvents()

    def finish(self, main_window: QWidget | None = None):
        self._is_finished = True
        if main_window:
            if not main_window.isVisible():
                main_window.show()
            main_window.raise_()
            main_window.activateWindow()
        self.close()
        self.deleteLater()

    def closeEvent(self, event):
        if not getattr(self, "_is_finished", False):
            event.accept()
        else:
            super().closeEvent(event)
