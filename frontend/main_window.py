# frontend\main_window.py

import html
import threading
import time
import logging
from datetime import datetime
from typing import Callable
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Slot, Signal, QTimer, QThread

from backend.utils.perf import perf_phase
from backend.services import ChatMessageDTO, WhatsNewService
from backend.controllers import UpdaterController
from backend.workers import ScheduleWorker
from frontend.common import get_global_qss, BrandColors, Size
from frontend.dialogs.update_flow import present_update_dialog
from frontend.navigation import Sidebar, ToastManager, SystemTrayManager
from frontend.views import DashboardView
from frontend.dialogs import ModernConfirmDialog, YouTubeConnectDialog, TikTokConnectDialog
from frontend.main_window_views import MainWindowViewFactory
from frontend.view_prewarmer import ViewPrewarmer
from frontend.recent_redemptions import RecentRedemptionCache
from frontend.window.session_metrics import SessionMetrics
from frontend.window.shutdown import ShutdownSequence
from frontend.window.updates import AutoUpdateCoordinator
from frontend.window.whats_new import WhatsNewPresenter
from frontend.window.window_state import WindowStateManager
from backend.connections import (
    LiveChatConnection,
    WorkerShutdownCoordinator,
    WorkerSlot,
    TikTokConnection,
    TwitchConnection,
    YouTubeConnection,
)

