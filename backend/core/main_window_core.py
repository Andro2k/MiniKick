# backend\core\main_window_core.py

import sys
import html
import time
import logging
from collections import deque
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, 
    QSystemTrayIcon, QApplication
)
from PySide6.QtCore import Qt, Slot, QEvent, QTimer

from .app_container_core import AppContainerCore
from .app_logger_core import setup_application_logging
from backend.services import (
    ChatMessageDTO, RewardsService, ChatService, CommandService, AvatarService,
    LogService, SettingsService, SpamService, TimerService
)
from backend.controllers import (
    RewardsController, ChatController, CommandController, DashboardController,
    TimerController, LogController, MusicController, SettingsController,
    SpamController, UpdateController, WidgetController,
    ScheduleController, AlertsController
)
from backend.providers import KickAPIClient, TwitchAPIClient
from backend.workers import (
    KickAuthWorker, TwitchAuthWorker, KickChatWorker, TwitchChatWorker, YouTubeChatWorker, TikTokChatWorker,
    FetchRewardsWorker, TwitchRewardWorker, TimerWorker, ScheduleWorker, GlobalMediaWorker
)
from frontend.common import COLOR_GREEN, get_global_qss
from frontend.navigation import Sidebar, ToastManager, SystemTrayManager
from frontend.views import (
    RewardsView, CommandView, DashboardView, TimersView, ChatView,
    LogView, MusicView, SettingsView, SpamView, WidgetsView,
    ScheduleView, AlertsView
)
from frontend.dialogs import ModernConfirmDialog, YouTubeConnectDialog, TikTokConnectDialog

try:
    from backend.config import KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY, TWITCH_CLIENT_ID
except ImportError:
    KICK_PUSHER_CLUSTER = "us2"
    KICK_PUSHER_KEY = "32cbd69e4b950bf97679"
    TWITCH_CLIENT_ID = ""

logger = logging.getLogger("minikick.core")

