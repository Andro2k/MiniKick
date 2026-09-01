# main.py

import os
import sys

os.environ["AV_LOG_LEVEL"] = "error"
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false;qt.multimedia=false;qt.qpa.wayland.*=false"

import logging
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase, QIcon

try:
    clean_paths = []
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        if not path_dir.strip():
            continue
        try:
            if os.path.exists(path_dir) and os.path.isdir(path_dir):
                os.stat(path_dir)
                clean_paths.append(path_dir)
        except Exception:
            pass
    os.environ["PATH"] = os.pathsep.join(clean_paths)
except Exception:
    pass

if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _ProactorBasePipeTransport.__del__ = lambda self, _warn=None: None
    except Exception:
        pass

from backend.core.app_logger_core import setup_application_logging, flush_all_logs
setup_application_logging()

from backend.services.system.updater_service import GithubUpdateProvider, UpdateManager, WindowsInstaller
from backend.services.system.instance_services import SocketInstanceProvider
from backend.core.main_window_core import MainWindowCore
from backend.config.version import APP_VERSION

from frontend.dialogs.already_running_dialog import AlreadyRunningDialog
from frontend.common.theme import GLOBAL_QSS
from frontend.common.paths import resource_path

logger = logging.getLogger("minikick.main")

def _get_safe_i18n():
    try:
        from backend.database.manager import DatabaseManager
        from backend.database import SQLiteSettingsStorage
        from backend.services import TranslationService
        db = DatabaseManager()
        settings = SQLiteSettingsStorage(db)
        saved_lang = settings.load_string("app_language", "es")
        return TranslationService(default_lang=saved_lang)
    except Exception as e:
        logger.warning("[Bootstrap] Pre-boot i18n hydration failed: %s", e)
        return None


def global_crash_handler(exctype, value, tb):
    tb_text = "".join(traceback.format_exception(exctype, value, tb))
    from datetime import datetime
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        logger.critical("[FATAL CRASH] Unhandled exception caught by global excepthook:\n%s", tb_text)
        from backend.core import app_logger_core
        if getattr(app_logger_core, "_fault_file_handle", None):
            app_logger_core._fault_file_handle.write(f"\n[{now_str}] [FATAL_CRASH] Unhandled exception caught by global excepthook:\n{tb_text}\n")
            app_logger_core._fault_file_handle.flush()
        flush_all_logs()
    except Exception:
        pass

    print(tb_text, file=sys.stderr)

    i18n = None
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            app.setStyleSheet(GLOBAL_QSS)
            
            font_family = "Google Sans"
            app_font = QFont(font_family, 10)
            app_font.setPointSize(10)
            app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            app.setFont(app_font)

        i18n = _get_safe_i18n()
        from backend.config.api_keys import DISCORD_WEBHOOK_URL
        from backend.workers import CrashReportWorker
        from frontend.dialogs.crash_report_dialog import CrashReportDialog
        dialog = CrashReportDialog(
            traceback_text=tb_text,
            i18n=i18n,
            webhook_url=DISCORD_WEBHOOK_URL,
            worker_class=CrashReportWorker
        )
        dialog.exec()
    except Exception as dialog_err:
        err_msg = i18n.get("logs.bootstrap.crash_dialog_failed").replace("{error}", str(dialog_err)) if i18n else f"[Bootstrap] Failed to display crash dialog: {dialog_err}"
        print(err_msg, file=sys.stderr)

    sys.exit(1)


def bootstrap():
    logger.info("==================================================================")
    logger.info("MiniKick Starting | Version: %s | Platform: %s | Python: %s", APP_VERSION, sys.platform, sys.version.split()[0])
    logger.info("==================================================================")

    if sys.platform == "win32":
        try:
            import ctypes
            myappid = "MiniKick"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            logger.debug("[Bootstrap] Set explicit AppUserModelID: %s", myappid)
        except Exception as e:
            logger.debug("[Bootstrap] Could not set AppUserModelID: %s", e)

    app = QApplication(sys.argv)
    font_family = "Google Sans"

    fonts_dir = resource_path(os.path.join("assets", "fonts"))
    loaded_fonts_count = 0
    if os.path.exists(fonts_dir):
        for archivo in os.listdir(fonts_dir):
            if archivo.endswith(('.ttf', '.otf')):
                font_path = os.path.join(fonts_dir, archivo)
                if QFontDatabase.addApplicationFont(font_path) != -1:
                    loaded_fonts_count += 1
    logger.debug("[Bootstrap] Loaded %d application fonts from %s", loaded_fonts_count, fonts_dir)

    app_font = QFont(font_family, 10)
    app_font.setPointSize(10)
    app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(app_font)
    app.setStyleSheet(GLOBAL_QSS)

    logger.debug("[Bootstrap] Checking single-instance socket on port 45678...")
    instance_provider = SocketInstanceProvider(port=45678)
    if instance_provider.is_already_running():
        logger.warning("[Bootstrap] Duplicate instance detected. Presenting AlreadyRunningDialog.")
        i18n_engine = _get_safe_i18n()
        dialog = AlreadyRunningDialog(i18n=i18n_engine)
        dialog.exec()
        sys.exit(1)
    logger.debug("[Bootstrap] Single-instance lock acquired successfully.")

    try:
        app.setQuitOnLastWindowClosed(False)
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
        
        logger.info("[Bootstrap] Initializing MainWindowCore...")
        window = MainWindowCore(updater_manager=updater, app_version=APP_VERSION)
        logger.info("[Bootstrap] Displaying main window...")
        window.show()
        logger.info("[Bootstrap] Entering Qt application event loop.")
        sys.exit(app.exec())
        
    finally:
        logger.info("[Bootstrap] Cleaning up instance socket lock.")
        instance_provider.cleanup()

if __name__ == "__main__":
    sys.excepthook = global_crash_handler
    bootstrap()