from backend.config import TWITCH_CLIENT_ID
from frontend.window.composition import MainWindowComposition
from frontend.window.startup import StartupSequencer
from frontend.window.wiring import MainWindowWiring

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
            self._setup_tray()
            self._init_updater()
            self.wiring.connect_signals()
            self._load_settings_into_ui()

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
        self.composition.create_services()
        self._create_views_registry()
        self.composition.create_controllers()
        self._start_background_workers()
        self._assemble_layout()
        QTimer.singleShot(0, self._update_dashboard_metrics)
        self._init_whats_new()
        self.whats_new.init_badges()
        self.startup_sequencer = StartupSequencer(
            logger=self.logger,
            is_active=lambda: not self._is_shutting_down,
            whats_new_check=self.whats_new.check_dialog,
            prewarm_views=self._view_prewarmer.start,
            start_database_maintenance=self._start_database_maintenance,
        )

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

    def _load_settings_into_ui(self, *, refresh_chat_backend: bool = False):
        self.logger.debug("[AutoStart] Loading controller initial state (Rewards, Widgets, Chat, Spam, Timers, Music)...")
        steps = (
            ("rewards", self.rewards_controller.load_initial_data),
            ("widgets", self.widgets_controller.load_initial_data),
            ("chat settings", self._load_chat_settings),
            ("command cache", self.command_service.reload_cache),
            ("spam, timers, and music", self._load_remaining_controller_data),
            ("chat and overlay settings", lambda: self._load_chat_controller_data(refresh_backend=refresh_chat_backend)),
            ("integrations and profile", self._finish_settings_hydration),
        )
        self.startup_sequencer.start(steps)

    def _on_backup_restored(self):
        self._load_settings_into_ui(refresh_chat_backend=True)

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
                self._handle_auth_process(startup=True)
            except Exception as e:
                self.logger.error("[AutoStart] Error auto-starting Kick integration: %s", e)

        twitch_tokens = self.container.twitch_token_storage.load()
        if twitch_tokens and twitch_tokens.get("access_token"):
            QTimer.singleShot(1200, self._autostart_twitch)

    def _schedule_live_chat_autostarts(self) -> None:
        for chat, delay_ms in ((self.youtube, 2400), (self.tiktok, 3600)):
            target = chat.saved_target()
            if target:
                QTimer.singleShot(delay_ms, lambda c=chat, t=target: self._autostart_live_chat(c, t))

    def _autostart_twitch(self):
        if self._is_shutting_down:
            return
        try:
            self.logger.info("[AutoStart] Starting Twitch integration...")
            self._startup_silent_connections.add("twitch")
            self.twitch.resume_session()
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
            self._startup_silent_connections.add(chat.platform_id)
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

    def _stop_all_workers(
        self,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        slots = (
            self.media_keys.slot,
            self.whats_new.slot,
            *(chat.slot for chat in self.live_chats),
            *self.twitch.slots,
            *self.kick.slots,
            self._schedule_slot,
        )
        self._stop_workers_parallel([slot.detach() for slot in slots], on_finished=on_finished)

    @Slot()
    def _handle_auth_process(self, force: bool = False, *, startup: bool = False):
        if not startup:
            self._startup_silent_connections.discard("kick")
        if self.twitch.is_auth_running:
            self.toast.show_toast(
                title=self.container.i18n.get("main.toast.auth_in_progress_title"),
                message=self.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning"
            )
            return
        if startup:
            self._startup_silent_connections.add("kick")
        self.kick.authenticate(force=force)

    def _on_kick_api_changed(self, api) -> None:
        self._evaluate_all_scopes()

        self.command_service.api_client = api
        self.spam_service.api_client = api
        self.timer_service.api_client = api

        self.command_service.reload_cache()
        self.spam_service.reload_filters()

        self.schedule_service.set_kick_client(api)
        self._start_schedule_worker()
        self.schedule_controller.fetch_current_info()

    def _on_kick_connected(self, username: str, user_data: dict) -> None:
        self.spam_service.broadcaster_id = user_data.get("broadcaster_id", 0)
        self.dashboard_controller.handle_connection_success(user_data)
        self._refresh_sidebar_profile()

        if not self._consume_startup_silent_connection("kick"):
            self.toast.show_toast(
                title=self.i18n.get("main.toast.kick_connected_title"),
                message=self.i18n.get("main.toast.kick_connected_msg").replace("{username}", username),
                state="success"
            )
        self._fetch_api_rewards()

    @Slot()
    def _fetch_api_rewards(self):
        self.kick.fetch_rewards()
        if self.container.twitch_auth_manager.is_authenticated():
            self.twitch.fetch_rewards()

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
        redemption = self.reward_redemption_handler.begin(user, reward_name, platform)
        if redemption is None:
            return

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

        outcome = self.reward_redemption_handler.process(redemption)
        if outcome.configured and not outcome.media_valid:
            missing_log = self.i18n.get("main.logs.reward_file_missing").replace("{reward_name}", reward_name).replace("{filepath}", outcome.filepath)
            self.logger.warning(missing_log)
            self.toast.show_toast(
                title=self.i18n.get("common.status.warning"),
                message=self.i18n.get("rewards.status.redeem_file_missing").replace("{reward}", reward_name),
                state="danger"
            )
        elif not outcome.configured:
            no_rewards_template = self.i18n.get("main.logs.reward_no_rewards")
            self.logger.debug("[Reward] %s", no_rewards_template.replace("{reward_name}", reward_name))

        settings = self.chat_service.get_settings()
        if settings.get("enabled", False) and message:
            dto = ChatMessageDTO(user, message, [], "", "", 0, timestamp=current_time, platform=platform)
            self.chat_controller.process_message(dto)

    def _handle_incoming_alert(self, alert_event):
        self.container.alert_service.process_event(alert_event)

    @Slot(str, bool, bool)
    def _send_timer_message(self, message: str, apply_kick: bool = True, apply_twitch: bool = True):
        if message:
            self.command_service.post_chat_message(message, apply_kick=apply_kick, apply_twitch=apply_twitch)

    @Slot()
    def _handle_twitch_auth_process(self, force: bool = False):
        self._startup_silent_connections.discard("twitch")
        if self.kick.is_auth_running or self.twitch.is_auth_running:
            self.toast.show_toast(
                title=self.container.i18n.get("main.toast.auth_in_progress_title"),
                message=self.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning",
            )
            return
        self.twitch.authenticate(force=force)

    def _on_twitch_browser_auth_opening(self) -> None:
        self.toast.show_toast(
            title=self.container.i18n.get("main.toast.twitch_auth_title"),
            message=self.container.i18n.get("main.toast.twitch_auth_opening"),
            state="info",
        )

    def _on_twitch_auth_failed(self, error: str) -> None:
        if self._is_shutting_down:
            return
        self.toast.show_toast(
            title=self.container.i18n.get("main.toast.twitch_auth_error_title"),
            message=error,
            state="danger",
        )

    def _on_twitch_api_changed(self, api) -> None:
        self.spam_service.twitch_api = api

    def _on_twitch_chat_worker_changed(self, worker) -> None:
        self.command_service.twitch_worker = worker
        self.spam_service.twitch_worker = worker

    def _on_twitch_error(self, error_msg: str) -> None:
        if self._is_shutting_down:
            return
        self.toast.show_toast(
            title=self.container.i18n.get("common.status.error"),
            message=error_msg,
            state="danger",
        )

    def _on_twitch_connected(self, username: str, broadcaster_id: str, profile: dict) -> None:
        if broadcaster_id:
            self.spam_service.twitch_broadcaster_id = broadcaster_id
        self._refresh_sidebar_profile()

        self.schedule_service.set_twitch_client(self.twitch.api, broadcaster_id)
        self.schedule_controller.fetch_current_info()
        self.rewards_controller.set_twitch_context(
            self.container.twitch_auth_manager,
            self.twitch.api,
            broadcaster_id,
        )
        if profile:
            self.dashboard_controller.set_channel_profile("twitch", profile)

        self._evaluate_all_scopes()

        if not self._consume_startup_silent_connection("twitch"):
            self.toast.show_toast(
                title=self.container.i18n.get("main.toast.twitch_connected_title"),
                message=self.container.i18n.get("main.toast.twitch_connected_msg").replace("{username}", username),
                state="success",
            )

    def _refresh_sidebar_profile(self):
        online_str = self.i18n.get("common.status.online")
        if self.kick.is_connected and self.kick.username:
            self.sidebar.update_profile_info(self.kick.username, online_str)
        elif self.twitch.is_connected and self.twitch.channel:
            self.sidebar.update_profile_info(self.twitch.channel, online_str)
        else:
            self.sidebar.reset_profile_info()

    def _on_twitch_disconnected(self) -> None:
        self.spam_service.twitch_broadcaster_id = ""
        self.dashboard_controller.clear_channel_profile("twitch")
        self.rewards_controller.clear_platform_rewards("twitch")
        self._refresh_sidebar_profile()
        self.toast.show_toast(
            title=self.container.i18n.get("main.toast.twitch_disconnected_title"),
            message=self.container.i18n.get("main.toast.twitch_disconnected_msg"),
            state="info",
        )
        self._evaluate_all_scopes()

    def _update_integrations_status_ui(self):
        self.integrations_status.refresh()

    def get_connected_platforms(self) -> dict[str, bool]:
        return self.connection_hub.get_connected_platforms()

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
                self._startup_silent_connections.discard(chat.platform_id)
                chat.disconnect_channel()
            return

        dialog = dialog_class(self.i18n, initial_target=chat.saved_target(), parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        target = "" if dialog.is_cleared() else dialog.get_target()
        if target:
            self._startup_silent_connections.discard(chat.platform_id)
            chat.connect_channel(target)
        else:
            chat.forget_channel()

    def _on_live_chat_connecting(self, chat: LiveChatConnection) -> None:
        set_status = getattr(self.dashboard_controller, f"set_{chat.platform_id}_status")
        set_status(connected=False, connecting=True)

    def _on_live_chat_connected(self, chat: LiveChatConnection, display_name: str) -> None:
        if self._consume_startup_silent_connection(chat.platform_id):
            return
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
        if self.twitch.is_connected:
            self.logger.info("[User Action] Requested unlinking Twitch account")
            dialog = ModernConfirmDialog(
                self.i18n,
                self,
                title_text=self.i18n.get("dialogs.unlink_twitch.title"),
                body_text=self.i18n.get("dialogs.unlink_twitch.desc")
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                self.twitch.disconnect_account()
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
        self.kick.reauthenticate()

    def _on_kick_reauth_ready(self) -> None:
        self.dashboard_controller.reset_to_disconnected()
        self._handle_auth_process(force=True)

    @Slot()
    def _handle_reauth_twitch(self):
        self.logger.info("[User Action] Requested renewal of Twitch permissions")
        self._handle_twitch_auth_process(force=True)

    @Slot()
    def _handle_unlink_account(self):
        if not self.kick.is_connected:
            self._handle_auth_process()
            return

        self.logger.info("[User Action] Requested unlinking Kick account")
        dialog = ModernConfirmDialog(
            self.i18n,
            self,
            title_text=self.i18n.get("dialogs.unlink.title"),
            body_text=self.i18n.get("dialogs.unlink.desc")
        )
        if dialog.exec() == dialog.DialogCode.Accepted and self.kick.disconnect_account():
            self.toast.show_toast(
                title=self.i18n.get("main.toast.kick_disconnected_title"),
                message=self.i18n.get("main.toast.kick_disconnected_msg"),
                state="info"
            )

    def _on_kick_disconnected(self) -> None:
        self.dashboard_controller.clear_channel_profile("kick")
        self.rewards_controller.clear_platform_rewards("kick")
        self._refresh_sidebar_profile()
        self._evaluate_all_scopes()

    @Slot(str)
    def _handle_alert_platform_connect(self, platform: str):
        if platform == "kick":
            self._handle_auth_process()
        elif platform == "twitch":
            self._handle_twitch_auth_process(force=False)

    def _start_schedule_worker(self):
        self._schedule_slot.start(self._build_schedule_worker)

    def _build_schedule_worker(self) -> ScheduleWorker:
        worker = ScheduleWorker(self.schedule_service)
        worker.schedule_triggered.connect(self._on_schedule_triggered)
        return worker

    def _on_schedule_triggered(self, schedule: dict, _result: dict):
        name = schedule.get("name", "")
        title = self.i18n.get("stream_info.toasts.schedule_auto_applied")
        self.toast.show_toast(
            title=title,
            message=name,
            state="success"
        )
        self.schedule_controller.reload_schedules()
        self.schedule_controller.fetch_current_info()

    def _route_incoming_message(
        self,
        user_or_dto,
        msg: str = None,
        badges: list = None,
        color: str = "",
        msg_id: str = "",
        sender_id: int = 0,
        avatar_url: str = "",
    ):
        self.chat_message_router.route(
            user_or_dto,
            msg,
            badges,
            color,
            msg_id,
            sender_id,
            avatar_url,
        )

    def _get_message_profile(self, platform: str) -> tuple[str, str]:
        if platform == "kick":
            return self.kick.username, self.kick.avatar_url
        if platform == "twitch":
            return self.twitch.channel, self.twitch.avatar_url
        return "", ""

    def _on_poll_updated(self, poll_data: dict):
        self.overlay_server.trigger_widget_event("poll_update", {"poll": poll_data})

    def _on_poll_deleted(self):
        self.overlay_server.trigger_widget_event("poll_delete", {})

    def _on_pinned_created(self, pinned_data: dict):
        self.overlay_server.trigger_widget_event("pinned_created", {"pinned": pinned_data})

    def _on_pinned_deleted(self):
        self.overlay_server.trigger_widget_event("pinned_deleted", {})

    @Slot(bool)
    def _handle_tray_tts_toggle(self, enabled: bool):
        self.chat_controller.set_tts_option("enabled", enabled)

    @Slot()
    def _handle_tray_play_pause(self):
        self.music_controller.handle_play_pause()

    @Slot()
    def _handle_tray_skip(self):
        self.music_controller.handle_skip()

    @Slot(object)
    def _handle_tray_song_changed(self, song: dict):
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
