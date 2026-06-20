# frontend/core/container.py

import os
import sys
from backend.sqlite_manager import (DatabaseManager, SQLiteCommandsStorage, 
                                 SQLiteTokenStorage, SQLiteSettingsStorage, 
                                 SQLiteAlertsStorage, SQLiteSpamStorage)
from backend.services.backup_service import BackupService
from backend.services.translation_service import TranslationService
from backend.auth_manager import AuthManager
from backend.tts_manager import TTSManager
from backend.services.overlay_server import OverlayServerManager
from backend.services.media_trigger_service import MediaTriggerService
from frontend.utils import resource_path

class AppContainer:
    def __init__(self, parent_widget):
        self.db_manager = DatabaseManager()
        self.token_storage = SQLiteTokenStorage(self.db_manager)
        self.settings_storage = SQLiteSettingsStorage(self.db_manager) 
        self.alerts_storage = SQLiteAlertsStorage(self.db_manager)
        self.commands_storage = SQLiteCommandsStorage(self.db_manager)
        self.spam_storage = SQLiteSpamStorage(self.db_manager)
        self.backup_service = BackupService(
            self.settings_storage, self.alerts_storage, 
            self.commands_storage, self.spam_storage
        )

        self.i18n = self._init_i18n()
        html_path = resource_path(os.path.join("assets", "web", "success.html"))
        self.auth_manager = AuthManager(
            client_id=os.getenv("KICK_CLIENT_ID", ""),
            client_secret=os.getenv("KICK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("KICK_REDIRECT_URI", "http://localhost:8080/auth/callback"),
            storage=self.token_storage,
            success_html_path=html_path
        )
        self.tts_manager = TTSManager()
        self.media_trigger_service = MediaTriggerService(parent_widget)
        self.overlay_server = OverlayServerManager(port=8090)
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