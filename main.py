# main.py

import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QFont, QFontDatabase, QIcon
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg.*=false;qt.qpa.wayland.*=false"
from backend.services.system.updater_service import GithubUpdateProvider, UpdateManager, WindowsInstaller
from frontend.views.main_window_view import MainWindow
from frontend.common.theme import GLOBAL_QSS
from frontend.common.utils import resource_path
from backend.services.system.instance_services import SocketInstanceProvider
from frontend.dialogs.already_running_dialog import AlreadyRunningDialog
from frontend.core.app_container_core import AppContainer


def _get_safe_i18n():
    try:
        return AppContainer(QMainWindow()).i18n
    except Exception as e:
        print(f"[Bootstrap] Advertencia: Falló hidratación de i18n pre-boot ({e})")
        return None


def bootstrap():
    app = QApplication(sys.argv)
    FONT_FILE_PREFIX = "Geist"
    FONT_FAMILY_NAME = "Geist"

    fonts_dir = resource_path(os.path.join("assets", "fonts"))
    
    if os.path.exists(fonts_dir):
        for archivo in os.listdir(fonts_dir):
            if archivo.startswith(FONT_FILE_PREFIX) and archivo.endswith(('.ttf', '.otf')):
                font_path = os.path.join(fonts_dir, archivo)
                QFontDatabase.addApplicationFont(font_path)

    app_font = QFont(FONT_FAMILY_NAME)
    app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(app_font)
    app.setStyleSheet(GLOBAL_QSS)

    instance_provider = SocketInstanceProvider(port=45678)
    if instance_provider.is_already_running():
        i18n_engine = _get_safe_i18n()
        dialog = AlreadyRunningDialog(i18n=i18n_engine)
        dialog.exec()
        sys.exit(1)

    try:
        app.setQuitOnLastWindowClosed(False)
        APP_VERSION = "v1.3.2"
        github_provider = GithubUpdateProvider(repo_owner="Andro2k", repo_name="MiniKick")
        windows_installer = WindowsInstaller()    
        updater = UpdateManager(
            current_version=APP_VERSION, 
            checker=github_provider,
            downloader=github_provider,
            installer=windows_installer
        )
        
        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        app.setWindowIcon(QIcon(icon_path))
        window = MainWindow(updater_manager=updater, app_version=APP_VERSION)
        window.show()
        sys.exit(app.exec())
        
    finally:
        instance_provider.cleanup()

if __name__ == "__main__":
    bootstrap()