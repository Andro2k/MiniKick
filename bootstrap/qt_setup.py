# bootstrap\qt_setup.py\\

import logging
import os
import sys

from PySide6.QtGui import QIcon, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from frontend.common import get_global_qss, create_dark_palette, resource_path

logger = logging.getLogger("minikick.bootstrap.qt")

FONT_FAMILY = "Google Sans"
FONT_SIZE = 10
_FONT_EXTENSIONS = (".ttf", ".otf")


def get_or_create_application() -> QApplication:
    return QApplication.instance() or create_application()


def create_application() -> QApplication:
    app = QApplication(sys.argv)
    app.setPalette(create_dark_palette())
    _load_fonts()
    app.setFont(_build_font())
    app.setStyleSheet(get_global_qss(12))
    app.setWindowIcon(QIcon(resource_path(os.path.join("assets", "icons", "icon.ico"))))
    return app


def _build_font() -> QFont:
    font = QFont(FONT_FAMILY, FONT_SIZE)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font


def _load_fonts() -> None:
    fonts_dir = resource_path(os.path.join("assets", "fonts"))
    if not os.path.isdir(fonts_dir):
        return
    loaded = sum(
        QFontDatabase.addApplicationFont(os.path.join(fonts_dir, name)) != -1
        for name in os.listdir(fonts_dir)
        if name.endswith(_FONT_EXTENSIONS)
    )
    logger.debug("[Bootstrap] Loaded %d application fonts from %s", loaded, fonts_dir)