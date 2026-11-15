# backend\controllers\bug_report_controller.py
"""Controlador de la vista de reporte de errores."""

import logging
from PySide6.QtCore import Slot
from .base_controller import BaseController

logger = logging.getLogger("minikick.bug_report_controller")


class BugReportController(BaseController):
    def __init__(self, view=None, worker_class=None, toast_manager=None, i18n=None):
        super().__init__(view=view, toast_manager=toast_manager, i18n=i18n)
        self.worker_class = worker_class
        self._worker = None
        self._active_workers = set()
        if self.view is not None:
            self._connect_signals()

    def _connect_signals(self):
        if not self._ensure_view_connected():
            return
        self.view.submit_requested.connect(self._handle_submit)

    def load_initial_data(self):
        try:
            from backend.services.app.identity_service import resolve_primary_identity
            self.view.set_contact(resolve_primary_identity())
        except Exception:
            logger.debug("[BugReport] Could not resolve the primary identity.")

    @Slot(str, str, bool, str, str)
    def _handle_submit(self, username, description, include_logs, image_path, severity):
        if self._worker is not None or self.worker_class is None:
            return
        logger.info("[User Action] Sending bug report (severity=%s)", severity)
        self.view.set_loading(True)
        worker = self.worker_class(
            username=username, description=description, include_logs=include_logs,
            image_path=image_path, i18n=self.i18n, severity=severity,
        )
        self._worker = worker
        self._active_workers.add(worker)
        worker.report_completed.connect(self._on_completed)
        worker.finished.connect(lambda w=worker: self._retire(w))
        worker.start()

    def _on_completed(self, success: bool, message: str):
        self._worker = None
        self.view.set_loading(False)
        if success:
            self.view.reset_form()
            if self.toast:
                self.toast.show_toast(self.i18n.get("dialogs.bug_report.success_title"),
                                      self.i18n.get("dialogs.bug_report.success_msg"), "success")
        else:
            self.view.show_error(message)

    def _retire(self, worker):
        self._active_workers.discard(worker)
        try:
            worker.deleteLater()
        except RuntimeError:
            pass
