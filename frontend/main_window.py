# frontend\main_window.py

import html
import threading
import time
import logging
from collections import deque
from datetime import datetime
from functools import partial
from typing import Callable, Iterable
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QSystemTrayIcon, QApplication
from PySide6.QtCore import Slot, Signal, QTimer, QThread

from backend.utils.perf import perf_phase
from backend.services import ChatMessageDTO, RewardsService, ChatService, CommandService, AvatarService, LogService, SettingsService, SpamService, TimerService, WhatsNewService
from backend.controllers import RewardsController, ChatController, CommandsController, DashboardController, TimersController, LogsController, MusicController, SettingsController, SpamController, UpdaterController, WidgetsController, ScheduleController, AlertsController
from backend.providers import KickAPIClient, TwitchAPIClient
from backend.workers import KickAuthWorker, TwitchAuthWorker, KickChatWorker, TwitchChatWorker, FetchRewardsWorker, TwitchRewardWorker, TimerWorker, ScheduleWorker, GlobalMediaWorker
from frontend.common import get_global_qss, BrandColors, Size
from frontend.dialogs.update_flow import present_update_dialog
from frontend.navigation import Sidebar, ToastManager, SystemTrayManager
from frontend.views import DashboardView
from frontend.dialogs import ModernConfirmDialog, YouTubeConnectDialog, TikTokConnectDialog
from frontend.main_window_views import MainWindowViewFactory
from frontend.view_prewarmer import ViewPrewarmer
from frontend.recent_redemptions import RecentRedemptionCache
from frontend.window.media_keys import MediaKeysHandler
from frontend.window.session_metrics import SessionMetrics
from frontend.window.shutdown import ShutdownSequence
from frontend.window.updates import AutoUpdateCoordinator
from frontend.window.whats_new import WhatsNewPresenter
from frontend.window.window_state import WindowStateManager
from backend.connections import (
    LiveChatConnection,
    TikTokConnection,
    WorkerShutdownCoordinator,
    WorkerSlot,
    YouTubeConnection,
    is_worker_running,
)

from backend.config import KICK_PUSHER, TWITCH_CLIENT_ID

logger = logging.getLogger("minikick.core")


