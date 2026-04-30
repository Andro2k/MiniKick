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
    env_path = resource_path(".env")
    load_dotenv(env_path)
    
    app = QApplication(sys.argv)
    
    # Aseguramos que la app no muera cuando la última ventana se oculta (Minimizar a tray)
    app.setQuitOnLastWindowClosed(False)
    
    app.setStyleSheet(GLOBAL_QSS)

    icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    bootstrap()