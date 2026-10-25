# bootstrap/crash.py

import logging
import sys
import traceback
from typing import Callable

from bootstrap.qt_setup import get_or_create_application
from bootstrap.translator import load_translator

logger = logging.getLogger("minikick.main")


class CrashHandler:
    def __init__(
        self,
        app_provider: Callable = get_or_create_application,
        translator_provider: Callable = load_translator,
    ):
        self._app_provider = app_provider
        self._translator_provider = translator_provider

    def handle(self, exctype, value, tb) -> None:
        tb_text = "".join(traceback.format_exception(exctype, value, tb))
        self._persist(tb_text)
        print(tb_text, file=sys.stderr)
        self._show_dialog(tb_text)
        sys.exit(1)

    def _persist(self, tb_text: str) -> None:
        message = f"Unhandled exception caught by global excepthook:\n{tb_text}"
        try:
            from backend.core import flush_all_logs, write_fault_log_record
            logger.critical(message)
            write_fault_log_record(logging.CRITICAL, "minikick.main", message)
            flush_all_logs()
        except Exception:
            pass

    def _show_dialog(self, tb_text: str) -> None:
        i18n = None
        try:
            self._app_provider()
            i18n = self._translator_provider()

            from backend.config import DISCORD_WEBHOOK_URL
            from backend.workers import CrashReportWorker
            from frontend.dialogs import CrashReportDialog

            CrashReportDialog(
                traceback_text=tb_text,
                i18n=i18n,
                webhook_url=DISCORD_WEBHOOK_URL,
                worker_class=CrashReportWorker,
                initial_contact=self._get_initial_contact(),
            ).exec()
        except Exception as dialog_err:
            print(self._dialog_error_message(i18n, dialog_err), file=sys.stderr)

    @staticmethod
    def _get_initial_contact() -> str:
        try:
            from backend.database import DatabaseManager
            return DatabaseManager().get_primary_identity()
        except Exception:
            return ""

    @staticmethod
    def _dialog_error_message(i18n, error: Exception) -> str:
        if i18n:
            return i18n.get("logs.bootstrap.crash_dialog_failed").replace("{error}", str(error))
        return f"[Bootstrap] Failed to display crash dialog: {error}"