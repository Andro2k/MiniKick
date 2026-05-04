import os
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

from backend.services.updater_services import GithubUpdateProvider, WindowsInstaller
from backend.updater_manager import UpdateManager
from frontend.main_window import MainWindow
from frontend.theme import GLOBAL_QSS
from frontend.utils import resource_path

# --- NUEVAS IMPORTACIONES ---
from backend.services.instance_services import SocketInstanceProvider

def bootstrap():
    env_path = resource_path(".env")
    load_dotenv(env_path)
    
    app = QApplication(sys.argv)
    
    # Control de instancia única (lo que agregamos antes)
    instance_provider = SocketInstanceProvider(port=45678)
    if instance_provider.is_already_running():
        QMessageBox.warning(None, "MiniKick", "La aplicación ya se encuentra en ejecución.")
        sys.exit(1)
        
    try:
        app.setQuitOnLastWindowClosed(False)
        
        # --- DEFINIMOS LA VERSIÓN AQUÍ (Única fuente de verdad) ---
        APP_VERSION = "v1.0.5"
        
        github_provider = GithubUpdateProvider(repo_owner="Andro2k", repo_name="MiniKick")
        windows_installer = WindowsInstaller()
        
        # Pasamos la variable al Updater
        updater = UpdateManager(
            current_version=APP_VERSION, 
            checker=github_provider,
            downloader=github_provider,
            installer=windows_installer
        )

        app.setStyleSheet(GLOBAL_QSS)
        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        app.setWindowIcon(QIcon(icon_path))

        # Pasamos la variable a la Ventana Principal
        window = MainWindow(updater_manager=updater, app_version=APP_VERSION)
        window.show()
        sys.exit(app.exec())
        
    finally:
        instance_provider.cleanup()

if __name__ == "__main__":
    bootstrap()