# resources\tools\generate_screenshots.py

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from bootstrap.environment import configure_environment

configure_environment()

from backend.config import APP_VERSION
from backend.handlers import QLogHandler
from bootstrap.qt_setup import get_or_create_application
from bootstrap.services import StartupServices
from frontend.main_window import MainWindowCore


def build_window() -> MainWindowCore:
    services = StartupServices()
    db_manager = services.create_database()
    i18n = services.create_translator(db_manager)
    return MainWindowCore(
        container=services.create_container(db_manager, i18n),
        q_log_handler=QLogHandler(),
        updater_manager=services.create_updater(),
        app_version=APP_VERSION,
    )


def generate_screenshots():
    print("=" * 60)
    print(f"[*] GENERADOR DE SCREENSHOTS DE ALTA RESOLUCION ({APP_VERSION})")
    print("=" * 60)

    app = get_or_create_application()
    window = build_window()
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
