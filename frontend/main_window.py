# frontend\main_window.py

import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Slot, Signal, QTimer

from backend.utils import perf_phase
from backend.services import WhatsNewService
from backend.controllers import UpdaterController
from frontend.common import get_global_qss, Size
from frontend.navigation import Sidebar, ToastManager
from frontend.views import DashboardView
from frontend.dialogs import ModernConfirmDialog, present_update_dialog
from frontend.main_window_views import MainWindowViewFactory
from frontend.view_prewarmer import ViewPrewarmer
from frontend.recent_redemptions import RecentRedemptionCache
from frontend.window import SessionMetrics, MainWindowShutdown, AutoUpdateCoordinator, WhatsNewPresenter, WindowStateManager, MainWindowComposition, NavigationCoordinator, MainWindowStartup, TrayPresenter, MainWindowWiring
from backend.connections import (
    WorkerSlot,
    TikTokConnection,
    TwitchConnection,
    YouTubeConnection,
)

from backend.config import TWITCH_CLIENT_ID

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
        ("Webhooks", "webhooks-filled.svg", "top"),

        ("Settings", "gear-filled.svg", "bottom"),
        ("Developer", "file-text-filled.svg", "bottom"),
    )
    _PREWARM_EXCLUDED_VIEWS = ("Dashboard", "Developer")

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
        self._init_session_state()
        self._bind_container()
        self._init_shutdown_support()
        self._init_live_chat_connections()
        self._init_twitch_connection()
        self.composition = MainWindowComposition(self)
        self.setWindowTitle(self.i18n.get("main.window.title").replace("{version}", app_version))

        self.logger.info("[MainWindow] Initializing main window components and UI shell...")
        self.toast = ToastManager(self)
        self.wiring = MainWindowWiring(self)
        with perf_phase(self.logger, "Startup", "Main UI shell and controllers initialized"):
            self._setup_ui()
        with perf_phase(self.logger, "Startup", "Tray and startup wiring initialized"):
            self.tray_presenter.setup()
            self._init_updater()
            self.wiring.connect_signals()
            self.startup.load_settings_into_ui()

        self.setUpdatesEnabled(True)
        self.logger.info("[MainWindow] Main window initialization complete.")

    def _init_flags(self):
        self._is_shutting_down = False
        self._cleanup_complete = False
        self._quit_requested = False
        self._startup_silent_connections: set[str] = set()
        self._applied_font_size: int | None = None

    def _consume_startup_silent_connection(self, platform: str) -> bool:
        if platform not in self._startup_silent_connections:
            return False
        self._startup_silent_connections.discard(platform)
        return True

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

    def _init_twitch_connection(self):
        self.twitch = TwitchConnection(
            auth_manager=self.container.twitch_auth_manager,
            client_id=TWITCH_CLIENT_ID,
            i18n=self.i18n,
            coordinator=self._worker_shutdown_coordinator,
            is_shutting_down=lambda: self._is_shutting_down,
            parent=self,
        )

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
        self.window_state = WindowStateManager(self, self.settings_storage)

    def _init_shutdown_support(self):
        self.shutdown = MainWindowShutdown(self)
        self._worker_shutdown_coordinator = self.shutdown.worker_shutdown_coordinator

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
        self.composition.create_services()
        self._create_views_registry()
        self.composition.create_controllers()
        self._start_background_workers()
        self._assemble_layout()
        QTimer.singleShot(0, self._update_dashboard_metrics)
        self._init_whats_new()
        self.whats_new.init_badges()
        self.startup = MainWindowStartup(self, self._view_prewarmer)
        self.tray_presenter = TrayPresenter(self)

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
        self.view_webhooks = None

        self._instantiated_views = {"Dashboard": self.view_dashboard}
        self._view_factory = MainWindowViewFactory(self)
        self.navigation = NavigationCoordinator(self)
        self._view_prewarmer = ViewPrewarmer(
            create_view=self.navigation.get_or_create_view,
            view_names=[name for name, _icon, _area in self._NAV_CONFIG if name not in self._PREWARM_EXCLUDED_VIEWS],
            is_created=lambda name: name in self._instantiated_views,
            is_active=lambda: not self._is_shutting_down,
            seconds_since_navigation=self.navigation.seconds_since_navigation,
            schedule=QTimer.singleShot,
        )

    def _start_background_workers(self):
        self.schedule_presenter.start_worker()
        self.media_keys.setup_global_keys()

    def _assemble_layout(self):
        self.content_stack.addWidget(self.view_dashboard)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

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

    def _force_quit(self):
        self.shutdown.force_quit()

    def _cleanup(self):
        self.shutdown.cleanup()

    @Slot(int)
    def _apply_dynamic_theme(self, base_size: int):
        if self._applied_font_size == base_size:
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
