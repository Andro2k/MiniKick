# backend\core\app_container_core.py
import logging
import os

from backend.config import (
    API_KEYS_MISSING,
    KICK_CLIENT_ID, KICK_CLIENT_SECRET, KICK_REDIRECT_URI,
    TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_REDIRECT_URI,
)
from backend.database import DatabaseManager, SQLiteCommandsStorage, SQLiteTokenStorage, SQLiteRewardsStorage, SQLiteSpamStorage, SQLiteTimersStorage, SQLiteWidgetsStorage, SQLiteAvatarStorage, SQLiteSystemLogStorage, SQLiteMusicStorage, SQLiteScheduleStorage, SQLiteAlertStorage, EncryptedTokenStorage
from backend.interfaces import IConfigProvider
from backend.services.system import create_secret_cipher
from backend.services import BackupService, TranslationService, KickAuthManager, TwitchAuthManager, SettingsService, AvatarService, WidgetService, ScheduleService, TTSManager, OverlayServerManager, AlertService, BrowserService
from backend.utils.paths import resource_path

logger = logging.getLogger("minikick.core.app_container")


class AppContainerCore:
    def __init__(self, db_manager: DatabaseManager, i18n: TranslationService, config_provider: IConfigProvider):
        self.db_manager = db_manager
        self.config_provider = config_provider
        self.i18n = i18n
        self._is_shutdown = False
        self._music_provider = None

        if API_KEYS_MISSING:
            logger.warning("[AppContainer] API keys configuration file not found, running with defaults.")

        self._init_storages()
        self._init_services()
        self._init_auth()
        self._init_overlay_and_alerts()
        logger.info("[AppContainer] Core dependency container initialized successfully.")

    @property
    def music_provider(self):
        return self.get_music_provider()

    def get_music_provider(self):
        if self._music_provider is None:
            from backend.providers.music import YouTubeMusicProvider
            self._music_provider = YouTubeMusicProvider(
                self.i18n, music_storage=self.music_storage, db_manager=self.db_manager,
                settings_storage=self.settings_storage,
            )
        return self._music_provider

    def shutdown(self):
        if self._is_shutdown:
            return
        self._is_shutdown = True

        components = (
            (self._music_provider, "shutdown"),
            (self.tts_manager, "shutdown"),
            (self.overlay_server, "stop"),
        )
        for component, method_name in components:
            if component is None:
                continue
            action = getattr(component, method_name, None)
            if not callable(action):
                logger.warning(
                    "[AppContainer] Component %s has no callable %s() method.",
                    type(component).__name__,
                    method_name,
                )
                continue
            try:
                action()
            except Exception:
                logger.exception(
                    "[AppContainer] Failed to stop component %s.",
                    type(component).__name__,
                )

    def _init_storages(self):
        logger.debug("[AppContainer] Initializing SQLite storage layers...")
        db = self.db_manager
        self.secret_cipher = create_secret_cipher()
        self.commands_storage = SQLiteCommandsStorage(db)
        self.kick_token_storage = EncryptedTokenStorage(
            SQLiteTokenStorage(db, provider="kick"), self.secret_cipher
        )
        self.twitch_token_storage = EncryptedTokenStorage(
            SQLiteTokenStorage(db, provider="twitch"), self.secret_cipher
        )
        self.settings_storage = self.config_provider
        self.rewards_storage = SQLiteRewardsStorage(db)
        self.spam_storage = SQLiteSpamStorage(db)
        self.timers_storage = SQLiteTimersStorage(db)
        self.widgets_storage = SQLiteWidgetsStorage(db)
        self.avatar_storage = SQLiteAvatarStorage(db)
        self.system_log_storage = SQLiteSystemLogStorage(db)
        self.music_storage = SQLiteMusicStorage(db)
        self.schedule_storage = SQLiteScheduleStorage(db)
        self.alert_storage = SQLiteAlertStorage(db)

    def _init_services(self):
        logger.debug("[AppContainer] Initializing core services...")
        self.backup_service = BackupService(
            settings_storage=self.settings_storage,
            rewards_storage=self.rewards_storage,
            commands_storage=self.commands_storage,
            spam_storage=self.spam_storage,
            timers_storage=self.timers_storage,
            schedule_storage=self.schedule_storage,
            alert_storage=self.alert_storage,
            widgets_storage=self.widgets_storage,
        )
        self.settings_service = SettingsService(self.settings_storage, self.backup_service)
        self.browser_service = BrowserService(self.settings_storage)
        self.avatar_service = AvatarService(avatar_storage=self.avatar_storage, db_manager=self.db_manager)
        self.widget_service = WidgetService(self.widgets_storage)
        self.schedule_service = ScheduleService(self.schedule_storage)

    def _init_auth(self):
        logger.debug("[AppContainer] Initializing Kick and Twitch OAuth managers...")
        auth_html_path = resource_path(os.path.join("assets", "web", "auth.html"))
        self.kick_auth_manager = KickAuthManager(
            client_id=KICK_CLIENT_ID,
            client_secret=KICK_CLIENT_SECRET,
            redirect_uri=KICK_REDIRECT_URI,
            storage=self.kick_token_storage,
            success_html_path=auth_html_path,
            browser_service=self.browser_service,
        )
        self.twitch_auth_manager = TwitchAuthManager(
            client_id=TWITCH_CLIENT_ID,
            client_secret=TWITCH_CLIENT_SECRET,
            redirect_uri=TWITCH_REDIRECT_URI,
            storage=self.twitch_token_storage,
            success_html_path=auth_html_path,
            browser_service=self.browser_service,
        )

    def _init_overlay_and_alerts(self):
        logger.debug("[AppContainer] Initializing TTS Manager and Overlay Server...")
        self.tts_manager = TTSManager()
        self.overlay_server = OverlayServerManager(settings_storage=self.settings_storage)
        self.overlay_server.start()
        self.alert_service = AlertService(
            storage=self.alert_storage,
            overlay_server=self.overlay_server,
            tts_service=self.tts_manager,
        )
        self.overlay_server.on_alert_finished = self.alert_service.ack_alert