class MainWindowCore(QMainWindow):
    shutdown_finished = Signal()

    SETTING_AUTOSTART = "dashboard_autostart"
    SETTING_WINDOW_MAXIMIZED = WindowStateManager.SETTING_WINDOW_MAXIMIZED
    SETTING_WINDOW_GEOMETRY = WindowStateManager.SETTING_WINDOW_GEOMETRY

    _NAV_CONFIG = (
        ("Dashboard", "element-filled.svg", "top"),
        ("Chat", "dialog-filled.svg", "top"),
        ("Stream Info", "calendar-days-filled.svg", "top"),
        ("Comandos", "chat-square-code-filled.svg", "top"),
        ("Timers", "alarm-filled.svg", "top"),
        ("Music", "music-notes-filled.svg", "top"),
        ("Widgets", "widget-add-filled.svg", "top"),
        ("Triggers", "treasure-chest-filled.svg", "top"),
        ("Alerts", "megaphone-filled.svg", "top"),

        ("Settings", "gear-filled.svg", "bottom"),
        ("Developer", "file-text-filled.svg", "bottom"),
    )
    _KICK_WORKER_ATTRS = ("kick_chat_worker", "kick_auth_worker", "fetch_rewards_worker", "timers_worker")
    _TWITCH_WORKER_ATTRS = (
        "twitch_chat_worker",
        "twitch_auth_worker",
        "twitch_reward_worker",
        "fetch_twitch_rewards_worker",
    )
    _WORKER_THREAD_NAMES = {
        "kick_chat_worker": "Worker_Kick_Chat_Socket",
        "kick_auth_worker": "Worker_Kick_Auth",
        "fetch_rewards_worker": "Worker_Fetch_Rewards",
        "timers_worker": "Worker_Timers",
        "twitch_chat_worker": "Worker_Twitch_Chat_Socket",
        "twitch_auth_worker": "Worker_Twitch_Auth",
        "twitch_reward_worker": "Worker_Twitch_Reward_EventSub",
        "fetch_twitch_rewards_worker": "Worker_Fetch_Twitch_Rewards",
        "schedule_worker": "Worker_Stream_Schedule",
    }
    _LIVE_CHAT_DIALOGS = {
        "youtube": (YouTubeConnectDialog, "dialogs.unlink_youtube.title", "dialogs.unlink_youtube.desc"),
        "tiktok": (TikTokConnectDialog, "dialogs.unlink_tiktok.title", "dialogs.unlink_tiktok.desc"),
    }
    _LIVE_CHAT_TOASTS = {
        "youtube": (
            "main.toast.youtube_connected_title",
            "main.toast.youtube_connected_msg",
            "main.toast.youtube_disconnected_title",
            "main.toast.youtube_disconnected_msg",
        ),
        "tiktok": (
            "main.toast.tiktok_connected_title",
            "main.toast.tiktok_connected_msg",
            "main.toast.tiktok_disconnected_title",
            "main.toast.tiktok_disconnected_msg",
        ),
    }
    _PREWARM_EXCLUDED_VIEWS = ("Dashboard", "Developer")
    _PREWARM_START_DELAY_MS = 300
    _DB_MAINTENANCE_DELAY_MS = 10_000
    _SLOW_STATUS_REFRESH_MS = 50.0

    def __init__(self, container, q_log_handler, updater_manager, app_version: str):
        super().__init__()
        self.setUpdatesEnabled(False)
        self.resize(1200, 800)

        self.logger = logger
        self.container = container
        self.q_log_handler = q_log_handler
        self.updater_manager = updater_manager
        self.app_version = app_version

        self._init_flags()
        self._init_worker_state()
        self._init_session_state()
        self._bind_container()
        self._init_shutdown_support()
        self._init_live_chat_connections()
        self.setWindowTitle(self.i18n.get("main.window.title").replace("{version}", app_version))

        self.logger.info("[MainWindow] Initializing main window components and UI shell...")
        self.toast = ToastManager(self)
        with perf_phase(self.logger, "Startup", "Main UI shell and controllers initialized"):
            self._setup_ui()
        with perf_phase(self.logger, "Startup", "Tray and startup wiring initialized"):
            self._setup_tray()
            self._init_updater()
            self._connect_signals()
            self._load_settings_into_ui()

        self.setUpdatesEnabled(True)
        self.logger.info("[MainWindow] Main window initialization complete.")

    def _init_flags(self):
        self._is_shutting_down = False
        self._cleanup_complete = False
        self._quit_requested = False
        self._kick_auth_start_pending = False
        self._kick_reauth_pending = False
        self._kick_disconnect_pending = False
        self._twitch_auth_start_pending = False
        self._twitch_disconnect_pending = False
        self._twitch_chat_start_pending = False
        self._twitch_reward_start_pending = False
        self._timer_worker_start_generation = 0

    def _init_worker_state(self):
        self.kick_api_client = None
        self.kick_chat_worker = None
        self.kick_auth_worker = None
        self.fetch_rewards_worker = None
        self.timers_worker = None
        self.schedule_worker = None
        self.twitch_chat_worker = None
        self.twitch_auth_worker = None

    def _init_live_chat_connections(self):
        def build(connection_class):
            return connection_class(
                config=self.settings_storage,
                i18n=self.i18n,
                coordinator=self._worker_shutdown_coordinator,
                is_shutting_down=lambda: self._is_shutting_down,
                parent=self,
            )

        self.youtube = build(YouTubeConnection)
        self.tiktok = build(TikTokConnection)
        self.live_chats = (self.youtube, self.tiktok)

    def _init_session_state(self):
        self.session_metrics = SessionMetrics(
            lambda: self.container.db_manager.get_dashboard_analytics_summary(),
            parent=self,
        )
        self._recent_reward_redemptions = RecentRedemptionCache(maxlen=100)

    def _bind_container(self):
        c = self.container
        self.settings_storage = c.settings_storage
        self.rewards_storage = c.rewards_storage
        self.commands_storage = c.commands_storage
        self.spam_storage = c.spam_storage
        self.timers_storage = c.timers_storage
        self.backup_service = c.backup_service
        self.i18n = c.i18n
        self.kick_auth_manager = c.kick_auth_manager
        self.tts_manager = c.tts_manager
        self.overlay_server = c.overlay_server
        self.window_state = WindowStateManager(self, self.settings_storage, self._notify_background)

    def _init_shutdown_support(self):
        self._retiring_workers: set = set()
        self._worker_shutdown_coordinator = WorkerShutdownCoordinator(
            self,
            self.logger,
            self._retiring_workers,
        )
        self._shutdown_sequence = ShutdownSequence(
            self.logger,
            stop_workers=self._stop_all_workers,
            release_steps=(
                ("clean up music_controller", lambda: self.music_controller.shutdown()),
                ("clean up widgets_controller", lambda: self.widgets_controller.cleanup()),
                ("stop the chat service", lambda: self.chat_service.shutdown()),
                ("clean up the chat controller", lambda: self.chat_controller.cleanup()),
            ),
            close_steps=(
                ("stop application services", lambda: self.container.shutdown()),
                ("flush pending log records", lambda: self.log_service.close()),
                ("close database resources", lambda: self.container.db_manager.cleanup()),
            ),
            on_complete=self._on_shutdown_complete,
        )

    def _init_updater(self):
        self.logger.debug("[MainWindow] Checking background silent updates...")
        self.updater_controller = UpdaterController(self.updater_manager)
        self.auto_updates = AutoUpdateCoordinator(
            parent=self,
            updater_controller=self.updater_controller,
            settings_service=self.settings_service,
            sidebar=self.sidebar,
            toast=self.toast,
            i18n=self.i18n,
            is_shutting_down=lambda: self._is_shutting_down,
            request_quit=self._force_quit,
        )
        self.updater_controller.update_found_silent.connect(self.auto_updates.on_update_found)
        self.updater_controller.download_finished.connect(self.auto_updates.on_download_finished)
        self.updater_controller.error.connect(self.auto_updates.on_download_error)
        self.updater_controller.check_updates_silently()


    def _setup_ui(self):
        self._build_layout_shell()
        self._create_services()
        self._create_views_registry()
        self._create_controllers()
        self._start_background_workers()
        self._assemble_layout()
        QTimer.singleShot(0, self._update_dashboard_metrics)
        self._init_whats_new()
        self.whats_new.init_badges()

    def _build_layout_shell(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(*Size.Margin.MRG_NON)
        self.main_layout.setSpacing(Size.SPACING_NN)

        self.sidebar = Sidebar(self.i18n, app_version=self.app_version, parent=self)
        for name, icon, pos in self._NAV_CONFIG:
            self.sidebar.add_tab(name, icon, position=pos, is_active=(name == "Dashboard"))

        self.content_stack = QStackedWidget(self.central_widget)

    def _create_services(self):
        self.avatar_service = AvatarService(avatar_storage=self.container.avatar_storage)
        self.chat_service = ChatService(self.tts_manager, self.settings_storage)
        self.settings_service = SettingsService(self.settings_storage, self.backup_service)
        self.rewards_service = RewardsService(self.rewards_storage, self.overlay_server)

        self.command_service = CommandService(self.commands_storage, api_client=None)
        self.spam_service = SpamService(self.spam_storage, api_client=None, i18n=self.i18n)
        self.timer_service = TimerService(self.timers_storage, api_client=None)
        self.log_service = LogService(log_storage=self.container.system_log_storage)
        self.schedule_service = self.container.schedule_service

    def _create_views_registry(self):
        self.view_dashboard = DashboardView(self.i18n, browser_service=self.container.browser_service, parent=self)
        self.view_schedule = None
        self.view_chat = None
        self.view_music = None
        self.view_rewards = None
        self.view_commands = None
        self.view_widgets = None
        self.view_spam = None
        self.view_timers = None
        self.view_settings = None
        self.view_logs = None
        self.view_alerts = None

        self._instantiated_views = {"Dashboard": self.view_dashboard}
        self._last_navigation_at: float | None = None
        self._view_prewarmer = ViewPrewarmer(
            create_view=self._get_or_create_view,
            view_names=[name for name, _icon, _area in self._NAV_CONFIG if name not in self._PREWARM_EXCLUDED_VIEWS],
            is_created=lambda name: name in self._instantiated_views,
            is_active=lambda: not self._is_shutting_down,
            seconds_since_navigation=self._seconds_since_navigation,
            schedule=QTimer.singleShot,
        )
        self._view_factory = MainWindowViewFactory(self)

    def _create_controllers(self):
        self.dashboard_controller = DashboardController(
            view=self.view_dashboard,
            avatar_service=self.avatar_service,
            db_manager=self.container.db_manager,
            widget_service=self.container.widget_service,
            toast_manager=self.toast,
            i18n=self.i18n
        )
        self.chat_controller = ChatController(
            view=None,
            service=self.chat_service,
            command_service=self.command_service,
            spam_service=self.spam_service,
            i18n=self.i18n,
            timer_service=self.timer_service,
            toast_manager=self.toast
        )
        self.widgets_controller = WidgetsController(
            view=None,
            widget_service=self.container.widget_service,
            command_service=self.command_service,
            overlay_server=self.overlay_server,
            i18n=self.i18n,
            toast_manager=self.toast,
            ignored_users_provider=self.chat_service.get_ignored_users
        )
        self.dashboard_controller.widgets_controller = self.widgets_controller
        self.music_controller = MusicController(
            view=None,
            command_service=self.command_service,
            toast_manager=self.toast,
            i18n=self.i18n,
            settings_storage=self.container.settings_storage,
            music_storage=self.container.music_storage,
            music_provider=self.container.music_provider
        )
        self.media_keys = MediaKeysHandler(
            self.music_controller,
            config=self.settings_storage,
            slot=WorkerSlot("Worker_Global_Media_Keys", self._worker_shutdown_coordinator),
            worker_factory=GlobalMediaWorker,
            is_shutting_down=lambda: self._is_shutting_down,
        )
        if hasattr(self.chat_service, "set_speech_callbacks"):
            self.chat_service.set_speech_callbacks(
                on_started=lambda: self.music_controller.set_ducking(True),
                on_finished=lambda: self.music_controller.set_ducking(False)
            )
        self.rewards_controller = RewardsController(
            view=None,
            service=self.rewards_service,
            toast_manager=self.toast,
            kick_auth_manager=self.kick_auth_manager,
            twitch_auth_manager=self.container.twitch_auth_manager
        )
        self.commands_controller = CommandsController(
            None,
            self.command_service,
            toast_manager=self.toast,
            connected_platforms_provider=self.get_connected_platforms
        )
        self.spam_controller = SpamController(
            None,
            self.spam_service,
            toast_manager=self.toast,
            connected_platforms_provider=self.get_connected_platforms
        )
        self.timers_controller = TimersController(
            None,
            self.timer_service,
            toast_manager=self.toast,
            schedule_service=self.schedule_service,
            connected_platforms_provider=self.get_connected_platforms
        )
        self.settings_controller = SettingsController(
            view=None,
            service=self.settings_service,
            toast_manager=self.toast,
            music_provider=self.container.music_provider,
            tts_manager=self.tts_manager,
            browser_service=self.container.browser_service
        )
        self.logs_controller = LogsController(
            view=None,
            service=self.log_service,
            toast_manager=self.toast
        )
        self.schedule_controller = ScheduleController(
            view=None,
            service=self.schedule_service,
            toast_manager=self.toast,
            i18n=self.i18n,
            connected_platforms_provider=self.get_connected_platforms
        )
        self.alerts_controller = AlertsController(
            view=None,
            service=self.container.alert_service,
            toast_manager=self.toast,
            i18n=self.i18n,
            browser_service=self.container.browser_service
        )

    def _start_background_workers(self):
        self._start_schedule_worker()
        self.media_keys.setup_global_keys()

    def _assemble_layout(self):
        self.content_stack.addWidget(self.view_dashboard)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

    def _setup_tray(self):
        self.tray_manager = SystemTrayManager(self.i18n, self)
        self.tray_manager.restore_requested.connect(self.window_state.restore_from_tray)
        self.tray_manager.quit_requested.connect(self._force_quit)
        self.tray_manager.tts_toggled.connect(self._handle_tray_tts_toggle)
        self.tray_manager.play_pause_requested.connect(self._handle_tray_play_pause)
        self.tray_manager.skip_requested.connect(self._handle_tray_skip)
        self.tray_manager.tts_use_command_toggled.connect(self._handle_tray_tts_use_command_toggle)
        self.tray_manager.tts_voice_type_changed.connect(self._handle_tray_tts_voice_type_change)
        self.tray_manager.show()

    def _connect_signals(self):
        self.settings_controller.style_reload_requested.connect(self._apply_dynamic_theme)
        self.sidebar.view_selected.connect(self._handle_navigation)
        self.sidebar.section_viewed.connect(self.whats_new.on_section_viewed)
        self.dashboard_controller.request_connection.connect(self._handle_auth_process)
        self.dashboard_controller.twitch_connect_requested.connect(self._on_twitch_integration_button_clicked)
        self.dashboard_controller.youtube_connect_requested.connect(partial(self._on_live_chat_button_clicked, self.youtube))
        self.dashboard_controller.tiktok_connect_requested.connect(partial(self._on_live_chat_button_clicked, self.tiktok))
        self._wire_live_chat(self.youtube)
        self._wire_live_chat(self.tiktok)
        self.dashboard_controller.reauth_requested.connect(self._force_reauth)
        self.dashboard_controller.reauth_kick_requested.connect(self._handle_reauth_kick)
        self.dashboard_controller.reauth_twitch_requested.connect(self._handle_reauth_twitch)
        self.chat_controller.tts_state_changed.connect(self._handle_chat_tts_state_changed)
        self.chat_controller.message_received.connect(self.overlay_server.trigger_chat_message)
        self.chat_controller.chat_overlay_config_changed.connect(self.overlay_server.trigger_chat_config_update)
        self.chat_controller.tts_ignored_users_changed.connect(self.widgets_controller.invalidate_ignored_bots_cache)
        self.chat_controller.message_received.connect(self.widgets_controller.handle_chat_message)
        self.music_controller.song_changed.connect(self.overlay_server.trigger_music_change)
        self.music_controller.song_changed.connect(self._handle_tray_song_changed)
        self.chat_controller.music_plugin_triggered.connect(self.music_controller.handle_music_plugin_command)
        self.chat_controller.widget_plugin_triggered.connect(self.widgets_controller.handle_widget_command)
        self.chat_controller.spam_blocked.connect(self.session_metrics.record_spam_blocked)
        self.session_metrics.refresh_requested.connect(self._refresh_dashboard_view)
        self.session_metrics.analytics_loaded.connect(self.dashboard_controller.update_analytics_summary)
        self.chat_controller.command_executed.connect(lambda *args: self._update_dashboard_metrics(force_db_query=True))
        self.settings_controller.unlink_account_requested.connect(self._handle_unlink_account)
        self.settings_controller.check_update_requested.connect(self.handle_update_check)
        self.sidebar.update_requested.connect(self.handle_update_check)
        self.settings_controller.notification_requested.connect(lambda title, msg: self.tray_manager.showMessage(title, msg))
        self.settings_controller.backup_restored.connect(self._on_backup_restored)
        self.q_log_handler.emitter.log_received.connect(self.logs_controller.process_incoming_log)
        self.avatar_service.avatar_downloaded.connect(self.sidebar.update_profile_avatar)

    def _load_settings_into_ui(self, *, refresh_chat_backend: bool = False):
        self.logger.debug("[AutoStart] Loading controller initial state (Rewards, Widgets, Chat, Spam, Timers, Music)...")
        self._startup_hydration_steps = deque((
            ("rewards", self.rewards_controller.load_initial_data),
            ("widgets", self.widgets_controller.load_initial_data),
            ("chat settings", self._load_chat_settings),
            ("command cache", self.command_service.reload_cache),
            ("spam, timers, and music", self._load_remaining_controller_data),
            ("chat and overlay settings", lambda: self._load_chat_controller_data(refresh_backend=refresh_chat_backend)),
            ("integrations and profile", self._finish_settings_hydration),
        ))
        QTimer.singleShot(50, self._run_next_startup_hydration_step)

    def _on_backup_restored(self):
        self._load_settings_into_ui(refresh_chat_backend=True)

    def _run_next_startup_hydration_step(self):
        import time

        if self._is_shutting_down or not self._startup_hydration_steps:
            return

        step_name, step = self._startup_hydration_steps.popleft()
        step_started = time.perf_counter()
        try:
            step()
        except Exception:
            self.logger.exception(
                "[Startup] Hydration phase '%s' failed.",
                step_name,
            )
        else:
            self.logger.info(
                "[Perf/Startup] Hydration phase '%s' completed in %.2f ms",
                step_name,
                (time.perf_counter() - step_started) * 1000
            )
        if self._startup_hydration_steps:
            QTimer.singleShot(16, self._run_next_startup_hydration_step)
        else:
            self._schedule_startup_followups()

    def _load_chat_settings(self):
        settings = self.chat_service.get_settings()
        self.tray_manager.set_tts_state(settings.get("enabled", True))
        self.tray_manager.set_tts_use_command_state(settings.get("use_command", False))
        self.tray_manager.set_tts_voice_type_state(settings.get("provider", "piper") == "web")

    def _load_remaining_controller_data(self):
        self.spam_controller.load_initial_data()
        self.timers_controller.load_initial_data()
        self.music_controller.load_initial_data()

    def _load_chat_controller_data(self, *, refresh_backend: bool = False):
        self.chat_controller.load_initial_data(refresh_backend=refresh_backend)
        if hasattr(self, "overlay_server") and self.overlay_server:
            self.overlay_server.trigger_chat_config_update(self.chat_controller.get_active_overlay_config())

    def _finish_settings_hydration(self):
        self._apply_dynamic_theme(self.settings_service.get_font_size())
        self._update_integrations_status_ui()
        self._refresh_sidebar_profile()
        self._evaluate_all_scopes()
        self._autostart_authenticated_platforms()
        self._schedule_live_chat_autostarts()

    def _autostart_authenticated_platforms(self) -> None:
        if self.kick_auth_manager.is_authenticated():
            try:
                self.logger.info("[AutoStart] Starting Kick integration...")
                self._handle_auth_process()
            except Exception as e:
                self.logger.error("[AutoStart] Error auto-starting Kick integration: %s", e)

        twitch_tokens = self.container.twitch_token_storage.load()
        if twitch_tokens and twitch_tokens.get("access_token"):
            QTimer.singleShot(1200, lambda: self._autostart_twitch(twitch_tokens))

    def _schedule_live_chat_autostarts(self) -> None:
        for chat, delay_ms in ((self.youtube, 2400), (self.tiktok, 3600)):
            target = chat.saved_target()
            if target:
                QTimer.singleShot(delay_ms, lambda c=chat, t=target: self._autostart_live_chat(c, t))

    def _autostart_twitch(self, twitch_tokens: dict):
        if self._is_shutting_down:
            return
        try:
            self.logger.info("[AutoStart] Starting Twitch integration...")
            self._on_twitch_auth_success(twitch_tokens)
        except Exception as e:
            self.logger.error("[AutoStart] Error auto-starting Twitch integration: %s", e)

    def _autostart_live_chat(self, chat: LiveChatConnection, target: str):
        if self._is_shutting_down:
            return
        if chat.is_offline_saved():
            self.logger.info(
                "[AutoStart] Skipping %s integration because the saved stream is offline; connect manually to retry.",
                chat.log_tag,
            )
            return
        try:
            self.logger.info("[AutoStart] Starting %s integration (target='%s')...", chat.log_tag, target)
            chat.connect_channel(target, manual=False)
        except Exception as e:
            self.logger.error("[AutoStart] Error auto-starting %s integration: %s", chat.log_tag, e)

    def _handle_navigation(self, view_name: str):
        navigation_started = time.perf_counter()
        self._last_navigation_at = navigation_started
        self.logger.info("[User Action] Navigated to view: '%s'", view_name)
        target_view = self._get_or_create_view(view_name)
        if target_view:
            switch_started = time.perf_counter()
            self.content_stack.setCurrentWidget(target_view)
            hooks_started = time.perf_counter()
            if view_name == "Dashboard":
                self._update_dashboard_metrics(force_db_query=True)
            elif view_name == "Settings":
                self._update_integrations_status_ui()
            elif view_name == "Triggers":
                self._fetch_api_rewards()
            finished = time.perf_counter()
            self.logger.info(
                "[Perf/Navigation] Navigation to '%s' completed in %.2f ms (create=%.2f, switch=%.2f, hooks=%.2f)",
                view_name,
                (finished - navigation_started) * 1000,
                (switch_started - navigation_started) * 1000,
                (hooks_started - switch_started) * 1000,
                (finished - hooks_started) * 1000,
            )

    def _get_or_create_view(self, view_name: str):
        return self._view_factory.get_or_create(view_name)

    def _schedule_startup_followups(self) -> None:
        QTimer.singleShot(750, self.whats_new.check_dialog)
        self._view_prewarmer.start(self._PREWARM_START_DELAY_MS)
        QTimer.singleShot(self._DB_MAINTENANCE_DELAY_MS, self._start_database_maintenance)

    def _start_database_maintenance(self) -> None:
        if self._is_shutting_down:
            return
        threading.Thread(
            target=self.container.db_maintenance.run, name="DatabaseMaintenance", daemon=True
        ).start()

    def _seconds_since_navigation(self) -> float:
        if self._last_navigation_at is None:
            return float("inf")
        return time.perf_counter() - self._last_navigation_at

    def _init_whats_new(self):
        self.whats_new = WhatsNewPresenter(
            parent=self,
            service=WhatsNewService(self.settings_storage, self.app_version),
            sidebar=self.sidebar,
            i18n=self.i18n,
            app_version=self.app_version,
            slot=WorkerSlot("Worker_Whats_New", self._worker_shutdown_coordinator),
            is_shutting_down=lambda: self._is_shutting_down,
        )

    def restore_window_state(self):
        self.window_state.restore()

    def changeEvent(self, event):
        self.window_state.handle_state_change(event)
        super().changeEvent(event)

    def closeEvent(self, event):
        if self._is_shutting_down:
            event.accept()
            return

        minimize_tray = self.window_state.minimize_to_tray_enabled()
        self.logger.info("[User Action] Window close triggered (minimize_tray=%s)", minimize_tray)
        if minimize_tray:
            self.window_state.save()
            self.hide()
            self._notify_background()
            event.ignore()
        else:
            dialog = ModernConfirmDialog(
                self.i18n,
                parent=None,
                title_text=self.i18n.get("dialogs.close.title"),
                body_text=self.i18n.get("dialogs.close.desc")
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                self.logger.info("[User Action] App exit confirmed by user")
                self.hide()
                event.ignore()
                self._force_quit()
            else:
                self.logger.info("[User Action] App exit cancelled by user")
                event.ignore()

    def nativeEvent(self, event_type, message):
        if self.media_keys.handle_native_event(event_type, message):
            return True, 1
        return super().nativeEvent(event_type, message)

    def keyPressEvent(self, event):
        if self.media_keys.handle_key(event.key()):
            event.accept()
            return
        super().keyPressEvent(event)

    def _safe_stop_worker(
        self,
        worker_attr_name: str,
        timeout_ms: int = 1500,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        worker = getattr(self, worker_attr_name, None)
        if not worker:
            self._worker_shutdown_coordinator.stop_workers(
                (),
                on_finished=on_finished,
                warning_after_seconds=max(timeout_ms, 0) / 1000,
            )
            return

        setattr(self, worker_attr_name, None)
        self._worker_shutdown_coordinator.stop_workers(
            [(worker_attr_name, worker)],
            on_finished=on_finished,
            warning_after_seconds=max(timeout_ms, 0) / 1000,
        )

    def _notify_background(self):
        self.tray_manager.showMessage(
            self.i18n.get("main.tray.bg_title"),
            self.i18n.get("main.tray.bg_desc"),
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def _force_quit(self):
        self.window_state.save()
        self.hide()
        self._quit_requested = True
        self._cleanup()

    def _cleanup(self):
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        self.session_metrics.stop()
        if self.view_chat is not None:
            self.view_chat.close_floating_chat()
        self._shutdown_sequence.run()

    def _on_shutdown_complete(self) -> None:
        self._cleanup_complete = True
        self.shutdown_finished.emit()
        if self._quit_requested:
            QTimer.singleShot(0, QApplication.quit)

    def _stop_workers_parallel(
        self,
        worker_map: list[tuple[str, QThread | None]],
        on_finished: Callable[[], None] | None = None,
        *,
        warning_after_ms: int = 10_000,
    ) -> None:
        self._worker_shutdown_coordinator.stop_workers(
            worker_map,
            on_finished=on_finished,
            warning_after_seconds=max(warning_after_ms, 0) / 1000,
        )

    def _detach_workers(self, attrs: Iterable[str]) -> list[tuple[str, QThread | None]]:
        workers = [(self._WORKER_THREAD_NAMES[attr], getattr(self, attr, None)) for attr in attrs]
        for attr in attrs:
            setattr(self, attr, None)
        return workers

    def _stop_workers_by_attr(
        self,
        attrs: tuple[str, ...],
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        self._stop_workers_parallel(self._detach_workers(attrs), on_finished=on_finished)

    def _stop_kick_connection_workers(
        self,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        self._timer_worker_start_generation += 1
        self._stop_workers_by_attr(self._KICK_WORKER_ATTRS, on_finished)

    def _stop_twitch_connection_workers(
        self,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        self._stop_workers_by_attr(self._TWITCH_WORKER_ATTRS, on_finished)

    def _stop_all_workers(
        self,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        workers = self._detach_workers(tuple(self._WORKER_THREAD_NAMES))
        slots = (self.media_keys.slot, self.whats_new.slot, *(chat.slot for chat in self.live_chats))
        workers.extend(slot.detach() for slot in slots)
        self._stop_workers_parallel(workers, on_finished=on_finished)

    _is_worker_running = staticmethod(is_worker_running)

    @Slot()
    def _handle_auth_process(self, force: bool = False):
        if self._is_worker_running(getattr(self, "twitch_auth_worker", None)):
            self.toast.show_toast(
                title=self.container.i18n.get("main.toast.auth_in_progress_title"),
                message=self.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning"
            )
            return

        if (
            self._kick_auth_start_pending
            or self._kick_disconnect_pending
            or self._is_shutting_down
        ):
            return
        self._kick_auth_start_pending = True
        self._stop_kick_connection_workers(
            on_finished=lambda: self._start_kick_auth_worker(force)
        )

    def _start_kick_auth_worker(self, force: bool) -> None:
        self._kick_auth_start_pending = False
        if self._is_shutting_down:
            return

        self.dashboard_controller.handle_connecting_state()

        self.kick_auth_worker = KickAuthWorker(self.i18n, self.kick_auth_manager, force=force)
        self.kick_auth_worker.auth_success.connect(self._on_auth_success)
        self.kick_auth_worker.auth_error.connect(self.dashboard_controller.handle_error_state)
        self.kick_auth_worker.finished.connect(lambda: setattr(self, 'kick_auth_worker', None))
        self.kick_auth_worker.finished.connect(self.kick_auth_worker.deleteLater)
        self.kick_auth_worker.start()

    def _on_auth_success(self, _tokens):
        self.kick_api_client = KickAPIClient(auth_provider=self.kick_auth_manager)
        self._evaluate_all_scopes()

        self.command_service.api_client = self.kick_api_client
        self.spam_service.api_client = self.kick_api_client
        self.timer_service.api_client = self.kick_api_client

        self.command_service.reload_cache()
        self.spam_service.reload_filters()

        self.schedule_service.set_kick_client(self.kick_api_client)
        self._start_schedule_worker()
        if hasattr(self, "schedule_controller") and self.schedule_controller:
            self.schedule_controller.fetch_current_info()

        self.kick_chat_worker = KickChatWorker(self.i18n, self.kick_api_client, KICK_PUSHER.cluster, KICK_PUSHER.keys)
        self.kick_chat_worker.connection_success.connect(self._on_web_socket_connected)
        self.kick_chat_worker.message_received.connect(self._route_incoming_message)
        self.kick_chat_worker.poll_updated.connect(self._on_poll_updated)
        self.kick_chat_worker.poll_deleted.connect(self._on_poll_deleted)
        self.kick_chat_worker.pinned_created.connect(self._on_pinned_created)
        self.kick_chat_worker.pinned_deleted.connect(self._on_pinned_deleted)
        self.kick_chat_worker.reward_redeemed.connect(lambda u, r, m: self._on_reward_redeemed(u, r, m, platform="kick"))
        self.kick_chat_worker.error_occurred.connect(self.dashboard_controller.handle_error_state)

        self.kick_chat_worker.start()
        self.kick_auth_worker = None

    def _on_web_socket_connected(self, user_data):
        self.spam_service.broadcaster_id = user_data.get("broadcaster_id", 0)
        self.dashboard_controller.handle_connection_success(user_data)

        username = user_data.get("username", "Kick")
        self._kick_connected = True
        self._kick_username = username
        self._kick_avatar_url = user_data.get("avatar_url") or user_data.get("profile_pic", "")
        self._update_integrations_status_ui()
        self._refresh_sidebar_profile()

        title = self.i18n.get("main.toast.kick_connected_title")
        msg = self.i18n.get("main.toast.kick_connected_msg").replace("{username}", username)
        self.toast.show_toast(
            title=title,
            message=msg,
            state="success"
        )

        slug = username.replace("_", "-").replace(" ", "")
        self._start_timers_worker(slug)
        self._fetch_api_rewards()

    @Slot()
    def _fetch_api_rewards(self):
        if self.kick_auth_manager.is_authenticated():
            if not self._is_worker_running(getattr(self, 'fetch_rewards_worker', None)):
                try:
                    api_client = KickAPIClient(auth_provider=self.kick_auth_manager)
                    self.fetch_rewards_worker = FetchRewardsWorker(api_client, platform="kick")
                    self.fetch_rewards_worker.rewards_fetched.connect(self.rewards_controller.update_rewards_list)
                    self.fetch_rewards_worker.error_occurred.connect(self._handle_rewards_error)
                    self.fetch_rewards_worker.finished.connect(lambda: setattr(self, 'fetch_rewards_worker', None))
                    self.fetch_rewards_worker.finished.connect(self.fetch_rewards_worker.deleteLater)
                    self.fetch_rewards_worker.start()
                except Exception as error:
                    err_template = self.i18n.get("main.logs.api_error_setup")
                    self.logger.exception(
                        err_template.replace("{error}", str(error))
                    )
        else:
            self.logger.debug("Kick auth not active, skipping Kick rewards fetch")

        if self.container.twitch_auth_manager.is_authenticated():
            self._fetch_twitch_rewards()

    @Slot(str)
    def _handle_rewards_error(self, error_msg: str):
        err_template = self.i18n.get("main.logs.api_error")
        self.logger.error(err_template.replace("{error}", error_msg))

    def _format_reward_message(self, reward_name: str) -> str:
        safe_reward_name = html.escape(reward_name)
        canje_template = self.i18n.get("main.chat.reward_redeemed")
        texto_canje = canje_template.replace("{reward_name}", safe_reward_name)
        return f'<span style="color: {BrandColors.GREEN};">{texto_canje}</span>'

    def _on_reward_redeemed(self, user: str, reward_name: str, message: str, platform: str = "kick"):
        recents = getattr(self, "_recent_reward_redemptions", None)
        if recents is not None:
            dedup_key = f"{platform}:{user.lower()}:{reward_name.lower()}:{int(time.time() / 8)}"
            if recents.contains_or_add(dedup_key):
                self.logger.debug("[Reward] Ignoring duplicate redemption: %s", dedup_key)
                return

        self.logger.info("[Reward] Redemption processed: user='%s', reward='%s' (Platform: %s)", user, reward_name, platform.capitalize())
        toast_template = self.i18n.get("main.toasts.reward_msg")
        self.toast.show_toast(
            title=self.i18n.get("main.toasts.reward_title"),
            message=toast_template.replace("{user}", user).replace("{reward_name}", reward_name),
            state="success"
        )

        current_time = datetime.now().strftime("%H:%M")

        msg_sistema = self._format_reward_message(reward_name)
        tag = self.i18n.get("main.chat.points_tag")
        if self.view_chat is not None:
            self.view_chat.append_message(f"[{tag}] {user}", msg_sistema, BrandColors.GREEN, timestamp=current_time, is_html=True, platform=platform)

        config = self.rewards_service.get_reward_config(reward_name, platform=platform)
        if config:
            if self.rewards_service.is_file_valid(config):
                self.rewards_service.trigger_preview(reward_name, config)
                self.rewards_service.log_redemption(reward_name, user, platform=platform)
            else:
                filepath = config.get("filepath", "") if isinstance(config, dict) else (config if isinstance(config, str) else "")
                missing_log = self.i18n.get("main.logs.reward_file_missing").replace("{reward_name}", reward_name).replace("{filepath}", str(filepath))
                self.logger.warning(missing_log)
                if self.toast:
                    self.toast.show_toast(
                        title=self.i18n.get("common.status.warning"),
                        message=self.i18n.get("rewards.status.redeem_file_missing").replace("{reward}", reward_name),
                        state="danger"
                    )
        else:
            no_rewards_template = self.i18n.get("main.logs.reward_no_rewards")
            self.logger.debug("[Reward] %s", no_rewards_template.replace("{reward_name}", reward_name))

        settings = self.chat_service.get_settings()
        if settings.get("enabled", False) and message:
            dto = ChatMessageDTO(user, message, [], "", "", 0, timestamp=current_time, platform=platform)
            self.chat_controller.process_message(dto)

    def _handle_incoming_alert(self, alert_event):
        if hasattr(self.container, "alert_service") and self.container.alert_service:
            self.container.alert_service.process_event(alert_event)

    def _start_timers_worker(self, channel_slug: str):
        if self._kick_disconnect_pending or self._kick_reauth_pending:
            return
        self._timer_worker_start_generation += 1
        generation = self._timer_worker_start_generation
        self._safe_stop_worker(
            "timers_worker",
            on_finished=lambda: self._create_timers_worker(
                channel_slug,
                generation,
            ),
        )

    def _create_timers_worker(self, channel_slug: str, generation: int) -> None:
        if generation != self._timer_worker_start_generation:
            return
        if self._is_shutting_down:
            return
        api_client = KickAPIClient(auth_provider=self.kick_auth_manager)
        self.timers_worker = TimerWorker(self.timer_service, api_client, channel_slug)
        self.timers_worker.post_message_requested.connect(self._send_timer_message)
        self.timers_worker.start()

    @Slot(str, bool, bool)
    def _send_timer_message(self, message: str, apply_kick: bool = True, apply_twitch: bool = True):
        if not message:
            return
        if hasattr(self, "command_service") and self.command_service:
            self.command_service.post_chat_message(message, apply_kick=apply_kick, apply_twitch=apply_twitch)
        elif apply_kick and hasattr(self, "kick_chat_worker") and self.kick_chat_worker:
            self.kick_chat_worker.send_message(message)

    @Slot()
    def _handle_twitch_auth_process(self, force: bool = False):
        if self._is_worker_running(getattr(self, "kick_auth_worker", None)):
            self.toast.show_toast(
                title=self.container.i18n.get("main.toast.auth_in_progress_title"),
                message=self.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning"
            )
            return

        if self._is_worker_running(getattr(self, "twitch_auth_worker", None)):
            self.toast.show_toast(
                title=self.container.i18n.get("main.toast.auth_in_progress_title"),
                message=self.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning",
            )
            return

        if (
            self._twitch_auth_start_pending
            or self._twitch_disconnect_pending
            or self._is_shutting_down
        ):
            return
        self._twitch_auth_start_pending = True
        self._stop_twitch_connection_workers(
            on_finished=lambda: self._start_twitch_auth_worker(force)
        )

    def _start_twitch_auth_worker(self, force: bool) -> None:
        self._twitch_auth_start_pending = False
        if self._is_shutting_down:
            return

        if not force and self.container.twitch_auth_manager.has_missing_scopes():
            force = True
        needs_browser = force or not self.container.twitch_auth_manager.is_authenticated()
        if needs_browser:
            title = self.container.i18n.get("main.toast.twitch_auth_title")
            msg = self.container.i18n.get("main.toast.twitch_auth_opening")
            self.toast.show_toast(
                title=title,
                message=msg,
                state="info"
            )
        self.twitch_auth_worker = TwitchAuthWorker(self.container.twitch_auth_manager, force=force)
        self.twitch_auth_worker.auth_success.connect(self._on_twitch_auth_success)
        self.twitch_auth_worker.auth_error.connect(self._on_twitch_auth_error)
        self.twitch_auth_worker.finished.connect(lambda: setattr(self, 'twitch_auth_worker', None))
        self.twitch_auth_worker.finished.connect(self.twitch_auth_worker.deleteLater)
        self.twitch_auth_worker.start()

    def _on_twitch_auth_error(self, err: str):
        self.twitch_auth_worker = None
        self._twitch_connected = False
        self._twitch_channel = ""
        self._update_integrations_status_ui()
        logger.error("[TwitchAuth] Authentication error: %s", err)
        if self._is_shutting_down:
            return
        err_title = self.container.i18n.get("main.toast.twitch_auth_error_title")
        self.toast.show_toast(title=err_title, message=str(err), state="danger")

    def _on_twitch_auth_success(self, _tokens):
        self.twitch_auth_worker = None
        logger.info("[Twitch Auth] Success callback received.")
        try:
            twitch_api = TwitchAPIClient(auth_provider=self.container.twitch_auth_manager, client_id=TWITCH_CLIENT_ID, i18n=self.container.i18n)
            self.spam_service.twitch_api = twitch_api
            self._start_twitch_chat_worker(channel="")
            self._evaluate_all_scopes()
        except Exception as error:
            self.logger.exception("[Twitch Auth] Error initializing Twitch session.")
            self._twitch_connected = False
            self._twitch_channel = ""
            self._update_integrations_status_ui()
            if hasattr(self, "toast") and self.toast and not self._is_shutting_down:
                err_title = self.container.i18n.get("main.toast.twitch_auth_error_title")
                self.toast.show_toast(
                    title=err_title,
                    message=str(error),
                    state="danger",
                )

    def _start_twitch_chat_worker(self, channel: str):
        if self._twitch_chat_start_pending or self._is_shutting_down:
            return
        self._twitch_chat_start_pending = True
        self._safe_stop_worker(
            "twitch_chat_worker",
            on_finished=lambda: self._create_twitch_chat_worker(channel),
        )

    def _create_twitch_chat_worker(self, channel: str) -> None:
        self._twitch_chat_start_pending = False
        if self._is_shutting_down:
            return
        self.twitch_chat_worker = TwitchChatWorker(
            channel_name=channel,
            oauth_token="",
            bot_nick="",
            api_client=self.spam_service.twitch_api,
            i18n=self.container.i18n
        )

        self.command_service.twitch_worker = self.twitch_chat_worker
        self.spam_service.twitch_worker = self.twitch_chat_worker
        self.twitch_chat_worker.connection_success.connect(self._on_twitch_connected)
        self.twitch_chat_worker.connection_lost.connect(self._on_twitch_socket_lost)
        self.twitch_chat_worker.connection_restored.connect(self._on_twitch_socket_restored)
        self.twitch_chat_worker.error_occurred.connect(self._on_twitch_error)
        self.twitch_chat_worker.message_received.connect(self._route_incoming_message)
        self.twitch_chat_worker.start()

    def _on_twitch_error(self, error_msg: str):
        self._twitch_connected = False
        self._safe_stop_worker("twitch_chat_worker")
        self.command_service.twitch_worker = None
        self.spam_service.twitch_worker = None
        self._update_integrations_status_ui()
        if hasattr(self, "toast") and self.toast and not self._is_shutting_down:
            self.toast.show_toast(
                title=self.container.i18n.get("common.status.error"),
                message=error_msg,
                state="danger"
            )

    def _on_twitch_connected(self, user_data=None):
        if isinstance(user_data, dict):
            username = user_data.get("username", "")
            broadcaster_id = user_data.get("broadcaster_id", "")
            self._twitch_avatar_url = user_data.get("avatar_url", "")
        elif isinstance(user_data, str):
            username = user_data
            broadcaster_id = getattr(self.spam_service, "twitch_broadcaster_id", "")
        else:
            username = getattr(self, "_twitch_channel", "")
            broadcaster_id = getattr(self.spam_service, "twitch_broadcaster_id", "")

        if broadcaster_id:
            self.spam_service.twitch_broadcaster_id = broadcaster_id
        self._twitch_connected = True
        if username:
            self._twitch_channel = username
        self._update_integrations_status_ui()
        self._refresh_sidebar_profile()

        self.schedule_service.set_twitch_client(self.spam_service.twitch_api, broadcaster_id)
        if hasattr(self, "schedule_controller") and self.schedule_controller:
            self.schedule_controller.fetch_current_info()

        if hasattr(self, "rewards_controller") and self.rewards_controller:
            self.rewards_controller.set_twitch_context(
                self.container.twitch_auth_manager,
                self.spam_service.twitch_api,
                broadcaster_id
            )

        if broadcaster_id and self.container.twitch_auth_manager.is_authenticated():
            self._start_twitch_reward_worker(broadcaster_id)
            self._fetch_twitch_rewards(broadcaster_id)
        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            if isinstance(user_data, dict) and user_data:
                self.dashboard_controller.set_channel_profile("twitch", user_data)

        self._evaluate_all_scopes()

        title = self.container.i18n.get("main.toast.twitch_connected_title")
        msg = self.container.i18n.get("main.toast.twitch_connected_msg").replace("{username}", username)
        self.toast.show_toast(
            title=title,
            message=msg,
            state="success"
        )

    def _start_twitch_reward_worker(self, broadcaster_id: str) -> None:
        if self._twitch_reward_start_pending or self._is_shutting_down:
            return
        self._twitch_reward_start_pending = True
        self._safe_stop_worker(
            "twitch_reward_worker",
            on_finished=lambda: self._create_twitch_reward_worker(broadcaster_id),
        )

    def _create_twitch_reward_worker(self, broadcaster_id: str) -> None:
        self._twitch_reward_start_pending = False
        if self._is_shutting_down:
            return
        self.twitch_reward_worker = TwitchRewardWorker(
            self.container.i18n,
            self.container.twitch_auth_manager,
            TWITCH_CLIENT_ID,
            broadcaster_id
        )
        self.twitch_reward_worker.reward_redeemed.connect(
            lambda user, reward, message: self._on_reward_redeemed(
                user, reward, message, platform="twitch"
            )
        )
        self.twitch_reward_worker.alert_received.connect(self._handle_incoming_alert)
        self.twitch_reward_worker.start()

    @Slot()
    def _fetch_twitch_rewards(self, broadcaster_id: str = ""):
        b_id = broadcaster_id or getattr(self.spam_service, "twitch_broadcaster_id", "")
        if not self.container.twitch_auth_manager.is_authenticated():
            return

        if self._is_worker_running(getattr(self, 'fetch_twitch_rewards_worker', None)):
            return

        try:
            twitch_api = self.spam_service.twitch_api or TwitchAPIClient(self.container.twitch_auth_manager, TWITCH_CLIENT_ID, i18n=self.container.i18n)
            self.fetch_twitch_rewards_worker = FetchRewardsWorker(twitch_api, broadcaster_id=b_id, platform="twitch")
            self.fetch_twitch_rewards_worker.rewards_fetched.connect(self.rewards_controller.update_rewards_list)
            self.fetch_twitch_rewards_worker.finished.connect(lambda: setattr(self, 'fetch_twitch_rewards_worker', None))
            self.fetch_twitch_rewards_worker.finished.connect(self.fetch_twitch_rewards_worker.deleteLater)
            self.fetch_twitch_rewards_worker.start()
        except Exception:
            self.logger.exception("[Main] Error launching Twitch rewards fetcher.")

    def _on_twitch_socket_lost(self):
        self._twitch_connected = False
        self.logger.warning("[Twitch] Connection lost for channel '%s'.", getattr(self, '_twitch_channel', '?'))
        self._update_integrations_status_ui()

    def _on_twitch_socket_restored(self):
        self._twitch_connected = True
        self.logger.info("[Twitch] Connection restored for channel '%s'.", getattr(self, '_twitch_channel', '?'))
        self._update_integrations_status_ui()

    def _refresh_sidebar_profile(self):
        online_str = self.i18n.get("common.status.online")
        if getattr(self, "_kick_connected", False) and getattr(self, "_kick_username", ""):
            self.sidebar.update_profile_info(self._kick_username, online_str)
        elif getattr(self, "_twitch_connected", False) and getattr(self, "_twitch_channel", ""):
            self.sidebar.update_profile_info(self._twitch_channel, online_str)
        else:
            self.sidebar.reset_profile_info()

    @Slot()
    def _handle_twitch_disconnect(self):
        if self._twitch_disconnect_pending or self._twitch_auth_start_pending:
            return
        self._twitch_disconnect_pending = True
        self.logger.info("[User Action] Twitch account unlinked successfully")
        self._stop_twitch_connection_workers(
            on_finished=self._finish_twitch_disconnect
        )

    def _finish_twitch_disconnect(self) -> None:
        self._twitch_disconnect_pending = False
        if self._is_shutting_down:
            return

        self.twitch_chat_worker = None
        self.twitch_auth_worker = None
        self.twitch_reward_worker = None
        self.fetch_twitch_rewards_worker = None
        self.command_service.twitch_worker = None
        self.spam_service.twitch_api = None
        self.spam_service.twitch_worker = None
        self.spam_service.twitch_broadcaster_id = ""
        self.container.twitch_auth_manager.logout()
        self._twitch_connected = False
        self._twitch_channel = ""
        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            self.dashboard_controller.clear_channel_profile("twitch")
        if hasattr(self, "rewards_controller") and self.rewards_controller:
            self.rewards_controller.clear_platform_rewards("twitch")
        self._refresh_sidebar_profile()
        self._update_integrations_status_ui()
        title_disc = self.container.i18n.get("main.toast.twitch_disconnected_title")
        msg_disc = self.container.i18n.get("main.toast.twitch_disconnected_msg")
        self.toast.show_toast(
            title=title_disc,
            message=msg_disc,
            state="info"
        )
        self._evaluate_all_scopes()

    def _update_integrations_status_ui(self):
        kick_connected = getattr(self, "_kick_connected", False)
        kick_user = getattr(self, "_kick_username", "")
        twitch_connected = getattr(self, "_twitch_connected", False)
        twitch_channel = getattr(self, "_twitch_channel", "")
        youtube_connected = self.youtube.is_connected
        youtube_channel = self.youtube.channel
        tiktok_connected = self.tiktok.is_connected
        tiktok_channel = self.tiktok.channel
        refresh_started = time.perf_counter()

        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            self.dashboard_controller.set_kick_status(
                connected=kick_connected,
                channel=kick_user,
                msg_count=self.session_metrics.platform_messages("kick")
            )
            self.dashboard_controller.set_twitch_status(
                connected=twitch_connected,
                channel=twitch_channel,
                msg_count=self.session_metrics.platform_messages("twitch")
            )
            self.dashboard_controller.set_youtube_status(
                connected=youtube_connected,
                channel=youtube_channel,
                msg_count=self.session_metrics.platform_messages("youtube")
            )
            self.dashboard_controller.set_tiktok_status(
                connected=tiktok_connected,
                channel=tiktok_channel,
                msg_count=self.session_metrics.platform_messages("tiktok")
            )

        dashboard_done = time.perf_counter()
        if hasattr(self, "view_settings") and self.view_settings:
            self.view_settings.set_integrations_status(
                kick_connected=kick_connected,
                kick_channel=kick_user,
                twitch_connected=twitch_connected,
                twitch_channel=twitch_channel,
                youtube_connected=youtube_connected,
                youtube_channel=youtube_channel,
                tiktok_connected=tiktok_connected,
                tiktok_channel=tiktok_channel
            )

        settings_view_done = time.perf_counter()
        conn_dict = self.get_connected_platforms()
        auth_done = time.perf_counter()
        if hasattr(self, "view_chat") and self.view_chat and hasattr(self.view_chat, "set_connected_platforms"):
            self.view_chat.set_connected_platforms(conn_dict)
        if hasattr(self, "view_commands") and self.view_commands and hasattr(self.view_commands, "set_connected_platforms"):
            self.view_commands.set_connected_platforms(conn_dict)
        if hasattr(self, "view_schedule") and self.view_schedule and hasattr(self.view_schedule, "set_connected_platforms"):
            self.view_schedule.set_connected_platforms(conn_dict)
        if hasattr(self, "view_rewards") and self.view_rewards and hasattr(self.view_rewards, "set_connected_platforms"):
            self.view_rewards.set_connected_platforms(conn_dict)
        if hasattr(self, "view_timers") and self.view_timers and hasattr(self.view_timers, "set_connected_platforms"):
            self.view_timers.set_connected_platforms(conn_dict)
        if hasattr(self, "view_alerts") and self.view_alerts and hasattr(self.view_alerts, "set_connected_platforms"):
            self.view_alerts.set_connected_platforms(conn_dict)

        finished = time.perf_counter()
        total_ms = (finished - refresh_started) * 1000
        if total_ms >= self._SLOW_STATUS_REFRESH_MS:
            self.logger.info(
                "[Perf/Integrations] Status refresh took %.2f ms (dashboard=%.2f, settings_view=%.2f, auth=%.2f, views=%.2f)",
                total_ms,
                (dashboard_done - refresh_started) * 1000,
                (settings_view_done - dashboard_done) * 1000,
                (auth_done - settings_view_done) * 1000,
                (finished - auth_done) * 1000,
            )

    def get_connected_platforms(self) -> dict[str, bool]:
        kick_auth = self.kick_auth_manager.is_authenticated() if hasattr(self, "kick_auth_manager") and self.kick_auth_manager else False
        twitch_auth = self.container.twitch_auth_manager.is_authenticated() if hasattr(self.container, "twitch_auth_manager") and self.container.twitch_auth_manager else False
        return {
            "kick": kick_auth or getattr(self, "_kick_connected", False),
            "twitch": twitch_auth or getattr(self, "_twitch_connected", False),
            "youtube": self.youtube.is_connected,
            "tiktok": self.tiktok.is_connected,
        }

    def _wire_live_chat(self, chat: LiveChatConnection) -> None:
        chat.connecting.connect(partial(self._on_live_chat_connecting, chat))
        chat.connected.connect(partial(self._on_live_chat_connected, chat))
        chat.disconnected.connect(partial(self._on_live_chat_disconnected, chat))
        chat.error_reported.connect(self._on_live_chat_error)
        chat.state_changed.connect(self._update_integrations_status_ui)
        chat.message_received.connect(self._route_incoming_message)

    def _on_live_chat_button_clicked(self, chat: LiveChatConnection) -> None:
        dialog_class, unlink_title_key, unlink_desc_key = self._LIVE_CHAT_DIALOGS[chat.platform_id]
        if chat.is_connected:
            self.logger.info("[User Action] Requested disconnecting %s", chat.log_name)
            dialog = ModernConfirmDialog(
                self.i18n,
                self,
                title_text=self.i18n.get(unlink_title_key),
                body_text=self.i18n.get(unlink_desc_key),
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                chat.disconnect_channel()
            return

        dialog = dialog_class(self.i18n, initial_target=chat.saved_target(), parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        target = "" if dialog.is_cleared() else dialog.get_target()
        if target:
            chat.connect_channel(target)
        else:
            chat.forget_channel()

    def _on_live_chat_connecting(self, chat: LiveChatConnection) -> None:
        set_status = getattr(self.dashboard_controller, f"set_{chat.platform_id}_status")
        set_status(connected=False, connecting=True)

    def _on_live_chat_connected(self, chat: LiveChatConnection, display_name: str) -> None:
        title_key, message_key, _, _ = self._LIVE_CHAT_TOASTS[chat.platform_id]
        self.toast.show_toast(
            title=self.i18n.get(title_key),
            message=self.i18n.get(message_key).replace("{target}", display_name),
            state="success",
        )

    def _on_live_chat_disconnected(self, chat: LiveChatConnection) -> None:
        _, _, title_key, message_key = self._LIVE_CHAT_TOASTS[chat.platform_id]
        self.toast.show_toast(
            title=self.i18n.get(title_key),
            message=self.i18n.get(message_key),
            state="info",
        )

    def _on_live_chat_error(self, error_msg: str, is_offline: bool) -> None:
        self.toast.show_toast(
            title=self.i18n.get("common.status.offline" if is_offline else "common.status.error"),
            message=error_msg,
            state="warning" if is_offline else "danger",
        )

    @Slot()
    def _on_twitch_integration_button_clicked(self):
        if getattr(self, "_twitch_connected", False):
            self.logger.info("[User Action] Requested unlinking Twitch account")
            dialog = ModernConfirmDialog(
                self.i18n,
                self,
                title_text=self.i18n.get("dialogs.unlink_twitch.title"),
                body_text=self.i18n.get("dialogs.unlink_twitch.desc")
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                self._handle_twitch_disconnect()
        else:
            self._handle_twitch_auth_process(force=False)

    @Slot()
    def _evaluate_all_scopes(self):
        missing_scopes = {
            "kick": self.kick_auth_manager.get_missing_scopes() if self.kick_auth_manager.is_authenticated() else [],
            "twitch": self.container.twitch_auth_manager.get_missing_scopes() if self.container.twitch_auth_manager.is_authenticated() else []
        }
        self.dashboard_controller.evaluate_scopes(missing_scopes)

    @Slot()
    def _force_reauth(self):
        if self.container.twitch_auth_manager.has_missing_scopes():
            self._handle_reauth_twitch()
        elif self.kick_auth_manager.has_missing_scopes():
            self._handle_reauth_kick()

    @Slot()
    def _handle_reauth_kick(self):
        if self._kick_reauth_pending or self._is_shutting_down:
            return
        self._kick_reauth_pending = True
        self.logger.info("[User Action] Requested renewal of Kick permissions")
        self._stop_kick_connection_workers(
            on_finished=self._finish_kick_reauth
        )

    def _finish_kick_reauth(self) -> None:
        self._kick_reauth_pending = False
        if self._is_shutting_down:
            return
        self.kick_auth_manager.logout()
        self._kick_connected = False
        self._kick_username = ""
        self.dashboard_controller.reset_to_disconnected()
        self._handle_auth_process(force=True)

    @Slot()
    def _handle_reauth_twitch(self):
        self.logger.info("[User Action] Requested renewal of Twitch permissions")
        self._handle_twitch_auth_process(force=True)

    @Slot()
    def _handle_unlink_account(self):
        if getattr(self, "_kick_connected", False):
            self.logger.info("[User Action] Requested unlinking Kick account")
            dialog = ModernConfirmDialog(
                self.i18n,
                self,
                title_text=self.i18n.get("dialogs.unlink.title"),
                body_text=self.i18n.get("dialogs.unlink.desc")
            )

            if dialog.exec() == dialog.DialogCode.Accepted:
                if self._kick_disconnect_pending:
                    return
                self._kick_disconnect_pending = True
                self.logger.info("[User Action] Kick account unlinked successfully")
                self.toast.show_toast(
                    title=self.i18n.get("main.toast.kick_disconnected_title"),
                    message=self.i18n.get("main.toast.kick_disconnected_msg"),
                    state="info"
                )
                self._stop_kick_connection_workers(
                    on_finished=self._finish_kick_disconnect
                )
        else:
            self._handle_auth_process()

    def _finish_kick_disconnect(self) -> None:
        self._kick_disconnect_pending = False
        if self._is_shutting_down:
            return

        self.kick_chat_worker = None
        self.timers_worker = None
        self.kick_auth_manager.logout()
        self._kick_connected = False
        self._kick_username = ""
        if self.dashboard_controller:
            self.dashboard_controller.clear_channel_profile("kick")
        if self.rewards_controller:
            self.rewards_controller.clear_platform_rewards("kick")
        self._refresh_sidebar_profile()
        self._update_integrations_status_ui()
        self._evaluate_all_scopes()

    @Slot(str)
    def _handle_alert_platform_connect(self, platform: str):
        if platform == "kick":
            self._handle_auth_process()
        elif platform == "twitch":
            self._handle_twitch_auth_process(force=False)

    def _start_schedule_worker(self):
        current_worker = getattr(self, "schedule_worker", None)
        if current_worker is None or not current_worker.isRunning():
            self.schedule_worker = ScheduleWorker(self.schedule_service)
            self.schedule_worker.schedule_triggered.connect(self._on_schedule_triggered)
            self.schedule_worker.start()

    def _on_schedule_triggered(self, schedule: dict, _result: dict):
        name = schedule.get("name", "")
        title = self.i18n.get("stream_info.toasts.schedule_auto_applied")
        self.toast.show_toast(
            title=title,
            message=name,
            state="success"
        )
        if hasattr(self, "schedule_controller") and self.schedule_controller:
            self.schedule_controller.reload_schedules()
            self.schedule_controller.fetch_current_info()

    def _route_incoming_message(self, user_or_dto, msg: str = None, badges: list = None, color: str = "", msg_id: str = "", sender_id: int = 0, avatar_url: str = ""):
        if isinstance(user_or_dto, ChatMessageDTO):
            dto = user_or_dto
            if not dto.timestamp:
                dto.timestamp = datetime.now().strftime("%H:%M")
            platform = getattr(dto, "platform", "kick") or "kick"
        else:
            dto = ChatMessageDTO(
                user_or_dto,
                msg,
                badges or [],
                color,
                msg_id,
                sender_id,
                timestamp=datetime.now().strftime("%H:%M"),
                avatar_url=avatar_url
            )
            platform = "kick"

        if not getattr(dto, "avatar_url", ""):
            user_lower = str(dto.user).lower()
            if platform == "kick" and getattr(self, "_kick_username", "") and user_lower == self._kick_username.lower():
                dto.avatar_url = getattr(self, "_kick_avatar_url", "")
            elif platform == "twitch" and getattr(self, "_twitch_channel", "") and user_lower == self._twitch_channel.lower():
                dto.avatar_url = getattr(self, "_twitch_avatar_url", "")

        self.session_metrics.record_message(platform)

        self.chat_controller.process_message(dto)

    def _on_poll_updated(self, poll_data: dict):
        if hasattr(self, 'overlay_server') and self.overlay_server:
            self.overlay_server.trigger_widget_event("poll_update", {"poll": poll_data})

    def _on_poll_deleted(self):
        if hasattr(self, 'overlay_server') and self.overlay_server:
            self.overlay_server.trigger_widget_event("poll_delete", {})

    def _on_pinned_created(self, pinned_data: dict):
        if hasattr(self, 'overlay_server') and self.overlay_server:
            self.overlay_server.trigger_widget_event("pinned_created", {"pinned": pinned_data})

    def _on_pinned_deleted(self):
        if hasattr(self, 'overlay_server') and self.overlay_server:
            self.overlay_server.trigger_widget_event("pinned_deleted", {})

    @Slot(bool)
    def _handle_tray_tts_toggle(self, enabled: bool):
        self.chat_controller.set_tts_option("enabled", enabled)
        estado = (self.i18n.get("main.tray.tts_on") if enabled else self.i18n.get("main.tray.tts_off"))
        msg_template = self.i18n.get("main.tray.tts_msg")
        self.tray_manager.showMessage("MiniKick", msg_template.replace("{estado}", estado), QSystemTrayIcon.MessageIcon.Information, 2000)

    @Slot()
    def _handle_tray_play_pause(self):
        if hasattr(self, "music_controller"):
            self.music_controller.handle_play_pause()

    @Slot()
    def _handle_tray_skip(self):
        if hasattr(self, "music_controller"):
            self.music_controller.handle_skip()

    @Slot(object)
    def _handle_tray_song_changed(self, song: dict):
        if hasattr(self, "tray_manager"):
            is_playing = bool(song.get("is_playing", False)) if isinstance(song, dict) else False
            self.tray_manager.set_playback_state(is_playing)

    @Slot(bool)
    def _handle_tray_tts_use_command_toggle(self, enabled: bool):
        self.chat_controller.set_tts_option("use_command", enabled)

    @Slot(bool)
    def _handle_tray_tts_voice_type_change(self, is_web: bool):
        self.chat_controller.set_tts_option("provider", "web" if is_web else "piper")

    @Slot(bool)
    def _handle_chat_tts_state_changed(self, enabled: bool):
        settings = self.chat_service.get_settings()
        self.tray_manager.set_tts_state(enabled)
        self.tray_manager.set_tts_use_command_state(settings.get("use_command", False))
        self.tray_manager.set_tts_voice_type_state(settings.get("provider", "piper") == "web")

    @Slot(int)
    def _apply_dynamic_theme(self, base_size: int):
        current_size = getattr(self, "_applied_font_size", None)
        if current_size == base_size:
            return
        self._applied_font_size = base_size
        app = QApplication.instance()
        if app:
            self.setStyleSheet(get_global_qss(base_size))

    @Slot()
    def handle_update_check(self):
        present_update_dialog(self.updater_controller, self, self.i18n, on_restart_callback=self._force_quit)

    def _refresh_dashboard_view(self) -> None:
        if self._is_shutting_down:
            return
        metrics = self.session_metrics
        self.view_dashboard.update_session_metrics(
            msg_count=metrics.messages_processed,
            cmd_count=metrics.total_usages,
            timer_count=metrics.active_timers,
            spam_count=metrics.spam_blocked,
        )
        self.dashboard_controller.update_platform_messages(
            **{platform: metrics.platform_messages(platform) for platform in metrics.PLATFORMS}
        )

    @Slot()
    def _update_dashboard_metrics(self, force_db_query=False):
        if self._is_shutting_down:
            return
        if self.session_metrics.refresh_analytics(force=force_db_query):
            self._refresh_dashboard_view()
