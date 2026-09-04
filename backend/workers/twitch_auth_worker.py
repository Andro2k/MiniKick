# backend\workers\twitch_auth_worker.py

import logging
from PySide6.QtCore import QThread, Signal
from backend.services.auth import TwitchAuthManager

logger = logging.getLogger("minikick.workers.twitch_auth")

class TwitchAuthWorker(QThread):
    auth_success = Signal(object)
    auth_error = Signal(str)

    def __init__(self, twitch_auth_manager: TwitchAuthManager, force: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Twitch_Auth")
        self.auth_manager = twitch_auth_manager
        self.force = force

    def run(self):
        logger.info("[TwitchAuthWorker] Starting Twitch OAuth flow (force=%s)...", self.force)
        try:
            tokens = self.auth_manager.login(force=self.force)
            logger.info("[TwitchAuthWorker] Twitch OAuth authentication successful.")
            self.auth_success.emit(tokens)
        except Exception as e:
            logger.error("[TwitchAuthWorker] Exception in Twitch OAuth flow: %s", e)
            self.auth_error.emit(str(e))
