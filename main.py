# main.py
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

from frontend.main_window import MainWindow
from frontend.theme import GLOBAL_QSS
from frontend.utils import resource_path

def bootstrap():
    load_dotenv()
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)

    icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    bootstrap()