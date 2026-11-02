# bootstrap\application.py\\

import logging
import sys
import time

from backend.config import APP_VERSION
from backend.utils.perf import elapsed_ms, perf_phase
from bootstrap.environment import PROCESS_STARTED, set_windows_app_id
from bootstrap.qt_setup import create_application
from bootstrap.services import StartupServices
from frontend.dialogs import SplashScreen

logger = logging.getLogger("minikick.main")

_BANNER = "=" * 66


class Application:
    def __init__(self, services: StartupServices | None = None, logging_setup=None):
        self._services = services or StartupServices()
        self._logging_setup = logging_setup or self._default_logging_setup

    def run(self) -> int:
        t_start = time.perf_counter()
        _, q_log_handler = self._logging_setup()
        self._log_banner()
        set_windows_app_id()

        with perf_phase(logger, "Bootstrap", "Qt application & fonts initialized", logging.DEBUG):
            qt_app = create_application()

        db_manager = self._services.create_database()
        i18n = self._services.create_translator(db_manager)
        splash = self._show_splash(i18n, t_start)

        splash.set_progress(30, i18n.get("splash.check_instance"))
        guard = self._services.create_instance_guard()
        if guard.is_already_running():
            return self._abort_duplicate(splash, i18n)

        try:
            qt_app.setQuitOnLastWindowClosed(False)
            window = self._build_window(splash, i18n, db_manager, q_log_handler)
            self._show_window(window, splash, i18n, t_start)
            logger.info("[Bootstrap] Entering Qt application event loop.")
            return qt_app.exec()
        finally:
            logger.info("[Bootstrap] Cleaning up instance socket lock.")
            guard.cleanup()

    @staticmethod
    def _default_logging_setup():
        from backend.core import setup_application_logging
        return setup_application_logging()

    def _log_banner(self) -> None:
        logger.info(
            "[Perf/Bootstrap] Python module imports completed in %.2f ms",
            elapsed_ms(PROCESS_STARTED),
        )
        logger.info(_BANNER)
        logger.info(
            "MiniKick Starting | Version: %s | Platform: %s | Python: %s",
            APP_VERSION, sys.platform, sys.version.split()[0],
        )
        logger.info(_BANNER)

    def _show_splash(self, i18n, t_start: float) -> SplashScreen:
        splash = SplashScreen(i18n=i18n, app_version=APP_VERSION)
        splash.showMaximized()
        splash.set_progress(15, i18n.get("splash.init_app"))
        logger.info("[Perf/Bootstrap] Splash displayed %.2f ms after bootstrap started", elapsed_ms(t_start))
        return splash

    def _abort_duplicate(self, splash: SplashScreen, i18n) -> int:
        logger.warning("[Bootstrap] Duplicate instance detected. Presenting AlreadyRunningDialog.")
        splash.close()
        from frontend.dialogs import AlreadyRunningDialog
        AlreadyRunningDialog(i18n=i18n).exec()
        return 1

    def _build_window(self, splash: SplashScreen, i18n, db_manager, q_log_handler):
        from frontend.main_window import MainWindowCore

        splash.set_progress(50, i18n.get("splash.init_services"))
        with perf_phase(logger, "Startup", "Core services initialized"):
            container = self._services.create_container(db_manager, i18n)
        updater = self._services.create_updater()

        splash.set_progress(75, i18n.get("splash.init_ui"))
        logger.info("[Bootstrap] Initializing MainWindowCore...")
        with perf_phase(logger, "Bootstrap", "MainWindowCore instantiated", logging.DEBUG):
            return MainWindowCore(
                container=container,
                q_log_handler=q_log_handler,
                updater_manager=updater,
                app_version=APP_VERSION,
            )

    def _show_window(self, window, splash: SplashScreen, i18n, t_start: float) -> None:
        logger.info("[Bootstrap] Displaying main window (restoring state)...")
        splash.set_progress(100, i18n.get("splash.ready"))
        window.restore_window_state()
        splash.finish(window)
        logger.info("[Perf/Bootstrap] Window displayed (Total bootstrap: %.2f ms)", elapsed_ms(t_start))