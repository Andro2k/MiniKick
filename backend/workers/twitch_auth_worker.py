# backend\workers\twitch_auth_worker.py

from PySide6.QtCore import QThread, Signal
from backend.services.auth.oauth_service import TwitchAuthManager

class TwitchAuthWorker(QThread):
    auth_success = Signal(dict)
    auth_error = Signal(str)

    def __init__(self, twitch_auth_manager: TwitchAuthManager, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Twitch_Auth")
        self.auth_manager = twitch_auth_manager

    def run(self):
        try:
            tokens = self.auth_manager._new_login()
            self.auth_success.emit(tokens)
        except Exception as e:
            self.auth_error.emit(str(e))
