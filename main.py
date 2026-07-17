# main.py

from backend.database import SQLiteSettingsStorage
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase, QIcon
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg.*=false;qt.qpa.wayland.*=false"
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
from backend.services import GithubUpdateProvider, UpdateManager, WindowsInstaller
from frontend.core.main_window_core import MainWindowCore
from frontend.common.theme import GLOBAL_QSS
from frontend.common.utils import resource_path
from backend.services import SocketInstanceProvider
from frontend.dialogs.already_running_dialog import AlreadyRunningDialog
from backend.config.version import APP_VERSION


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
        print(f"[Bootstrap] Advertencia: Falló hidratación de i18n pre-boot ({e})")
        return None


def global_crash_handler(exctype, value, tb):
    import traceback
    tb_text = "".join(traceback.format_exception(exctype, value, tb))
    
    try:
        import logging
        logging.critical("Unhandled exception captured by global exception hook:\n%s", tb_text)
    except Exception:
        pass

    print(tb_text, file=sys.stderr)

    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            from frontend.common.theme import GLOBAL_QSS
            app.setStyleSheet(GLOBAL_QSS)
            
            FONT_FAMILY_NAME = "Google Sans"
            app_font = QFont(FONT_FAMILY_NAME)
            app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            app.setFont(app_font)

        i18n = _get_safe_i18n()
        from frontend.dialogs.crash_report_dialog import CrashReportDialog
        dialog = CrashReportDialog(traceback_text=tb_text, i18n=i18n)
        dialog.exec()
    except Exception as dialog_err:
        print(f"[Bootstrap] Falló la visualización del diálogo de crash: {dialog_err}", file=sys.stderr)

    sys.exit(1)


def bootstrap():
    app = QApplication(sys.argv)
    FONT_FILE_PREFIX = "GoogleSans"
    FONT_FAMILY_NAME = "Google Sans"

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
        window = MainWindowCore(updater_manager=updater, app_version=APP_VERSION)
        window.show()
        sys.exit(app.exec())
        
    finally:
        instance_provider.cleanup()

if __name__ == "__main__":
    sys.excepthook = global_crash_handler
    bootstrap()