# main.py

import os
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont, QFontDatabase, QIcon
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg.*=false;qt.qpa.wayland.*=false"
from backend.services.updater_services import GithubUpdateProvider, WindowsInstaller
from backend.updater_manager import UpdateManager
from frontend.main_window_view import MainWindow
from frontend.theme import GLOBAL_QSS
from frontend.utils import resource_path
from backend.services.instance_services import SocketInstanceProvider

def bootstrap():
    app = QApplication(sys.argv)
    FONT_FILE_PREFIX = "Inter"
    FONT_FAMILY_NAME = "Inter"

    fonts_dir = resource_path(os.path.join("assets", "fonts"))
    
    if os.path.exists(fonts_dir):
        for archivo in os.listdir(fonts_dir):
            if archivo.startswith(FONT_FILE_PREFIX) and archivo.endswith(('.ttf', '.otf')):
                font_path = os.path.join(fonts_dir, archivo)
                QFontDatabase.addApplicationFont(font_path)

    app_font = QFont(FONT_FAMILY_NAME)
    app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(app_font)

    instance_provider = SocketInstanceProvider(port=45678)
    if instance_provider.is_already_running():
        QMessageBox.warning(None, "MiniKick", "La aplicación ya se encuentra en ejecución.")
        sys.exit(1)
    try:
        app.setQuitOnLastWindowClosed(False)
        APP_VERSION = "v1.2.5"
        github_provider = GithubUpdateProvider(repo_owner="Andro2k", repo_name="MiniKick")
        windows_installer = WindowsInstaller()    
        updater = UpdateManager(
            current_version=APP_VERSION, 
            checker=github_provider,
            downloader=github_provider,
            installer=windows_installer
        )
        app.setStyleSheet(GLOBAL_QSS)
        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        app.setWindowIcon(QIcon(icon_path))
        window = MainWindow(updater_manager=updater, app_version=APP_VERSION)
        window.show()
        sys.exit(app.exec())
        
    finally:
        instance_provider.cleanup()

if __name__ == "__main__":
    bootstrap()