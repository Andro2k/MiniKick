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

logger = logging.getLogger("minikick.core.app_container")

from backend.database import (
    DatabaseManager, SQLiteCommandsStorage, SQLiteTokenStorage, SQLiteSettingsStorage, 
    SQLiteRewardsStorage, SQLiteSpamStorage, SQLiteTimersStorage, SQLiteWidgetsStorage,
    SQLiteAvatarStorage, SQLiteSystemLogStorage, SQLiteMusicStorage, SQLiteScheduleStorage,
    SQLiteAlertStorage
)
from backend.services import (
    BackupService, TranslationService, KickAuthManager, TwitchAuthManager, 
    SettingsService, AvatarService, WidgetService, ScheduleService,
    TTSManager, OverlayServerManager, AlertService
)
from frontend.common.paths import resource_path

class AppContainerCore:
    def __init__(self):
        logger.debug("[AppContainer] Initializing database manager and SQLite storage layers...")
        self.db_manager = DatabaseManager()
        self.commands_storage = SQLiteCommandsStorage(self.db_manager)
        self.kick_token_storage = SQLiteTokenStorage(self.db_manager, provider="kick")
        self.twitch_token_storage = SQLiteTokenStorage(self.db_manager, provider="twitch")
        self.settings_storage = SQLiteSettingsStorage(self.db_manager)
        self.rewards_storage = SQLiteRewardsStorage(self.db_manager)
        self.spam_storage = SQLiteSpamStorage(self.db_manager)
        self.timers_storage = SQLiteTimersStorage(self.db_manager)
        self.widgets_storage = SQLiteWidgetsStorage(self.db_manager)
        self.avatar_storage = SQLiteAvatarStorage(self.db_manager)
        self.system_log_storage = SQLiteSystemLogStorage(self.db_manager)
        self.music_storage = SQLiteMusicStorage(self.db_manager)
        self.schedule_storage = SQLiteScheduleStorage(self.db_manager)
        self.alert_storage = SQLiteAlertStorage(self.db_manager)

        logger.debug("[AppContainer] Initializing core services (Backup, Settings, Avatar, Widget, Schedule)...")
        self.backup_service = BackupService(
            settings_storage=self.settings_storage,
            rewards_storage=self.rewards_storage,
            commands_storage=self.commands_storage,
            spam_storage=self.spam_storage,
            timers_storage=self.timers_storage,
            schedule_storage=self.schedule_storage
        )
        self.settings_service = SettingsService(self.settings_storage, self.backup_service)
        self.i18n = self._init_i18n()
        self.avatar_service = AvatarService(avatar_storage=self.avatar_storage, db_manager=self.db_manager)
        self.widget_service = WidgetService(self.widgets_storage)
        self.schedule_service = ScheduleService(self.schedule_storage)

        auth_html_path = resource_path(os.path.join("assets", "web", "auth.html"))

        logger.debug("[AppContainer] Initializing Kick and Twitch OAuth managers...")
        self.kick_auth_manager = KickAuthManager(
            client_id=KICK_CLIENT_ID,
            client_secret=KICK_CLIENT_SECRET,
            redirect_uri=KICK_REDIRECT_URI,
            storage=self.kick_token_storage,
            success_html_path=auth_html_path
        )

        self.twitch_auth_manager = TwitchAuthManager(
            client_id=TWITCH_CLIENT_ID,
            client_secret=TWITCH_CLIENT_SECRET,
            redirect_uri=TWITCH_REDIRECT_URI,
            storage=self.twitch_token_storage,
            success_html_path=auth_html_path
        )

        logger.debug("[AppContainer] Initializing TTS Manager and Overlay Server...")
        self.tts_manager = TTSManager()
        self.overlay_server = OverlayServerManager(settings_storage=self.settings_storage)
        self.overlay_server.start()
        self.alert_service = AlertService(
            storage=self.alert_storage,
            overlay_server=self.overlay_server,
            tts_service=self.tts_manager
        )
        self.overlay_server.on_alert_finished = self.alert_service.ack_alert
        logger.info("[AppContainer] Core dependency container initialized successfully.")
        self._music_provider = None

    @property
    def music_provider(self):
        return self.get_music_provider()

    def get_music_provider(self):
        if self._music_provider is None:
            from backend.providers.music.youtube_client import YouTubeMusicProvider
            self._music_provider = YouTubeMusicProvider(self.i18n, music_storage=self.music_storage, db_manager=self.db_manager)
        return self._music_provider


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
                    if install_lang != saved_lang:
                        saved_lang = install_lang
                        ts.set_language(saved_lang)
                try:
                    os.remove(install_lang_path)
                except OSError:
                    pass
            except Exception as e:
                logger.debug("[AppContainer] Notice reading .install_lang: %s", e)

        if getattr(sys, "_api_keys_missing", False):
            logger.warning(ts.get("logs.app_container.api_keys_not_found"))
        return ts

    def shutdown(self):
        if hasattr(self, '_music_provider') and self._music_provider:
            if hasattr(self._music_provider, "shutdown"):
                self._music_provider.shutdown()
        if hasattr(self, 'tts_manager') and self.tts_manager:
            if hasattr(self.tts_manager, "stop"):
                self.tts_manager.stop()
        if hasattr(self, 'overlay_server') and self.overlay_server:
            if hasattr(self.overlay_server, "stop"):
                self.overlay_server.stop()
