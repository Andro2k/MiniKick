# main.py
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

from backend.services.updater_services import GithubUpdateProvider, WindowsInstaller
from backend.updater_manager import UpdateManager
from frontend.main_window import MainWindow
from frontend.theme import GLOBAL_QSS
from frontend.utils import resource_path

def bootstrap():
    env_path = resource_path(".env")
    load_dotenv(env_path)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # --- INYECCIÓN DE DEPENDENCIAS (PRODUCCIÓN REAL) ---
    # Coloca exactamente tu usuario y el nombre del repositorio en GitHub
    github_provider = GithubUpdateProvider(repo_owner="Andro2k", repo_name="MiniKick")
    windows_installer = WindowsInstaller()
    
    # Ensamblamos el manager UNA SOLA VEZ
    updater = UpdateManager(
        current_version="v1.0.2", # Asegúrate de que tenga la "v" si usas tags con "v" en GitHub
        checker=github_provider,
        downloader=github_provider,
        installer=windows_installer
    )

    app.setStyleSheet(GLOBAL_QSS)

    icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
    app.setWindowIcon(QIcon(icon_path))

    # Pasamos el manager a la ventana principal
    window = MainWindow(updater_manager=updater)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    bootstrap()