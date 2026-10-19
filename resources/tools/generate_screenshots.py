
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

os.environ["AV_LOG_LEVEL"] = "fatal"
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.*=false;qt.multimedia.ffmpeg.*=false;qt.qpa.wayland.*=false"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

from backend.config import APP_VERSION
from backend.services.system import (
    GithubUpdateProvider, UpdateManager, WindowsInstaller
)
from frontend.main_window import MainWindowCore
from frontend.common import GLOBAL_QSS, create_dark_palette

def generate_screenshots():
    print("=" * 60)
    print("[*] GENERADOR DE SCREENSHOTS DE ALTA RESOLUCION (v1.6.0)")
    print("=" * 60)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setPalette(create_dark_palette())
    font_family = "Google Sans"

    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts"))
    if os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.endswith(('.ttf', '.otf')):
                QFontDatabase.addApplicationFont(os.path.join(fonts_dir, f))

    app_font = QFont(font_family, 10)
    app_font.setPointSize(10)
    app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(app_font)
    app.setStyleSheet(GLOBAL_QSS)

    github_provider = GithubUpdateProvider(repo_owner="Andro2k", repo_name="MiniKick")
    windows_installer = WindowsInstaller()
    updater = UpdateManager(
        current_version=APP_VERSION,
        checker=github_provider,
        downloader=github_provider,
        installer=windows_installer
    )

    window = MainWindowCore(updater_manager=updater, app_version=APP_VERSION)
    window.resize(1920, 1080)
    window.show()
    app.processEvents()
    time.sleep(0.5)

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "screenshots"))
    os.makedirs(out_dir, exist_ok=True)

    def capture(name: str):
        app.processEvents()
        time.sleep(0.3)
        app.processEvents()
        pix = window.grab()
        target = os.path.join(out_dir, f"{name}.png")
        pix.save(target, "PNG")
        print(f"  [OK] Capturado: {name}.png ({pix.width()}x{pix.height()})")

    print("[*] Capturando Dashboard...")
    window._handle_navigation("Dashboard")
    capture("dashboard_preview")

    print("[*] Capturando Chat (Ajustes de Voz)...")
    window._handle_navigation("Chat")
    if hasattr(window, "view_chat") and window.view_chat:
        window.view_chat.tabs.setCurrentIndex(0)
    capture("chat_settings_preview")

    print("[*] Capturando Chat (Overlay OBS con nuevo mockup Messenger)...")
    if hasattr(window, "view_chat") and window.view_chat:
        window.view_chat.tabs.setCurrentIndex(2)
    capture("chat_overlay_preview")

    print("[*] Capturando Reproductor de Música...")
    window._handle_navigation("Music")
    capture("music_player_preview")

    print("[*] Capturando Alertas...")
    window._handle_navigation("Alerts")
    capture("alerts_preview")

    print("[*] Capturando Recompensas...")
    window._handle_navigation("Triggers")
    capture("rewards_preview")

    print("[*] Capturando Widgets...")
    window._handle_navigation("Widgets")
    capture("widgets_preview")

    print("[*] Capturando Programación de Directos...")
    window._handle_navigation("Stream Info")
    capture("schedule_preview")

    window.close()
    print("\n[OK] Todas las capturas fueron actualizadas con exito.")

if __name__ == "__main__":
    generate_screenshots()
