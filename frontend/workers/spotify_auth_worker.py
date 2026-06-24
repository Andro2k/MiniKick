# frontend/workers/spotify_auth_worker.py

from PySide6.QtCore import QThread, Signal
from backend.music.spotify_client import SpotifyAuthManager

class SpotifyAuthWorker(QThread):
    auth_success = Signal(dict)
    auth_error = Signal(str)

    def __init__(self, i18n, spotify_auth: SpotifyAuthManager, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.spotify_auth = spotify_auth

    def run(self):
        try:
            tokens = self.spotify_auth.storage.load()
            if not tokens or not self.spotify_auth.get_access_token():
                tokens = self.spotify_auth.login()
            
            self.auth_success.emit(tokens)
        except TimeoutError:
            err_msg = self.i18n.get("spotify.error.timeout")
            self.auth_error.emit(err_msg)
        except Exception as e:
            err_prefix = self.i18n.get("spotify.error.generic")
            self.auth_error.emit(f"{err_prefix} {str(e)}")