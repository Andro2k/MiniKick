# backend\workers\kick_auth_worker.py

import logging
from PySide6.QtCore import QThread, Signal
from backend.services.auth.oauth_service import AuthManager

logger = logging.getLogger("minikick.workers.kick_auth")

class KickAuthWorker(QThread):
    auth_success = Signal(object)
    auth_error = Signal(str)

    def __init__(self, i18n, auth_manager: AuthManager, force: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Auth")
        self.i18n = i18n
        self.auth_manager = auth_manager
        self.force = force

    def run(self):
        logger.info("[KickAuthWorker] Starting Kick OAuth flow (force=%s)...", self.force)
        try:
            tokens = self.auth_manager.login(force=self.force)
            if tokens:
                logger.info("[KickAuthWorker] Kick OAuth authentication successful.")
                self.auth_success.emit(tokens)
            else:
                err_msg = self.i18n.get("main.workers.auth.error_failed")
                logger.error("[KickAuthWorker] Kick OAuth failed: %s", err_msg)
                self.auth_error.emit(err_msg)
        except Exception as e:
            logger.error("[KickAuthWorker] Exception in Kick OAuth flow: %s", e)
            self.auth_error.emit(str(e))
