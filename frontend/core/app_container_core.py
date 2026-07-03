# frontend\core\app_container_core.py

import os
import sys
try:
    from backend.config.api_keys import (
        KICK_CLIENT_ID, KICK_CLIENT_SECRET, KICK_REDIRECT_URI,
        SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
    )
except ImportError:
    print("ADVERTENCIA: Archivo backend/api_keys.py no encontrado. Usando credenciales vacías.")
    KICK_CLIENT_ID = ""
    KICK_CLIENT_SECRET = ""
    KICK_REDIRECT_URI = "http://localhost:8080/auth/callback"
    SPOTIFY_CLIENT_ID = ""
    SPOTIFY_CLIENT_SECRET = ""
    SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080/auth/callback"

from backend.providers.spotify.spotify_client import SpotifyAuthManager, SpotifyMusicProvider
from backend.storage.database import (DatabaseManager, SQLiteCommandsStorage, 
                                 SQLiteTokenStorage, SQLiteSettingsStorage, 
                                 SQLiteRewardsStorage, SQLiteSpamStorage)
from backend.services.system.backup_service import BackupService
from backend.services.system.translation_service import TranslationService
from backend.services.auth.oauth_service import AuthManager
from backend.providers.tts.tts_service import TTSManager
from backend.services.stream.overlay_server import OverlayServerManager
from backend.services.stream.media_trigger import MediaTriggerService
from frontend.common.utils import resource_path

class AppContainer:
    def __init__(self, parent_widget):
        self.db_manager = DatabaseManager()
        self.kick_token_storage = SQLiteTokenStorage(self.db_manager, provider="kick")
        self.spotify_token_storage = SQLiteTokenStorage(self.db_manager, provider="spotify")
        self.settings_storage = SQLiteSettingsStorage(self.db_manager) 
        self.rewards_storage = SQLiteRewardsStorage(self.db_manager)
        self.commands_storage = SQLiteCommandsStorage(self.db_manager)
        self.spam_storage = SQLiteSpamStorage(self.db_manager)
        self.backup_service = BackupService(
            self.settings_storage, self.rewards_storage, 
            self.commands_storage, self.spam_storage
        )
        self.i18n = self._init_i18n()
        html_path = resource_path(os.path.join("assets", "web", "auth.html"))
        
        self.auth_manager = AuthManager(
            client_id=KICK_CLIENT_ID,
            client_secret=KICK_CLIENT_SECRET,
            redirect_uri=KICK_REDIRECT_URI,
            storage=self.kick_token_storage,
            success_html_path=html_path
        )
        
        self.spotify_auth = SpotifyAuthManager(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            storage=self.spotify_token_storage,
            success_html_path=html_path
        )
        self.music_provider = SpotifyMusicProvider(self.spotify_auth, self.i18n)
        
        self.tts_manager = TTSManager()
        self.media_trigger_service = MediaTriggerService(parent_widget)
        self.overlay_server = OverlayServerManager(port=8090, settings_storage=self.settings_storage)
        self.overlay_server.start()

    def _init_i18n(self) -> TranslationService:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        install_lang_path = os.path.join(app_dir, ".install_lang")
        if os.path.exists(install_lang_path):
            try:
                with open(install_lang_path, 'r', encoding='utf-8') as f:
                    install_lang = f.read().strip()
                if install_lang in ["es", "en"]:
                    self.settings_storage.save_string("app_language", install_lang)
                os.remove(install_lang_path)
            except Exception:
                pass
        saved_lang = self.settings_storage.load_string("app_language", "es")
        return TranslationService(default_lang=saved_lang)

    def shutdown(self):
        self.tts_manager.stop()
        self.overlay_server.stop()