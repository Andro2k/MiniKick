# backend\workers\auth_worker.py

from PySide6.QtCore import QThread, Signal
from backend.services.auth.oauth_service import AuthManager

class AuthWorker(QThread):
    auth_success = Signal(object)
    auth_error = Signal(str)

    def __init__(self, i18n, auth_manager: AuthManager, force: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Auth")
        self.i18n = i18n
        self.auth_manager = auth_manager
        self.force = force

    def run(self):
        try:
            tokens = self.auth_manager.get_tokens(force=self.force)
            if tokens:
                self.auth_success.emit(tokens)
            else:
                self.auth_error.emit(self.i18n.get("main.workers.auth.error_failed"))
        except Exception as e:
            self.auth_error.emit(str(e))
