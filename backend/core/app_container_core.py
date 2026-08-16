# backend\core\app_container_core.py

import os
import sys
import logging

try:
    import backend.config.api_keys as _api_keys
    KICK_CLIENT_ID = getattr(_api_keys, "KICK_CLIENT_ID", "")
    KICK_CLIENT_SECRET = getattr(_api_keys, "KICK_CLIENT_SECRET", "")
    KICK_REDIRECT_URI = getattr(_api_keys, "KICK_REDIRECT_URI", "http://localhost:8080/auth/callback")
    TWITCH_CLIENT_ID = getattr(_api_keys, "TWITCH_CLIENT_ID", "")
    TWITCH_CLIENT_SECRET = getattr(_api_keys, "TWITCH_CLIENT_SECRET", "")
    TWITCH_REDIRECT_URI = getattr(_api_keys, "TWITCH_REDIRECT_URI", "http://localhost:8080/auth/callback")
except ImportError:
    sys._api_keys_missing = True
    KICK_CLIENT_ID = ""
    KICK_CLIENT_SECRET = ""
    KICK_REDIRECT_URI = "http://localhost:8080/auth/callback"
    TWITCH_CLIENT_ID = ""
    TWITCH_CLIENT_SECRET = ""
    TWITCH_REDIRECT_URI = "http://localhost:8080/auth/callback"

from backend.providers import YouTubeMusicProvider
from backend.database import (DatabaseManager, SQLiteCommandsStorage, SQLiteTokenStorage, SQLiteSettingsStorage, 
                            SQLiteRewardsStorage, SQLiteSpamStorage, SQLiteTimersStorage, SQLiteWidgetsStorage,
                            SQLiteAvatarStorage, SQLiteSystemLogStorage, SQLiteMusicStorage, SQLiteScheduleStorage)
from backend.services import (BackupService, TranslationService, AuthManager, TwitchAuthManager, OverlayServerManager, 
                              MediaTriggerService, TTSManager, WidgetService, ScheduleService)
from frontend.common.utils import resource_path

class AppContainer:
    def __init__(self, parent_widget):
        self.db_manager = DatabaseManager()
        self.kick_token_storage = SQLiteTokenStorage(self.db_manager, provider="kick")
        self.twitch_token_storage = SQLiteTokenStorage(self.db_manager, provider="twitch")
        self.settings_storage = SQLiteSettingsStorage(self.db_manager) 
        self.rewards_storage = SQLiteRewardsStorage(self.db_manager)
        self.commands_storage = SQLiteCommandsStorage(self.db_manager)
        self.spam_storage = SQLiteSpamStorage(self.db_manager)
        self.timers_storage = SQLiteTimersStorage(self.db_manager)
        self.widgets_storage = SQLiteWidgetsStorage(self.db_manager)
        self.avatar_storage = SQLiteAvatarStorage(self.db_manager)
        self.log_storage = SQLiteSystemLogStorage(self.db_manager)
        self.music_storage = SQLiteMusicStorage(self.db_manager)
        self.schedule_storage = SQLiteScheduleStorage(self.db_manager)
        self.stream_schedule_storage = self.schedule_storage
        self.widget_service = WidgetService(self.widgets_storage)
        self.backup_service = BackupService(
            self.settings_storage, self.rewards_storage, 
            self.commands_storage, self.spam_storage,
            self.timers_storage, self.schedule_storage
        )
        self.i18n = self._init_i18n()
        self.schedule_service = ScheduleService(self.schedule_storage, i18n=self.i18n)
        self.stream_info_service = self.schedule_service
        html_path = resource_path(os.path.join("assets", "web", "auth.html"))
        
        self.auth_manager = AuthManager(
            client_id=KICK_CLIENT_ID,
            client_secret=KICK_CLIENT_SECRET,
            redirect_uri=KICK_REDIRECT_URI,
            storage=self.kick_token_storage,
            success_html_path=html_path
        )
        
        self.twitch_auth_manager = TwitchAuthManager(
            client_id=TWITCH_CLIENT_ID,
            client_secret=TWITCH_CLIENT_SECRET,
            redirect_uri=TWITCH_REDIRECT_URI,
            storage=self.twitch_token_storage,
            success_html_path=html_path
        )
        
        self.music_provider = YouTubeMusicProvider(self.i18n, music_storage=self.music_storage, db_manager=self.db_manager)
        
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
        saved_lang = self.settings_storage.load_string("app_language", "es")
        ts = TranslationService(default_lang=saved_lang)
        if os.path.exists(install_lang_path):
            try:
                with open(install_lang_path, 'r', encoding='utf-8') as f:
                    install_lang = f.read().strip()
                if install_lang in ("es", "en"):
                    self.settings_storage.save_string("app_language", install_lang)
                os.remove(install_lang_path)
            except Exception as e:
                logging.error(ts.get("logs.app_container.install_lang_error").replace("{error}", str(e)))
        if getattr(sys, "_api_keys_missing", False):
            logging.warning(ts.get("logs.app_container.api_keys_not_found"))
        return ts

    def shutdown(self):
        if hasattr(self, 'tts_manager') and self.tts_manager:
            self.tts_manager.stop()
        if hasattr(self, 'overlay_server') and self.overlay_server:
            self.overlay_server.stop()