class MainWindowCore(QMainWindow):
    _recent_reward_redemptions: deque | None = None
    SETTING_MINIMIZE_TRAY = "minimize_to_tray"
    SETTING_AUTOSTART = "dashboard_autostart"

    _NAV_CONFIG = (
        ("Dashboard", "dashboard.svg", "top"),
        ("Chat", "message.svg", "top"),
        ("Stream Info", "calendar.svg", "top"),
        ("Spam Filters", "shield-half.svg", "top"),
        ("Comandos", "code.svg", "top"),
        ("Timers", "clock.svg", "top"),
        ("Music", "music.svg", "top"),
        ("Widgets", "apps.svg", "top"),
        ("Triggers", "chart-bubble.svg", "top"),
        ("Alerts", "alert-circle.svg", "top"),

        ("Settings", "settings.svg", "bottom"),
        ("Developer", "brand-tabler.svg", "bottom"),
    )

    def __init__(self, updater_manager, app_version: str):
        super().__init__()
        self.setUpdatesEnabled(False)
        self.resize(1200, 800)
        
        self._is_shutting_down = False
        self.updater_manager = updater_manager
        self.app_version = app_version
        
        self.container = AppContainerCore()
        self.settings_storage = self.container.settings_storage 
        self.rewards_storage = self.container.rewards_storage
        self.commands_storage = self.container.commands_storage
        self.spam_storage = self.container.spam_storage
        self.timers_storage = self.container.timers_storage
        self.backup_service = self.container.backup_service
        self.i18n = self.container.i18n
        self.kick_auth_manager = self.container.kick_auth_manager
        self.tts_manager = self.container.tts_manager
        self.overlay_server = self.container.overlay_server
        
        title_template = self.i18n.get("main.window.title")
        self.setWindowTitle(title_template.replace("{version}", app_version))
        
        self.kick_chat_worker = None
        self.kick_api_client = None
        self.kick_auth_worker = None
        self.fetch_rewards_worker = None
        self.timers_worker = None
        self.schedule_worker = None
        self.global_media_worker = None
        self.twitch_chat_worker = None
        self.twitch_auth_worker = None
        self.youtube_chat_worker = None
        self._youtube_connected = False
        self._youtube_channel = ""
        self.tiktok_chat_worker = None
        self._tiktok_connected = False
        self._tiktok_channel = ""

        self._cached_total_usages = None
        self._cached_active_timers = None

        self.session_metrics = {
            "messages_processed": 0,
            "spam_blocked": 0
        }
        self.session_platform_messages = {
            "kick": 0,
            "twitch": 0,
            "youtube": 0,
            "tiktok": 0
        }
        self._recent_reward_redemptions = deque(maxlen=100)

        self.logger, self.q_log_handler = setup_application_logging()  
        self.logger.info("[MainWindow] Initializing main window components and UI shell...")
        self.toast = ToastManager(self)
        self._setup_ui()
        self.logger.debug("[MainWindow] Setting up system tray...")
        self._setup_tray() 
        
        self.logger.debug("[MainWindow] Checking background silent updates...")
        self.update_controller = UpdateController(self.updater_manager)
        self.update_controller.update_found_silent.connect(self._on_silent_update_found)
        self.update_controller.check_updates_silently()
        
        self.logger.debug("[MainWindow] Connecting signal handlers...")
        self._connect_signals()     
        self.logger.info("[MainWindow] Hydrating views and loading stored settings into UI...")
        self._load_settings_into_ui()
        self.setUpdatesEnabled(True)
        self.logger.info("[MainWindow] Main window initialization complete.")
        self._schedule_view_prewarming()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sidebar = Sidebar(self.i18n, app_version=self.app_version, parent=self)
        for name, icon, pos in self._NAV_CONFIG:
            self.sidebar.add_tab(name, icon, position=pos, is_active=(name == "Dashboard"))

        self.content_stack = QStackedWidget(self.central_widget)
        self.avatar_service = AvatarService(avatar_storage=self.container.avatar_storage)
        self.chat_service = ChatService(self.tts_manager, self.settings_storage)
        self.settings_service = SettingsService(self.settings_storage, self.backup_service)
        self.rewards_service = RewardsService(self.rewards_storage, self.overlay_server)
        
        self.command_service = CommandService(self.commands_storage, api_client=None)
        self.spam_service = SpamService(self.spam_storage, api_client=None, i18n=self.i18n)
        self.timer_service = TimerService(self.timers_storage, api_client=None)
        self.log_service = LogService(log_storage=self.container.system_log_storage)
        self.schedule_service = self.container.schedule_service

        self.view_dashboard = DashboardView(self.i18n, parent=self)
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

        self.dashboard_controller = DashboardController(
            view=self.view_dashboard, 
            avatar_service=self.avatar_service,
            db_manager=self.container.db_manager
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
        self.widget_controller = WidgetController(
            view=None,
            widget_service=self.container.widget_service,
            command_service=self.command_service,
            overlay_server=self.overlay_server,
            i18n=self.i18n,
            toast_manager=self.toast
        )
        self.music_controller = MusicController(
            view=None,
            command_service=self.command_service,
            toast_manager=self.toast,
            i18n=self.i18n,
            settings_storage=self.container.settings_storage,
            music_storage=self.container.music_storage,
            music_provider=self.container.music_provider
        )
        self.rewards_controller = RewardsController(
            view=None, 
            service=self.rewards_service,
            toast_manager=self.toast,
            kick_auth_manager=self.kick_auth_manager,
            twitch_auth_manager=getattr(self.container, "twitch_auth_manager", None)
        )
        self.command_controller = CommandController(
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
        self.timer_controller = TimerController(
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
            tts_manager=self.tts_manager
        )
        self.log_controller = LogController(
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
            i18n=self.i18n
        )
        self._start_schedule_worker()
        self._setup_global_media_keys()
        self.session_metrics = {
            "messages_processed": 0,
            "commands_executed": 0,
            "timers_sent": 0,
            "spam_blocked": 0
        }

        self.content_stack.addWidget(self.view_dashboard)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

        self._update_dashboard_metrics()

    def _setup_tray(self):
        self.tray_manager = SystemTrayManager(self.i18n, self)
        self.tray_manager.restore_requested.connect(self._restore_from_tray)
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
        self.dashboard_controller.request_connection.connect(self._handle_auth_process)
        self.dashboard_controller.twitch_connect_requested.connect(self._on_twitch_integration_button_clicked)
        self.dashboard_controller.youtube_connect_requested.connect(self._on_youtube_integration_button_clicked)
        self.dashboard_controller.tiktok_connect_requested.connect(self._on_tiktok_integration_button_clicked)
        self.dashboard_controller.auto_start_toggled.connect(self._handle_autostart_change)
        self.dashboard_controller.reauth_requested.connect(self._force_reauth)
        self.dashboard_controller.reauth_kick_requested.connect(self._handle_reauth_kick)
        self.dashboard_controller.reauth_twitch_requested.connect(self._handle_reauth_twitch)
        self.chat_controller.tts_state_changed.connect(self._handle_chat_tts_state_changed)
        self.chat_controller.message_received.connect(self.overlay_server.trigger_chat_message)
        self.chat_controller.message_received.connect(self.widget_controller.handle_chat_message)
        self.music_controller.song_changed.connect(self.overlay_server.trigger_music_change)
        self.chat_controller.music_plugin_triggered.connect(self.music_controller.handle_music_plugin_command)
        self.chat_controller.widget_plugin_triggered.connect(self.widget_controller.handle_widget_command)
        self.chat_controller.spam_blocked.connect(lambda: self._increment_metric("spam_blocked"))
        self.chat_controller.command_executed.connect(lambda *args: self._update_dashboard_metrics(force_db_query=True))
        self.settings_controller.unlink_account_requested.connect(self._handle_unlink_account)
        self.settings_controller.check_update_requested.connect(self.handle_update_check)
        self.sidebar.update_requested.connect(self.handle_update_check)
        self.settings_controller.notification_requested.connect(lambda title, msg: self.tray_manager.showMessage(title, msg))
        self.settings_controller.backup_restored.connect(self._load_settings_into_ui)
        self.q_log_handler.emitter.log_received.connect(self.log_controller.process_incoming_log)
        self.avatar_service.avatar_downloaded.connect(self.sidebar.update_profile_avatar)

    def _load_settings_into_ui(self):
        self.logger.debug("[AutoStart] Loading controller initial state (Rewards, Widgets, Chat, Spam, Timers, Music)...")
        self.rewards_controller.load_initial_data()
        self.widget_controller.load_initial_data()
        settings = self.chat_service.get_settings()
        self.tray_manager.set_tts_state(settings.get("enabled", True))
        self.tray_manager.set_tts_use_command_state(settings.get("use_command", False))
        self.tray_manager.set_tts_voice_type_state(settings.get("provider", "local") == "web")
        autostart_enabled = self.settings_storage.load_bool(self.SETTING_AUTOSTART, False)
        self.view_dashboard.set_autostart_state(autostart_enabled)
        self.command_service.reload_cache()
        self.spam_controller.load_initial_data()
        self.timer_controller.load_initial_data()
        self.music_controller.load_initial_data()
        self.chat_controller.load_initial_data()
        self.chat_controller.sync_settings_cache()
        self._apply_dynamic_theme(self.settings_service.get_font_size(), immediate=True)
        self._update_integrations_status_ui()
        self._refresh_sidebar_profile()
        self._evaluate_all_scopes()

        self.logger.info("[AutoStart] Autostart configuration: enabled=%s", autostart_enabled)
        if autostart_enabled:
            if self.kick_auth_manager.is_authenticated():
                try:
                    self.logger.info("[AutoStart] Starting Kick integration...")
                    self._handle_auth_process()
                except Exception as e:
                    self.logger.error("[AutoStart] Error auto-starting Kick integration: %s", e)
            twitch_tokens = self.container.twitch_token_storage.load()
            if twitch_tokens and twitch_tokens.get("access_token"):
                try:
                    self.logger.info("[AutoStart] Starting Twitch integration...")
                    self._on_twitch_auth_success(twitch_tokens)
                except Exception as e:
                    self.logger.error("[AutoStart] Error auto-starting Twitch integration: %s", e)
            yt_target = self.settings_storage.load_string("youtube_target_channel", "")
            if yt_target:
                try:
                    self.logger.info("[AutoStart] Starting YouTube integration (target='%s')...", yt_target)
                    self._handle_youtube_connect(yt_target)
                except Exception as e:
                    self.logger.error("[AutoStart] Error auto-starting YouTube integration: %s", e)
            tk_target = self.settings_storage.load_string("tiktok_target_channel", "")
            if tk_target:
                try:
                    self.logger.info("[AutoStart] Starting TikTok integration (target='%s')...", tk_target)
                    self._handle_tiktok_connect(tk_target)
                except Exception as e:
                    self.logger.error("[AutoStart] Error auto-starting TikTok integration: %s", e)

    def _handle_navigation(self, view_name: str):
        self.logger.info("[User Action] Navigated to view: '%s'", view_name)
        target_view = self._get_or_create_view(view_name)
        if target_view:
            self.content_stack.setCurrentWidget(target_view)
            if view_name == "Dashboard":
                self._update_dashboard_metrics(force_db_query=True)
            elif view_name == "Settings":
                self._update_integrations_status_ui()
            elif view_name == "Triggers":
                self._fetch_api_rewards()

    def _get_or_create_view(self, view_name: str):
        if view_name in self._instantiated_views:
            return self._instantiated_views[view_name]

        view_widget = None
        if view_name == "Stream Info":
            self.view_schedule = ScheduleView(self.i18n, parent=self.content_stack)
            self.content_stack.addWidget(self.view_schedule)
            self.schedule_controller.attach_view(self.view_schedule)
            view_widget = self.view_schedule
        elif view_name == "Chat":
            self.view_chat = ChatView(self.i18n, parent=self.content_stack)
            self.content_stack.addWidget(self.view_chat)
            self.view_chat.chat_overlay_url = self.overlay_server.get_chat_overlay_url()
            self.chat_controller.attach_view(self.view_chat)
            view_widget = self.view_chat
        elif view_name == "Music":
            self.view_music = MusicView(self.i18n, music_overlay_url=self.overlay_server.get_music_overlay_url(), parent=self.content_stack)
            self.content_stack.addWidget(self.view_music)
            self.music_controller.attach_view(self.view_music)
            view_widget = self.view_music
        elif view_name == "Triggers":
            self.view_rewards = RewardsView(self.i18n, overlay_url=self.overlay_server.get_overlay_url(), parent=self.content_stack)
            self.content_stack.addWidget(self.view_rewards)
            self.view_rewards.refresh_rewards_requested.connect(self._fetch_api_rewards)
            self.rewards_controller.attach_view(self.view_rewards)
            self._fetch_api_rewards()
            view_widget = self.view_rewards
        elif view_name == "Comandos":
            self.view_commands = CommandView(self.i18n, parent=self.content_stack)
            self.content_stack.addWidget(self.view_commands)
            self.command_controller.attach_view(self.view_commands)
            view_widget = self.view_commands
        elif view_name == "Widgets":
            self.view_widgets = WidgetsView(
                self.i18n,
                shoutout_overlay_url=self.overlay_server.get_shoutout_overlay_url(),
                death_overlay_url=self.overlay_server.get_death_overlay_url(),
                score_overlay_url=self.overlay_server.get_score_overlay_url(),
                explosion_overlay_url=self.overlay_server.get_explosion_overlay_url(),
                combo_overlay_url=self.overlay_server.get_combo_overlay_url(),
                poll_overlay_url=self.overlay_server.get_poll_overlay_url(),
                pinned_overlay_url=self.overlay_server.get_pinned_overlay_url(),
                parent=self.content_stack
            )
            self.content_stack.addWidget(self.view_widgets)
            self.widget_controller.attach_view(self.view_widgets)
            view_widget = self.view_widgets
        elif view_name == "Spam Filters":
            self.view_spam = SpamView(self.i18n, parent=self.content_stack)
            self.content_stack.addWidget(self.view_spam)
            self.spam_controller.attach_view(self.view_spam)
            view_widget = self.view_spam
        elif view_name == "Timers":
            self.view_timers = TimersView(self.i18n, parent=self.content_stack)
            self.content_stack.addWidget(self.view_timers)
            self.timer_controller.attach_view(self.view_timers)
            view_widget = self.view_timers
        elif view_name == "Settings":
            self.view_settings = SettingsView(self.i18n, parent=self.content_stack)
            self.content_stack.addWidget(self.view_settings)
            self.view_settings.twitch_integration_clicked.connect(self._on_twitch_integration_button_clicked)
            self.view_settings.youtube_integration_clicked.connect(self._on_youtube_integration_button_clicked)
            self.view_settings.tiktok_integration_clicked.connect(self._on_tiktok_integration_button_clicked)
            self.settings_controller.attach_view(self.view_settings)
            self._update_integrations_status_ui()
            view_widget = self.view_settings
        elif view_name == "Developer":
            self.view_logs = LogView(self.i18n, parent=self.content_stack)
            self.content_stack.addWidget(self.view_logs)
            self.log_controller.attach_view(self.view_logs)
            view_widget = self.view_logs
        elif view_name == "Alerts":
            self.view_alerts = AlertsView(
                self.i18n,
                alerts_overlay_url=self.overlay_server.get_alerts_overlay_url(),
                parent=self.content_stack
            )
            self.content_stack.addWidget(self.view_alerts)
            self.alerts_controller.attach_view(self.view_alerts)
            view_widget = self.view_alerts

        if view_widget:
            self._instantiated_views[view_name] = view_widget
            if self.content_stack.indexOf(view_widget) == -1:
                self.content_stack.addWidget(view_widget)

        return view_widget

    def _schedule_view_prewarming(self):
        views_to_warm = [
            "Chat", "Alerts", "Widgets", "Settings", "Triggers",
            "Stream Info", "Comandos", "Timers", "Spam Filters",
            "Music", "Developer"
        ]
        self._prewarm_queue = deque(views_to_warm)
        QTimer.singleShot(750, self._prewarm_next_view)

    def _prewarm_next_view(self):
        if not hasattr(self, "_prewarm_queue") or not self._prewarm_queue or self._is_shutting_down:
            return
        view_name = self._prewarm_queue.popleft()
        if view_name not in self._instantiated_views:
            try:
                self.logger.debug("[Prewarm] Background warming view: '%s'", view_name)
                self._get_or_create_view(view_name)
            except Exception as e:
                self.logger.warning("[Prewarm] Error pre-warming view '%s': %s", view_name, e)

        if self._prewarm_queue and not self._is_shutting_down:
            QTimer.singleShot(150, self._prewarm_next_view)

    @Slot()
    def _restore_from_tray(self):
        self.logger.info("[User Action] Window restored from system tray")
        self.showNormal()
        self.activateWindow()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False):
                self.logger.info("[User Action] Window minimized to system tray")
                self.hide()
                self._notify_background()
        super().changeEvent(event)

    def closeEvent(self, event):
        if self._is_shutting_down:
            event.accept()
            return
            
        minimize_tray = self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False)
        self.logger.info("[User Action] Window close triggered (minimize_tray=%s)", minimize_tray)
        if minimize_tray:
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
                event.accept() 
                self._force_quit() 
            else:
                self.logger.info("[User Action] App exit cancelled by user")
                event.ignore()

    def nativeEvent(self, event_type, message):
        if sys.platform == "win32" and (event_type == b"windows_generic_MSG" or event_type == "windows_generic_MSG"):
            try:
                from ctypes import wintypes
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == 0x0319:
                    app_cmd = (msg.lParam >> 16) & ~0xF000
                    if app_cmd in (14, 46, 47):
                        if hasattr(self, "music_controller") and self.music_controller:
                            self.music_controller.handle_play_pause()
                        return True, 1
                    elif app_cmd == 11:
                        if hasattr(self, "music_controller") and self.music_controller:
                            self.music_controller.handle_skip()
                        return True, 1
                    elif app_cmd == 13:
                        if hasattr(self, "music_controller") and self.music_controller:
                            self.music_controller.handle_play_pause()
                        return True, 1
            except Exception:
                pass
        return super().nativeEvent(event_type, message)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_MediaTogglePlayPause, Qt.Key.Key_MediaPlay, Qt.Key.Key_MediaPause, Qt.Key.Key_Play, Qt.Key.Key_Pause):
            if hasattr(self, "music_controller") and self.music_controller:
                self.music_controller.handle_play_pause()
            event.accept()
            return
        elif key == Qt.Key.Key_MediaNext:
            if hasattr(self, "music_controller") and self.music_controller:
                self.music_controller.handle_skip()
            event.accept()
            return
        elif key == Qt.Key.Key_MediaStop:
            if hasattr(self, "music_controller") and self.music_controller:
                self.music_controller.handle_play_pause()
            event.accept()
            return
        super().keyPressEvent(event)

    def _setup_global_media_keys(self):
        if sys.platform != "win32":
            return
        enabled = self.settings_storage.load_bool("music_global_media_keys", True)
        if enabled:
            self._start_global_media_worker()
        if hasattr(self, "music_controller") and self.music_controller:
            self.music_controller.media_keys_state_changed.connect(self._on_media_keys_state_changed)

    def _start_global_media_worker(self):
        if sys.platform != "win32":
            return
        if self.global_media_worker and self.global_media_worker.isRunning():
            return
        self.global_media_worker = GlobalMediaWorker()
        self.global_media_worker.play_pause_pressed.connect(self.music_controller.handle_play_pause)
        self.global_media_worker.skip_pressed.connect(self.music_controller.handle_skip)
        self.global_media_worker.stop_pressed.connect(self.music_controller.handle_play_pause)
        self.global_media_worker.start()

    def _stop_global_media_worker(self):
        if self.global_media_worker and self.global_media_worker.isRunning():
            self.global_media_worker.stop()
            self.global_media_worker.wait(2000)
            self.global_media_worker = None

    def _on_media_keys_state_changed(self, enabled: bool):
        if enabled:
            self._start_global_media_worker()
        else:
            self._stop_global_media_worker()

    def _notify_background(self):
        self.tray_manager.showMessage(
            self.i18n.get("main.tray.bg_title"),
            self.i18n.get("main.tray.bg_desc"),
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def _force_quit(self):
        self.hide()
        self._cleanup()
        QApplication.quit()

    def _cleanup(self):
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        
        self.logger.info(self.i18n.get("main.logs.shutdown_init"))
        
        if hasattr(self, 'music_controller') and self.music_controller:
            self.music_controller.shutdown()

        self.logger.info(self.i18n.get("main.logs.shutdown_tts_overlay"))
        self.container.shutdown()

        self._stop_all_workers()

        if hasattr(self.container, 'db_manager') and self.container.db_manager:
            self.container.db_manager.cleanup()

        self.logger.info(self.i18n.get("main.logs.shutdown_complete"))

    def _stop_workers_parallel(self, worker_map: list):
        active_workers = []
        for name, instance in worker_map:
            if instance:
                try:
                    if instance.isRunning():
                        active_workers.append((name, instance))
                    else:
                        try:
                            instance.deleteLater()
                        except RuntimeError:
                            pass
                except RuntimeError:
                    pass

        if not active_workers:
            return

        stop_template = self.i18n.get("main.logs.worker_stopping")
        for name, instance in active_workers:
            try:
                self.logger.info(stop_template.replace("{worker}", name))
                if hasattr(instance, 'stop'):
                    instance.stop()
                if hasattr(instance, 'requestInterruption'):
                    instance.requestInterruption()
                if hasattr(instance, 'quit'):
                    instance.quit()
            except RuntimeError:
                pass

        stuck_template = self.i18n.get("main.logs.worker_stuck")
        stopped_template = self.i18n.get("main.logs.worker_stopped")
        for name, instance in active_workers:
            try:
                if instance.wait(2000):
                    self.logger.info(stopped_template.replace("{worker}", name))
                else:
                    self.logger.warning("[Shutdown] Worker '%s' wait timed out", name)
                instance.deleteLater()
            except RuntimeError:
                pass

    def _stop_kick_connection_workers(self):
        worker_map = [
            ("Worker_Kick_Chat_Socket", getattr(self, 'kick_chat_worker', None)),
            ("Worker_Kick_Auth", getattr(self, 'kick_auth_worker', None)),
            ("Worker_Fetch_Rewards", getattr(self, 'fetch_rewards_worker', None)),
            ("Worker_Timers", getattr(self, 'timers_worker', None)),
        ]
        self._stop_workers_parallel(worker_map)
        self.kick_chat_worker = None
        self.kick_auth_worker = None
        self.fetch_rewards_worker = None
        self.timers_worker = None

    def _stop_twitch_connection_workers(self):
        worker_map = [
            ("Worker_Twitch_Chat_Socket", getattr(self, 'twitch_chat_worker', None)),
            ("Worker_Twitch_Auth", getattr(self, 'twitch_auth_worker', None)),
            ("Worker_Twitch_Reward_EventSub", getattr(self, 'twitch_reward_worker', None)),
            ("Worker_Fetch_Twitch_Rewards", getattr(self, 'fetch_twitch_rewards_worker', None)),
        ]
        self._stop_workers_parallel(worker_map)
        self.twitch_chat_worker = None
        self.twitch_auth_worker = None
        self.twitch_reward_worker = None
        self.fetch_twitch_rewards_worker = None

    def _stop_all_workers(self):
        worker_map = [
            ("Worker_Kick_Chat_Socket", getattr(self, 'kick_chat_worker', None)),
            ("Worker_Kick_Auth", getattr(self, 'kick_auth_worker', None)),
            ("Worker_Fetch_Rewards", getattr(self, 'fetch_rewards_worker', None)),
            ("Worker_Timers", getattr(self, 'timers_worker', None)),
            ("Worker_Twitch_Chat_Socket", getattr(self, 'twitch_chat_worker', None)),
            ("Worker_Twitch_Auth", getattr(self, 'twitch_auth_worker', None)),
            ("Worker_Twitch_Reward_EventSub", getattr(self, 'twitch_reward_worker', None)),
            ("Worker_Fetch_Twitch_Rewards", getattr(self, 'fetch_twitch_rewards_worker', None)),
            ("Worker_YouTube_Chat", getattr(self, 'youtube_chat_worker', None)),
            ("Worker_TikTok_Chat", getattr(self, 'tiktok_chat_worker', None)),
            ("Worker_Stream_Schedule", getattr(self, 'schedule_worker', None)),
            ("Worker_Global_Media_Keys", getattr(self, 'global_media_worker', None)),
        ]

        self._stop_workers_parallel(worker_map)
        self.kick_chat_worker = None
        self.kick_auth_worker = None
        self.fetch_rewards_worker = None
        self.timers_worker = None
        self.twitch_chat_worker = None
        self.twitch_auth_worker = None
        self.twitch_reward_worker = None
        self.youtube_chat_worker = None
        self.tiktok_chat_worker = None
        self.schedule_worker = None
        self.global_media_worker = None
        if hasattr(self, "chat_service") and self.chat_service and hasattr(self.chat_service, "shutdown"):
            try:
                self.chat_service.shutdown()
            except Exception:
                pass

    @staticmethod
    def _is_worker_running(worker) -> bool:
        if worker is None:
            return False
        try:
            return bool(worker.isRunning())
        except (RuntimeError, AttributeError):
            return False

    @Slot()
    def _handle_auth_process(self, force: bool = False):
        if self._is_worker_running(getattr(self, "twitch_auth_worker", None)):
            self.toast.show_toast(
                title=self.container.i18n.get("main.toast.auth_in_progress_title"),
                message=self.container.i18n.get("main.toast.auth_in_progress_msg"),
                state="warning"
            )
            return

        self._stop_kick_connection_workers()
        self.dashboard_controller.handle_connecting_state()

        self.kick_auth_worker = KickAuthWorker(self.i18n, self.kick_auth_manager, force=force)
        self.kick_auth_worker.auth_success.connect(self._on_auth_success)
        self.kick_auth_worker.auth_error.connect(self.dashboard_controller.handle_error_state)
        self.kick_auth_worker.finished.connect(lambda: setattr(self, 'kick_auth_worker', None))
        self.kick_auth_worker.finished.connect(self.kick_auth_worker.deleteLater)
        self.kick_auth_worker.start()

    def _on_auth_success(self, tokens):
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

        self.kick_chat_worker = KickChatWorker(self.i18n, self.kick_api_client, KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY)
        self.kick_chat_worker.connection_success.connect(self._on_web_socket_connected)
        self.kick_chat_worker.message_received.connect(self._route_incoming_message)
        self.kick_chat_worker.poll_updated.connect(self._on_poll_updated)
        self.kick_chat_worker.poll_deleted.connect(self._on_poll_deleted)
        self.kick_chat_worker.pinned_created.connect(self._on_pinned_created)
        self.kick_chat_worker.pinned_deleted.connect(self._on_pinned_deleted)
        self.kick_chat_worker.alert_received.connect(self._handle_incoming_alert)
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
                except Exception as e:
                    err_template = self.i18n.get("main.logs.api_error_setup")
                    self.logger.error(err_template.replace("{error}", str(e)))
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
        return f'<span style="color: #00e701;">{texto_canje}</span>'

    def _on_reward_redeemed(self, user: str, reward_name: str, message: str, platform: str = "kick"):
        recents = getattr(self, "_recent_reward_redemptions", None)
        if recents is not None:
            dedup_key = f"{platform}:{user.lower()}:{reward_name.lower()}:{int(time.time() / 8)}"
            if dedup_key in recents:
                self.logger.debug("[Reward] Ignorando canje duplicado: %s", dedup_key)
                return
            recents.append(dedup_key)

        self.logger.info("[Reward] Canje procesado: usuario='%s', recompensa='%s' (Plataforma: %s)", user, reward_name, platform.capitalize())
        toast_template = self.i18n.get("main.toasts.reward_msg")
        self.toast.show_toast(
            title=self.i18n.get("main.toasts.reward_title"), 
            message=toast_template.replace("{user}", user).replace("{reward_name}", reward_name), 
            state="success"
        )
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        msg_sistema = self._format_reward_message(reward_name)
        tag = self.i18n.get("main.chat.points_tag")
        if self.view_chat is not None:
            self.view_chat.append_message(f"[{tag}] {user}", msg_sistema, COLOR_GREEN, timestamp=current_time, is_html=True, platform=platform)
        
        mappings = self.rewards_service.get_mappings()
        config = mappings.get(reward_name)
        if config and config.get("platform", "kick") == platform:
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
            self.logger.debug(no_rewards_template.replace("{reward_name}", reward_name))

        settings = self.chat_service.get_settings()
        if settings.get("enabled", False) and message:
            dto = ChatMessageDTO(user, message, [], "", "", 0, timestamp=current_time, platform=platform)
            self.chat_controller.process_message(dto)

    def _handle_incoming_alert(self, alert_event):
        if hasattr(self.container, "alert_service") and self.container.alert_service:
            self.container.alert_service.process_event(alert_event)

    def _start_timers_worker(self, channel_slug: str):
        self._stop_workers_parallel([("Worker_Timers", getattr(self, 'timers_worker', None))])
        
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

        self._stop_twitch_connection_workers()
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
        log_msg = self.container.i18n.get("logs.main_window.twitch_auth_error").replace("{error}", str(err))
        logger.error(f"[Twitch Auth Error] {log_msg}")
        if getattr(self, "_is_window_closing", False):
            return
        err_title = self.container.i18n.get("main.toast.twitch_auth_error_title")
        self.toast.show_toast(title=err_title, message=str(err), state="danger")

    def _on_twitch_auth_success(self, tokens):
        self.twitch_auth_worker = None
        logger.info("[Twitch Auth] Success callback received.")
        try:
            twitch_api = TwitchAPIClient(auth_provider=self.container.twitch_auth_manager, client_id=TWITCH_CLIENT_ID, i18n=self.container.i18n)
            self.spam_service.twitch_api = twitch_api
            self._start_twitch_chat_worker(channel="")
            self._evaluate_all_scopes()
        except Exception as e:
            logger.error("[Twitch Auth] Error initializing Twitch session: %s", e)
            self._twitch_connected = False
            self._twitch_channel = ""
            self._update_integrations_status_ui()
            if hasattr(self, "toast") and self.toast and not getattr(self, "_is_window_closing", False):
                err_title = self.container.i18n.get("main.toast.twitch_auth_error_title")
                self.toast.show_toast(title=err_title, message=str(e), state="danger")

    def _start_twitch_chat_worker(self, channel: str):
        if hasattr(self, 'twitch_chat_worker') and self.twitch_chat_worker:
            self.twitch_chat_worker.stop()
            self.twitch_chat_worker = None

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
        if hasattr(self, "twitch_chat_worker") and self.twitch_chat_worker:
            self.twitch_chat_worker.stop()
            self.twitch_chat_worker = None
        self._update_integrations_status_ui()
        if hasattr(self, "toast") and self.toast and not getattr(self, "_is_window_closing", False):
            self.toast.show_toast(
                title=self.container.i18n.get("common.status.error"),
                message=error_msg,
                state="danger"
            )

    def _on_twitch_connected(self, user_data=None):
        if isinstance(user_data, dict):
            username = user_data.get("username", "")
            broadcaster_id = user_data.get("broadcaster_id", "")
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
            if hasattr(self, 'twitch_reward_worker') and self.twitch_reward_worker:
                self.twitch_reward_worker.stop()
                self.twitch_reward_worker = None

            self.twitch_reward_worker = TwitchRewardWorker(
                self.container.i18n,
                self.container.twitch_auth_manager,
                TWITCH_CLIENT_ID,
                broadcaster_id
            )
            self.twitch_reward_worker.reward_redeemed.connect(lambda u, r, m: self._on_reward_redeemed(u, r, m, platform="twitch"))
            self.twitch_reward_worker.alert_received.connect(self._handle_incoming_alert)
            self.twitch_reward_worker.start()
            self._fetch_twitch_rewards(broadcaster_id)
        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            if isinstance(user_data, dict) and user_data.get("followers") is not None and user_data.get("followers") > 0:
                self.dashboard_controller.set_channel_profile("twitch", user_data)
            elif self.spam_service.twitch_api and broadcaster_id:
                try:
                    full_info = self.spam_service.twitch_api.fetch_full_channel_info(broadcaster_id)
                    self.dashboard_controller.set_channel_profile("twitch", full_info)
                except Exception as e:
                    logger.warning("[Twitch] Could not refresh full channel info: %s", e)
            elif isinstance(user_data, dict):
                self.dashboard_controller.set_channel_profile("twitch", user_data)

        self._evaluate_all_scopes()

        title = self.container.i18n.get("main.toast.twitch_connected_title")
        msg = self.container.i18n.get("main.toast.twitch_connected_msg").replace("{username}", username)
        self.toast.show_toast(
            title=title,
            message=msg,
            state="success"
        )

    @Slot()
    def _fetch_twitch_rewards(self, broadcaster_id: str = ""):
        b_id = broadcaster_id or getattr(self.spam_service, "twitch_broadcaster_id", "")
        if not b_id and self.container.twitch_auth_manager.is_authenticated():
            try:
                twitch_api = self.spam_service.twitch_api or TwitchAPIClient(self.container.twitch_auth_manager, TWITCH_CLIENT_ID, i18n=self.container.i18n)
                user_info = twitch_api.fetch_user_data()
                b_id = user_info.get("broadcaster_id", "")
                if b_id:
                    self.spam_service.twitch_broadcaster_id = b_id
            except Exception as e:
                logger.error("[Main] Error resolving broadcaster_id for Twitch rewards: %s", e)

        if not b_id or not self.container.twitch_auth_manager.is_authenticated():
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
        except Exception as e:
            logger.error("[Main] Error launching Twitch rewards fetcher: %s", e)

    def _on_twitch_socket_lost(self):
        self._twitch_connected = False
        self._update_integrations_status_ui()

    def _on_twitch_socket_restored(self):
        self._twitch_connected = True
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
        self.logger.info("[User Action] Twitch account unlinked successfully")
        self._stop_twitch_connection_workers()
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
        youtube_connected = getattr(self, "_youtube_connected", False)
        youtube_channel = getattr(self, "_youtube_channel", "")
        tiktok_connected = getattr(self, "_tiktok_connected", False)
        tiktok_channel = getattr(self, "_tiktok_channel", "")

        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            self.dashboard_controller.set_kick_status(
                connected=kick_connected,
                channel=kick_user,
                msg_count=self.session_platform_messages.get("kick", 0)
            )
            self.dashboard_controller.set_twitch_status(
                connected=twitch_connected,
                channel=twitch_channel,
                msg_count=self.session_platform_messages.get("twitch", 0)
            )
            self.dashboard_controller.set_youtube_status(
                connected=youtube_connected,
                channel=youtube_channel,
                msg_count=self.session_platform_messages.get("youtube", 0)
            )
            self.dashboard_controller.set_tiktok_status(
                connected=tiktok_connected,
                channel=tiktok_channel,
                msg_count=self.session_platform_messages.get("tiktok", 0)
            )

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

        conn_dict = self.get_connected_platforms()
        if hasattr(self, "view_commands") and self.view_commands and hasattr(self.view_commands, "set_connected_platforms"):
            self.view_commands.set_connected_platforms(conn_dict)
        if hasattr(self, "view_schedule") and self.view_schedule and hasattr(self.view_schedule, "set_connected_platforms"):
            self.view_schedule.set_connected_platforms(conn_dict)
        if hasattr(self, "view_spam") and self.view_spam and hasattr(self.view_spam, "set_connected_platforms"):
            self.view_spam.set_connected_platforms(conn_dict)
        if hasattr(self, "view_rewards") and self.view_rewards and hasattr(self.view_rewards, "set_connected_platforms"):
            self.view_rewards.set_connected_platforms(conn_dict)
        if hasattr(self, "view_timers") and self.view_timers and hasattr(self.view_timers, "set_connected_platforms"):
            self.view_timers.set_connected_platforms(conn_dict)

    def get_connected_platforms(self) -> dict[str, bool]:
        kick_auth = self.kick_auth_manager.is_authenticated() if hasattr(self, "kick_auth_manager") and self.kick_auth_manager else False
        twitch_auth = self.container.twitch_auth_manager.is_authenticated() if hasattr(self.container, "twitch_auth_manager") and self.container.twitch_auth_manager else False
        return {
            "kick": kick_auth or getattr(self, "_kick_connected", False),
            "twitch": twitch_auth or getattr(self, "_twitch_connected", False),
            "youtube": getattr(self, "_youtube_connected", False),
            "tiktok": getattr(self, "_tiktok_connected", False),
        }

    @Slot()
    def _on_youtube_integration_button_clicked(self):
        if getattr(self, "_youtube_connected", False):
            self.logger.info("[User Action] Requested disconnecting YouTube Live")
            dialog = ModernConfirmDialog(
                self.i18n,
                self,
                title_text=self.i18n.get("dialogs.unlink_youtube.title"),
                body_text=self.i18n.get("dialogs.unlink_youtube.desc")
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                self._handle_youtube_disconnect()
        else:
            saved_target = self.settings_storage.load_string("youtube_target_channel", "")
            dialog = YouTubeConnectDialog(self.i18n, initial_target=saved_target, parent=self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                if hasattr(dialog, "is_cleared") and dialog.is_cleared():
                    self.settings_storage.save_string("youtube_target_channel", "")
                    self._handle_youtube_disconnect()
                else:
                    target = dialog.get_target()
                    if target:
                        self._handle_youtube_connect(target)
                    else:
                        self.settings_storage.save_string("youtube_target_channel", "")
                        self._handle_youtube_disconnect()

    def _handle_youtube_connect(self, target: str):
        if hasattr(self, "youtube_chat_worker") and self.youtube_chat_worker and self.youtube_chat_worker.isRunning():
            self.youtube_chat_worker.stop()
            self.youtube_chat_worker.wait(1000)

        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            self.dashboard_controller.set_youtube_status(connected=False, connecting=True)

        self.youtube_chat_worker = YouTubeChatWorker(
            target_channel=target,
            i18n=self.container.i18n
        )
        self.youtube_chat_worker.connection_success.connect(self._on_youtube_connected)
        self.youtube_chat_worker.connection_lost.connect(self._on_youtube_disconnected)
        self.youtube_chat_worker.error_occurred.connect(self._on_youtube_error)
        self.youtube_chat_worker.message_received.connect(self._route_incoming_message)
        self.youtube_chat_worker.start()

    def _on_youtube_connected(self, stream_info: dict):
        self._youtube_connected = True
        ch_name = stream_info.get("channel_name", "") or stream_info.get("title", "") or stream_info.get("channel", "") or "YouTube Live"
        self._youtube_channel = ch_name
        target = stream_info.get("channel", "")
        if target:
            self.settings_storage.save_string("youtube_target_channel", target)
        self._update_integrations_status_ui()
        title = self.container.i18n.get("main.toast.youtube_connected_title")
        msg = self.container.i18n.get("main.toast.youtube_connected_msg").replace("{target}", ch_name)
        self.toast.show_toast(title=title, message=msg, state="success")

    def _on_youtube_disconnected(self):
        self._youtube_connected = False
        self._update_integrations_status_ui()

    def _on_youtube_error(self, error_msg: str):
        self._youtube_connected = False
        if hasattr(self, "youtube_chat_worker") and self.youtube_chat_worker:
            self.youtube_chat_worker.stop()
            self.youtube_chat_worker = None
        self._update_integrations_status_ui()
        self.toast.show_toast(
            title=self.container.i18n.get("common.status.error"),
            message=error_msg,
            state="danger"
        )

    @Slot()
    def _handle_youtube_disconnect(self):
        self.logger.info("[User Action] YouTube Live disconnected successfully")
        if hasattr(self, "youtube_chat_worker") and self.youtube_chat_worker:
            self.youtube_chat_worker.stop()
            self.youtube_chat_worker.wait(1000)
            self.youtube_chat_worker = None
        self._youtube_connected = False
        self._youtube_channel = ""
        self.settings_storage.save_string("youtube_target_channel", "")
        self._update_integrations_status_ui()
        title_disc = self.container.i18n.get("main.toast.youtube_disconnected_title")
        msg_disc = self.container.i18n.get("main.toast.youtube_disconnected_msg")
        self.toast.show_toast(title=title_disc, message=msg_disc, state="info")

    @Slot()
    def _on_tiktok_integration_button_clicked(self):
        if getattr(self, "_tiktok_connected", False):
            self.logger.info("[User Action] Requested disconnecting TikTok Live")
            dialog = ModernConfirmDialog(
                self.i18n,
                self,
                title_text=self.i18n.get("dialogs.unlink_tiktok.title"),
                body_text=self.i18n.get("dialogs.unlink_tiktok.desc")
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                self._handle_tiktok_disconnect()
        else:
            saved_target = self.settings_storage.load_string("tiktok_target_channel", "")
            dialog = TikTokConnectDialog(self.i18n, initial_target=saved_target, parent=self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                if hasattr(dialog, "is_cleared") and dialog.is_cleared():
                    self.settings_storage.save_string("tiktok_target_channel", "")
                    self._handle_tiktok_disconnect()
                else:
                    target = dialog.get_target()
                    if target:
                        self._handle_tiktok_connect(target)
                    else:
                        self.settings_storage.save_string("tiktok_target_channel", "")
                        self._handle_tiktok_disconnect()

    def _handle_tiktok_connect(self, target: str):
        clean_target = target.strip().lstrip("@")
        if not clean_target:
            return

        if hasattr(self, "tiktok_chat_worker") and self.tiktok_chat_worker and self.tiktok_chat_worker.isRunning():
            self.tiktok_chat_worker.stop()
            self.tiktok_chat_worker.wait(1000)

        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            self.dashboard_controller.set_tiktok_status(connected=False, connecting=True)

        self.tiktok_chat_worker = TikTokChatWorker(
            target_channel=clean_target,
            i18n=self.container.i18n
        )
        self.tiktok_chat_worker.connection_success.connect(self._on_tiktok_connected)
        self.tiktok_chat_worker.connection_lost.connect(self._on_tiktok_disconnected)
        self.tiktok_chat_worker.error_occurred.connect(self._on_tiktok_error)
        self.tiktok_chat_worker.message_received.connect(self._route_incoming_message)
        self.tiktok_chat_worker.start()

    def _on_tiktok_connected(self, stream_info: dict):
        self._tiktok_connected = True
        unique_id = stream_info.get("unique_id", "") or stream_info.get("channel", "") or "TikTok Live"
        self._tiktok_channel = unique_id
        if unique_id:
            self.settings_storage.save_string("tiktok_target_channel", unique_id)
        self._update_integrations_status_ui()
        title = self.container.i18n.get("main.toast.tiktok_connected_title")
        msg = self.container.i18n.get("main.toast.tiktok_connected_msg").replace("{target}", unique_id)
        self.toast.show_toast(title=title, message=msg, state="success")

    def _on_tiktok_disconnected(self):
        self._tiktok_connected = False
        self._update_integrations_status_ui()

    def _on_tiktok_error(self, error_msg: str):
        self._tiktok_connected = False
        if hasattr(self, "tiktok_chat_worker") and self.tiktok_chat_worker:
            self.tiktok_chat_worker.stop()
            self.tiktok_chat_worker = None
        self._update_integrations_status_ui()
        self.toast.show_toast(
            title=self.container.i18n.get("common.status.error"),
            message=error_msg,
            state="danger"
        )

    @Slot()
    def _handle_tiktok_disconnect(self):
        self.logger.info("[User Action] TikTok Live disconnected successfully")
        if hasattr(self, "tiktok_chat_worker") and self.tiktok_chat_worker:
            self.tiktok_chat_worker.stop()
            self.tiktok_chat_worker.wait(1000)
            self.tiktok_chat_worker = None
        self._tiktok_connected = False
        self._tiktok_channel = ""
        self.settings_storage.save_string("tiktok_target_channel", "")
        self._update_integrations_status_ui()
        title_disc = self.container.i18n.get("main.toast.tiktok_disconnected_title")
        msg_disc = self.container.i18n.get("main.toast.tiktok_disconnected_msg")
        self.toast.show_toast(title=title_disc, message=msg_disc, state="info")

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
        self.logger.info("[User Action] Requested renewal of Kick permissions")
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
                self.logger.info("[User Action] Kick account unlinked successfully")
                self.toast.show_toast(
                    title=self.i18n.get("main.toast.kick_disconnected_title"),
                    message=self.i18n.get("main.toast.kick_disconnected_msg"),
                    state="info"
                )
                self._stop_kick_connection_workers()
                self.kick_chat_worker = None
                self.timers_worker = None

                self.kick_auth_manager.logout()
                self._kick_connected = False
                self._kick_username = ""
                if hasattr(self, "dashboard_controller") and self.dashboard_controller:
                    self.dashboard_controller.clear_channel_profile("kick")
                if hasattr(self, "rewards_controller") and self.rewards_controller:
                    self.rewards_controller.clear_platform_rewards("kick")
                self._refresh_sidebar_profile()
                self._update_integrations_status_ui()
                self._evaluate_all_scopes()
        else:
            self._handle_auth_process()

    def _start_schedule_worker(self):
        current_worker = getattr(self, "schedule_worker", None)
        if current_worker is None or not current_worker.isRunning():
            self.schedule_worker = ScheduleWorker(self.schedule_service)
            self.schedule_worker.schedule_triggered.connect(self._on_schedule_triggered)
            self.schedule_worker.start()

    def _on_schedule_triggered(self, schedule: dict, result: dict):
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

    def _route_incoming_message(self, user_or_dto, msg: str = None, badges: list = None, color: str = "", msg_id: str = "", sender_id: int = 0):
        self._increment_metric("messages_processed")
        current_time = datetime.now().strftime("%H:%M:%S")
        if isinstance(user_or_dto, ChatMessageDTO):
            dto = user_or_dto
            if not dto.timestamp:
                dto.timestamp = current_time
            platform = getattr(dto, "platform", "kick") or "kick"
        else:
            dto = ChatMessageDTO(user_or_dto, msg, badges or [], color, msg_id, sender_id, timestamp=current_time)
            platform = "kick"

        if hasattr(self, "session_platform_messages") and platform in self.session_platform_messages:
            self.session_platform_messages[platform] += 1
            if hasattr(self, "dashboard_controller") and self.dashboard_controller:
                self.dashboard_controller.update_platform_messages(
                    kick=self.session_platform_messages["kick"],
                    twitch=self.session_platform_messages["twitch"],
                    youtube=self.session_platform_messages["youtube"],
                    tiktok=self.session_platform_messages["tiktok"]
                )

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
    def _handle_autostart_change(self, enabled: bool):
        self.logger.info("[User Action] Toggled dashboard autostart setting: enabled=%s", enabled)
        self.settings_storage.save_bool(self.SETTING_AUTOSTART, enabled)


    @Slot(bool)
    def _handle_tray_tts_toggle(self, enabled: bool):
        settings = self.chat_service.get_settings()
        settings["enabled"] = enabled
        self.chat_service.save_settings(settings)
        self.chat_controller.load_initial_data()
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

    @Slot(bool)
    def _handle_tray_tts_use_command_toggle(self, enabled: bool):
        settings = self.chat_service.get_settings()
        settings["use_command"] = enabled
        self.chat_service.save_settings(settings)
        self.chat_controller.load_initial_data()

    @Slot(bool)
    def _handle_tray_tts_voice_type_change(self, is_web: bool):
        settings = self.chat_service.get_settings()
        settings["provider"] = "web" if is_web else "local"
        self.chat_service.save_settings(settings)
        self.chat_controller.load_initial_data()

    @Slot(bool)
    def _handle_chat_tts_state_changed(self, enabled: bool):
        settings = self.chat_service.get_settings()
        self.tray_manager.set_tts_state(enabled)
        self.tray_manager.set_tts_use_command_state(settings.get("use_command", False))
        self.tray_manager.set_tts_voice_type_state(settings.get("provider", "local") == "web")

    @Slot(int)
    def _apply_dynamic_theme(self, base_size: int, immediate: bool = True):
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_global_qss(base_size))

    @Slot(object)
    def _on_silent_update_found(self, info):
        version = ""
        if isinstance(info, dict):
            version = info.get("version", "")
        elif isinstance(info, str):
            version = info
        self.sidebar.set_update_available(True, version=version)

    @Slot()
    def handle_update_check(self):
        self.update_controller.show_update_dialog(self, self.i18n, on_restart_callback=self._force_quit)

    def _increment_metric(self, name: str):
        if hasattr(self, 'session_metrics') and name in self.session_metrics:
            self.session_metrics[name] += 1
        self._update_dashboard_metrics(force_db_query=False)

    @Slot()
    def _update_dashboard_metrics(self, force_db_query=False):
        if self._cached_total_usages is None or self._cached_active_timers is None or force_db_query:
            try:
                analytics = self.container.db_manager.get_dashboard_analytics_summary()
                self._cached_total_usages = analytics.get("total_command_usages", 0)
                self._cached_active_timers = analytics.get("active_timers", 0)
                if hasattr(self, "dashboard_controller") and self.dashboard_controller:
                    self.dashboard_controller.update_analytics_summary(analytics)
            except Exception as e:
                self.logger.error(f"[Metrics] Error reading analytics: {e}")
                self._cached_total_usages = self._cached_total_usages or 0
                self._cached_active_timers = self._cached_active_timers or 0

        self.view_dashboard.update_session_metrics(
            msg_count=self.session_metrics["messages_processed"],
            cmd_count=self._cached_total_usages,
            timer_count=self._cached_active_timers,
            spam_count=self.session_metrics["spam_blocked"]
        )

        if hasattr(self, "schedule_service") and hasattr(self, "dashboard_controller"):
            next_sched = self.schedule_service.get_next_schedule_text()
            self.dashboard_controller.update_next_schedule(next_sched)
