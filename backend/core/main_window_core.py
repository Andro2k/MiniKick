# backend\core\main_window_core.py

import html
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, 
    QSystemTrayIcon, QApplication
)
from PySide6.QtCore import Slot, QEvent, QTimer

from backend.core.app_container_core import AppContainer
from backend.core.app_logger_core import setup_application_logging
from backend.services import (
    ChatMessageDTO, RewardsService, ChatService, CommandService, AvatarService,
    LogService, SettingsService, NetworkService, SpamService, TimerService
)
from backend.controllers import (
    RewardsController, ChatController, CommandController, DashboardController,
    TimerController, LogController, MusicController, SettingsController,
    SpamController, UpdateController, NetworkController, WidgetController,
    ScheduleController
)
from backend.providers import KickAPIClient
from backend.providers.chat.twitch_client import TwitchAPIClient
from backend.workers import (
    AuthWorker, TwitchAuthWorker, ChatWorker, TwitchChatWorker,
    FetchRewardsWorker, RewardWorker, TimerWorker, ScheduleWorker
)
from frontend.common.theme import COLOR_GREEN, get_global_qss
from frontend.navigation.sidebar_component import Sidebar
from frontend.navigation.toast_component import ToastManager
from frontend.navigation.tray_menu_component import SystemTrayManager
from frontend.views import (
    RewardsView, CommandView, DashboardView, TimersView, ChatView,
    LogView, MusicView, SettingsView, SpamView, NetworkView, WidgetsView,
    ScheduleView
)
from frontend.dialogs import ModernConfirmDialog

try:
    from backend.config.api_keys import KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY, TWITCH_CLIENT_ID
except ImportError:
    KICK_PUSHER_CLUSTER = "us2"
    KICK_PUSHER_KEY = "32cbd69e4b950bf97679"
    TWITCH_CLIENT_ID = ""

logger = logging.getLogger("minikick.core")

class MainWindowCore(QMainWindow):
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

        ("Network Status", "access-point.svg", "bottom"),
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
        
        self.container = AppContainer(self)
        self.settings_storage = self.container.settings_storage 
        self.rewards_storage = self.container.rewards_storage
        self.commands_storage = self.container.commands_storage
        self.spam_storage = self.container.spam_storage
        self.timers_storage = self.container.timers_storage
        self.backup_service = self.container.backup_service
        self.i18n = self.container.i18n
        self.auth_manager = self.container.auth_manager
        self.tts_manager = self.container.tts_manager
        self.overlay_server = self.container.overlay_server
        
        title_template = self.i18n.get("main.window.title")
        self.setWindowTitle(title_template.replace("{version}", app_version))
        
        self.chat_worker = None
        self.reward_worker = None
        self.auth_worker = None
        self.fetch_rewards_worker = None
        self.timers_worker = None
        self.schedule_worker = None
        self.twitch_chat_worker = None
        self.twitch_auth_worker = None

        self._cached_total_usages = None
        self._cached_active_timers = None

        self.logger, self.q_log_handler = setup_application_logging()  
        self.toast = ToastManager(self)
        self._setup_ui()
        self._setup_tray() 
        
        self.update_controller = UpdateController(self.updater_manager)
        self.update_controller.update_found_silent.connect(
            lambda: self.sidebar.set_update_available(True)
        )
        self.update_controller.check_updates_silently()
        
        self._connect_signals()     
        self._load_settings_into_ui()
        self.setUpdatesEnabled(True)

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
        self.log_service = LogService(log_storage=self.container.log_storage)
        self.network_service = NetworkService(overlay_port=self.overlay_server.port)
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
        self.view_network = None

        self._instantiated_views = {"Dashboard": self.view_dashboard}

        self.dashboard_controller = DashboardController(
            view=self.view_dashboard, 
            avatar_service=self.avatar_service
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
            auth_manager=self.auth_manager
        )
        self.command_controller = CommandController(
            None, 
            self.command_service,
            toast_manager=self.toast
        )
        self.spam_controller = SpamController(
            None, 
            self.spam_service,
            toast_manager=self.toast
        )
        self.timer_controller = TimerController(
            None,
            self.timer_service,
            toast_manager=self.toast
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
        self.network_controller = NetworkController(
            view=None, 
            service=self.network_service
        )
        self.schedule_controller = ScheduleController(
            view=None,
            service=self.schedule_service,
            toast_manager=self.toast,
            i18n=self.i18n
        )
        self._start_schedule_worker()
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
        self.dashboard_controller.auto_start_toggled.connect(self._handle_autostart_change)
        self.dashboard_controller.reauth_requested.connect(self._force_reauth)
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
        self.settings_controller.notification_requested.connect(lambda title, msg: self.tray_manager.showMessage(title, msg))
        self.settings_controller.backup_restored.connect(self._load_settings_into_ui)
        self.q_log_handler.emitter.log_received.connect(self.log_controller.process_incoming_log)
        self.avatar_service.avatar_downloaded.connect(self.sidebar.update_profile_avatar)

    def _load_settings_into_ui(self):
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
        if autostart_enabled:
            self._handle_auth_process()
            twitch_tokens = self.container.twitch_token_storage.load()
            if twitch_tokens and twitch_tokens.get("access_token"):
                self._on_twitch_auth_success(twitch_tokens)

    def _handle_navigation(self, view_name: str):
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
            self.view_schedule = ScheduleView(self.i18n, parent=self)
            self.schedule_controller.attach_view(self.view_schedule)
            view_widget = self.view_schedule
        elif view_name == "Chat":
            self.view_chat = ChatView(self.i18n, parent=self)
            self.view_chat.chat_overlay_url = self.overlay_server.get_chat_overlay_url()
            self.chat_controller.attach_view(self.view_chat)
            view_widget = self.view_chat
        elif view_name == "Music":
            self.view_music = MusicView(self.i18n, music_overlay_url=self.overlay_server.get_music_overlay_url(), parent=self)
            self.music_controller.attach_view(self.view_music)
            view_widget = self.view_music
        elif view_name == "Triggers":
            self.view_rewards = RewardsView(self.i18n, overlay_url=self.overlay_server.get_overlay_url(), parent=self)
            self.view_rewards.refresh_rewards_requested.connect(self._fetch_api_rewards)
            self.rewards_controller.attach_view(self.view_rewards)
            self._fetch_api_rewards()
            view_widget = self.view_rewards
        elif view_name == "Comandos":
            self.view_commands = CommandView(self.i18n, parent=self)
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
                parent=self
            )
            self.widget_controller.attach_view(self.view_widgets)
            view_widget = self.view_widgets
        elif view_name == "Spam Filters":
            self.view_spam = SpamView(self.i18n, parent=self)
            self.spam_controller.attach_view(self.view_spam)
            view_widget = self.view_spam
        elif view_name == "Timers":
            self.view_timers = TimersView(self.i18n, parent=self)
            self.timer_controller.attach_view(self.view_timers)
            view_widget = self.view_timers
        elif view_name == "Settings":
            self.view_settings = SettingsView(self.i18n, parent=self)
            self.view_settings.twitch_integration_clicked.connect(self._on_twitch_integration_button_clicked)
            self.settings_controller.attach_view(self.view_settings)
            self._update_integrations_status_ui()
            view_widget = self.view_settings
        elif view_name == "Developer":
            self.view_logs = LogView(self.i18n, parent=self)
            self.log_controller.attach_view(self.view_logs)
            view_widget = self.view_logs
        elif view_name == "Network Status":
            self.view_network = NetworkView(self.i18n, parent=self)
            self.network_controller.attach_view(self.view_network)
            view_widget = self.view_network

        if view_widget:
            self._instantiated_views[view_name] = view_widget
            self.content_stack.addWidget(view_widget)

        return view_widget

    @Slot()
    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False):
                self.hide()
                self._notify_background()
        super().changeEvent(event)

    def closeEvent(self, event):
        if self._is_shutting_down:
            event.accept()
            return
            
        if self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False):
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
                self.hide()
                event.accept() 
                self._force_quit() 
            else:
                event.ignore()

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
                elif hasattr(instance, 'quit'):
                    instance.quit()
            except RuntimeError:
                pass

        stuck_template = self.i18n.get("main.logs.worker_stuck")
        stopped_template = self.i18n.get("main.logs.worker_stopped")
        for name, instance in active_workers:
            try:
                if not instance.wait(1000):
                    self.logger.warning(stuck_template.replace("{worker}", name))
                    instance.terminate()
                    instance.wait(300)
                else:
                    self.logger.info(stopped_template.replace("{worker}", name))
            except RuntimeError:
                pass

    def _stop_worker_safely(self, worker_name: str, worker_instance):
        if not worker_instance:
            return
        self._stop_workers_parallel([(worker_name, worker_instance)])

    def _stop_kick_connection_workers(self):
        worker_map = [
            ("Worker_Chat_Socket", getattr(self, 'chat_worker', None)),
            ("Worker_Reward_Polling", getattr(self, 'reward_worker', None)),
            ("Worker_Auth", getattr(self, 'auth_worker', None)),
            ("Worker_Fetch_Rewards", getattr(self, 'fetch_rewards_worker', None)),
            ("Worker_Timers", getattr(self, 'timers_worker', None)),
        ]
        self._stop_workers_parallel(worker_map)

    def _stop_twitch_connection_workers(self):
        worker_map = [
            ("Worker_Twitch_Chat_Socket", getattr(self, 'twitch_chat_worker', None)),
            ("Worker_Twitch_Auth", getattr(self, 'twitch_auth_worker', None)),
        ]
        self._stop_workers_parallel(worker_map)

    def _stop_all_workers(self):
        worker_map = [
            ("Worker_Chat_Socket", getattr(self, 'chat_worker', None)),
            ("Worker_Reward_Polling", getattr(self, 'reward_worker', None)),
            ("Worker_Auth", getattr(self, 'auth_worker', None)),
            ("Worker_Fetch_Rewards", getattr(self, 'fetch_rewards_worker', None)),
            ("Worker_Timers", getattr(self, 'timers_worker', None)),
            ("Worker_Twitch_Chat_Socket", getattr(self, 'twitch_chat_worker', None)),
            ("Worker_Twitch_Auth", getattr(self, 'twitch_auth_worker', None)),
            ("Worker_Stream_Schedule", getattr(self, 'schedule_worker', None)),
        ]
        if hasattr(self, 'network_controller') and self.network_controller:
            worker_map.append(("Worker_Network", getattr(self.network_controller, 'worker', None)))

        self._stop_workers_parallel(worker_map)

    @Slot()
    def _handle_auth_process(self):
        self._stop_kick_connection_workers()
        self.dashboard_controller.handle_connecting_state()

        self.auth_worker = AuthWorker(self.i18n, self.auth_manager)
        self.auth_worker.setParent(self)
        self.auth_worker.auth_success.connect(self._on_auth_success)
        self.auth_worker.auth_error.connect(self.dashboard_controller.handle_error_state)
        self.auth_worker.finished.connect(self.auth_worker.deleteLater)
        self.auth_worker.start()

    def _on_auth_success(self, tokens):
        api_client = KickAPIClient(auth_provider=self.auth_manager)
        missing_scopes = self.auth_manager.get_missing_scopes() + self.container.twitch_auth_manager.get_missing_scopes()
        self.dashboard_controller.evaluate_scopes(missing_scopes)
        
        self.command_service.api_client = api_client
        self.spam_service.api_client = api_client
        self.timer_service.api_client = api_client
        
        self.command_service.reload_cache()
        self.spam_service.reload_filters()

        self.schedule_service.set_kick_client(api_client)
        self._start_schedule_worker()
        if hasattr(self, "schedule_controller") and self.schedule_controller:
            self.schedule_controller.fetch_current_info()

        self.chat_worker = ChatWorker(self.i18n, api_client, KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY, parent=self)
        self.chat_worker.connection_success.connect(self._on_web_socket_connected)
        self.chat_worker.message_received.connect(self._route_incoming_message)
        self.chat_worker.poll_updated.connect(self._on_poll_updated)
        self.chat_worker.poll_deleted.connect(self._on_poll_deleted)
        self.chat_worker.pinned_created.connect(self._on_pinned_created)
        self.chat_worker.pinned_deleted.connect(self._on_pinned_deleted)
        self.chat_worker.error_occurred.connect(self.dashboard_controller.handle_error_state)
        
        self.reward_worker = RewardWorker(self.i18n, api_client, poll_interval_seconds=10, parent=self)
        self.reward_worker.reward_redeemed.connect(self._on_reward_redeemed)
        
        self.chat_worker.start()
        self.reward_worker.start()
        self.auth_worker = None

    def _on_web_socket_connected(self, user_data):
        self.spam_service.broadcaster_id = user_data.get("broadcaster_id", 0)
        self.dashboard_controller.handle_connection_success(user_data)
        
        username = user_data.get("username", "Kick")
        self._kick_connected = True
        self._kick_username = username
        self._update_integrations_status_ui()

        online_str = self.i18n.get("common.status.online")
        self.sidebar.update_profile_info(username, online_str)

        msg = self.i18n.get("dashboard.status.connected_toast_msg").replace("{username}", user_data.get('username', 'Kick'))
        self.toast.show_toast(
            title=self.i18n.get("common.status.connected"),
            message=msg,
            state="success"
        )
        
        slug = username.replace("_", "-").replace(" ", "")
        self._start_timers_worker(slug)
        self._fetch_api_rewards()

    @Slot()
    def _fetch_api_rewards(self):
        if not self.auth_manager.get_tokens():
            self.logger.error(self.i18n.get("main.logs.api_offline"))
            self.rewards_controller.update_rewards_list([])
            return

        worker = getattr(self, 'fetch_rewards_worker', None)
        if worker is not None:
            try:
                if worker.isRunning():
                    self.logger.warning(self.i18n.get("main.logs.api_fetching"))
                    return
            except RuntimeError:
                self.fetch_rewards_worker = None

        try:
            api_client = KickAPIClient(auth_provider=self.auth_manager)
            self.fetch_rewards_worker = FetchRewardsWorker(api_client, parent=self)
            self.fetch_rewards_worker.rewards_fetched.connect(self.rewards_controller.update_rewards_list)
            self.fetch_rewards_worker.error_occurred.connect(self._handle_rewards_error)
            self.fetch_rewards_worker.finished.connect(self.fetch_rewards_worker.deleteLater)
            self.fetch_rewards_worker.start()
        except Exception as e:
            err_template = self.i18n.get("main.logs.api_error_setup")
            self.logger.error(err_template.replace("{error}", str(e)))

    @Slot(str)
    def _handle_rewards_error(self, error_msg: str):
        err_template = self.i18n.get("main.logs.api_error")
        self.logger.error(err_template.replace("{error}", error_msg))
        self.rewards_controller.update_rewards_list([])

    def _format_reward_message(self, reward_name: str) -> str:
        safe_reward_name = html.escape(reward_name)
        canje_template = self.i18n.get("main.chat.reward_redeemed")
        texto_canje = canje_template.replace("{reward_name}", safe_reward_name)
        return f'<span style="color: #00e701;">{texto_canje}</span>'

    @Slot(str, str, str)
    def _on_reward_redeemed(self, user: str, reward_name: str, message: str):
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
            self.view_chat.append_message(f"[{tag}] {user}", msg_sistema, COLOR_GREEN, timestamp=current_time, is_html=True)
        
        mappings = self.rewards_service.get_mappings()
        if reward_name in mappings:
            config = mappings[reward_name]
            self.rewards_service.trigger_preview(reward_name, config)
            self.rewards_service.log_redemption(reward_name, user)
        else:
            no_rewards_template = self.i18n.get("main.logs.reward_no_rewards")
            self.logger.debug(no_rewards_template.replace("{reward_name}", reward_name))

        settings = self.chat_service.get_settings()
        if settings.get("enabled", False) and message:
            dto = ChatMessageDTO(user, message, [], "", "", 0, timestamp=current_time)
            self.chat_controller.process_message(dto)

    def _start_timers_worker(self, channel_slug: str):
        self._stop_worker_safely("Worker_Timers", getattr(self, 'timers_worker', None))
        
        api_client = KickAPIClient(auth_provider=self.auth_manager)
        self.timers_worker = TimerWorker(self.timer_service, api_client, channel_slug, parent=self)
        self.timers_worker.post_message_requested.connect(self._send_timer_message)
        self.timers_worker.start()

    @Slot(str, bool, bool)
    def _send_timer_message(self, message: str, apply_kick: bool = True, apply_twitch: bool = True):
        if not message:
            return
        if apply_kick and hasattr(self, "command_service") and self.command_service:
            try:
                self.command_service.send_response(message, platform="kick")
            except Exception as e:
                self.logger.error(f"[Timer] Error posting Kick message: {e}")
        elif apply_kick and self.timer_service.api_client:
            try:
                self.timer_service.api_client.post_chat_message(content=message, msg_type="bot")
            except Exception as e:
                self.logger.error(f"[Timer] Error posting Kick message: {e}")

        if apply_twitch and hasattr(self, "command_service") and self.command_service:
            try:
                self.command_service.send_response(message, platform="twitch")
            except Exception as e:
                self.logger.error(f"[Timer] Error posting Twitch message: {e}")

    @Slot()
    def _handle_twitch_auth_process(self, force: bool = False):
        self._stop_twitch_connection_workers()
        needs_browser = force or not self.container.twitch_auth_manager.is_authenticated()
        if needs_browser:
            title = self.container.i18n.get("main.toast.twitch_auth_title")
            msg = self.container.i18n.get("main.toast.twitch_auth_opening")
            self.toast.show_toast(
                title=title,
                message=msg,
                state="info"
            )
        self.twitch_auth_worker = TwitchAuthWorker(self.container.twitch_auth_manager, force=force, parent=self)
        self.twitch_auth_worker.auth_success.connect(self._on_twitch_auth_success)
        self.twitch_auth_worker.auth_error.connect(self._on_twitch_auth_error)
        self.twitch_auth_worker.finished.connect(self.twitch_auth_worker.deleteLater)
        self.twitch_auth_worker.start()

    def _on_twitch_auth_error(self, err: str):
        logger.error(f"[Twitch Auth Error] {err}")
        log_msg = self.container.i18n.get("logs.main_window.twitch_auth_error").replace("{error}", str(err))
        self.q_log_handler.emitter.log_received.emit(log_msg)
        if getattr(self, "_is_window_closing", False):
            return
        err_title = self.container.i18n.get("main.toast.twitch_auth_error_title")
        self.toast.show_toast(title=err_title, message=str(err), state="danger")

    def _on_twitch_auth_success(self, tokens):
        logger.info("[Twitch Auth] Success callback received.")
        twitch_api = TwitchAPIClient(auth_provider=self.container.twitch_auth_manager, client_id=TWITCH_CLIENT_ID, i18n=self.container.i18n)
        user_data = twitch_api.fetch_user_data()
        if not user_data:
            logger.error("[Twitch Auth] Failed to fetch user data after auth.")
            return

        broadcaster_id = user_data.get("user_id", "")
        broadcaster_login = user_data.get("user_login", "")

        self._twitch_connected = True
        self._twitch_channel = broadcaster_login
        self.spam_service.twitch_api = twitch_api
        self.spam_service.twitch_broadcaster_id = broadcaster_id

        self._start_twitch_chat_worker(broadcaster_login)
        self._update_integrations_status_ui()
        missing_scopes = self.auth_manager.get_missing_scopes() + self.container.twitch_auth_manager.get_missing_scopes()
        self.dashboard_controller.evaluate_scopes(missing_scopes)

    def _start_twitch_chat_worker(self, channel: str):
        if hasattr(self, 'twitch_chat_worker') and self.twitch_chat_worker:
            self.twitch_chat_worker.stop()
            self.twitch_chat_worker = None

        self.twitch_chat_worker = TwitchChatWorker(
            channel_name=channel,
            oauth_token="",
            bot_nick="",
            api_client=self.spam_service.twitch_api,
            i18n=self.container.i18n,
            parent=self
        )

        self.command_service.twitch_worker = self.twitch_chat_worker
        self.spam_service.twitch_worker = self.twitch_chat_worker
        self.twitch_chat_worker.connection_success.connect(self._on_twitch_connected)
        self.twitch_chat_worker.connection_lost.connect(self._on_twitch_socket_lost)
        self.twitch_chat_worker.connection_restored.connect(self._on_twitch_socket_restored)
        self.twitch_chat_worker.message_received.connect(self._route_incoming_message)
        self.twitch_chat_worker.start()

    def _on_twitch_connected(self, user_data: dict):
        username = user_data.get("username", "")
        broadcaster_id = user_data.get("broadcaster_id", "")
        if broadcaster_id:
            self.spam_service.twitch_broadcaster_id = broadcaster_id
        self._twitch_connected = True
        self._twitch_channel = username
        self._update_integrations_status_ui()

        self.schedule_service.set_twitch_client(self.spam_service.twitch_api, broadcaster_id)
        if hasattr(self, "schedule_controller") and self.schedule_controller:
            self.schedule_controller.fetch_current_info()

        missing_scopes = self.auth_manager.get_missing_scopes() + self.container.twitch_auth_manager.get_missing_scopes()
        self.dashboard_controller.evaluate_scopes(missing_scopes)

        title = self.container.i18n.get("main.toast.twitch_connected_title")
        msg = self.container.i18n.get("main.toast.twitch_connected_msg").replace("{username}", username)
        self.toast.show_toast(
            title=title,
            message=msg,
            state="success"
        )

    def _on_twitch_socket_lost(self):
        self._twitch_connected = False
        self._update_integrations_status_ui()

    def _on_twitch_socket_restored(self):
        self._twitch_connected = True
        self._update_integrations_status_ui()

    @Slot()
    def _handle_twitch_disconnect(self):
        self._stop_twitch_connection_workers()
        self.twitch_chat_worker = None
        self.twitch_auth_worker = None
        self.command_service.twitch_worker = None
        self.spam_service.twitch_api = None
        self.spam_service.twitch_worker = None
        self.spam_service.twitch_broadcaster_id = ""
        self.container.twitch_auth_manager.logout()
        self._twitch_connected = False
        self._twitch_channel = ""
        self._update_integrations_status_ui()
        title_disc = self.container.i18n.get("main.toast.twitch_disconnected_title")
        msg_disc = self.container.i18n.get("main.toast.twitch_disconnected_msg")
        self.toast.show_toast(
            title=title_disc,
            message=msg_disc,
            state="info"
        )

    def _update_integrations_status_ui(self):
        kick_connected = getattr(self, "_kick_connected", False)
        kick_user = getattr(self, "_kick_username", "")
        twitch_connected = getattr(self, "_twitch_connected", False)
        twitch_channel = getattr(self, "_twitch_channel", "")

        if hasattr(self, "dashboard_controller") and self.dashboard_controller:
            self.dashboard_controller.set_twitch_status(
                connected=twitch_connected,
                channel=twitch_channel
            )

        if hasattr(self, "view_settings") and self.view_settings:
            self.view_settings.set_integrations_status(
                kick_connected=kick_connected,
                kick_channel=kick_user,
                twitch_connected=twitch_connected,
                twitch_channel=twitch_channel
            )

    @Slot()
    def _on_twitch_integration_button_clicked(self):
        if getattr(self, "_twitch_connected", False):
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
    def _on_kick_integration_button_clicked(self):
        if getattr(self, "_kick_connected", False):
            self._force_reauth()
        else:
            self._handle_auth_process()

    @Slot()
    def _force_reauth(self):
        if self.container.twitch_auth_manager.has_missing_scopes():
            self._handle_twitch_auth_process(force=True)
        if self.auth_manager.has_missing_scopes() or not self.container.twitch_auth_manager.has_missing_scopes():
            self.auth_manager.logout()
            self._handle_auth_process()

    @Slot()
    def _handle_unlink_account(self):
        dialog = ModernConfirmDialog(
            self.i18n,
            self, 
            title_text=self.i18n.get("dialogs.unlink.title"), 
            body_text=self.i18n.get("dialogs.unlink.desc")
        )
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.toast.show_toast(
                title=self.i18n.get("settings.status.unlinked"),
                message=self.i18n.get("settings.status.unlinked_msg"),
                state="warning"
            )
            self._stop_all_workers()
            self.chat_worker = None
            self.reward_worker = None
            self.timers_worker = None

            self.auth_manager.logout()
            self.dashboard_controller.reset_to_disconnected()
            self.sidebar.reset_profile_info()
            
            if self.view_chat and hasattr(self.view_chat, "chat_display") and self.view_chat.chat_display is not None:
                self.view_chat.chat_display.clear()
            self._handle_navigation("Dashboard")
            
            for btn in self.sidebar.nav_buttons:
                if btn.property("view_name") == "Dashboard":
                    btn.setChecked(True)
                    break

    def _start_schedule_worker(self):
        current_worker = getattr(self, "schedule_worker", None)
        if current_worker is None or not current_worker.isRunning():
            self.schedule_worker = ScheduleWorker(self.schedule_service, parent=self)
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
            self.schedule_controller.fetch_current_info()

    def _route_incoming_message(self, user_or_dto, msg: str = None, badges: list = None, color: str = "", msg_id: str = "", sender_id: int = 0):
        self._increment_metric("messages_processed")
        current_time = datetime.now().strftime("%H:%M:%S")
        if isinstance(user_or_dto, ChatMessageDTO):
            dto = user_or_dto
            if not dto.timestamp:
                dto.timestamp = current_time
        else:
            dto = ChatMessageDTO(user_or_dto, msg, badges or [], color, msg_id, sender_id, timestamp=current_time)
        self.chat_controller.process_message(dto)

    def _on_poll_updated(self, poll_data: dict):
        self._active_poll_data = poll_data
        if hasattr(self, 'overlay_server') and self.overlay_server:
            self.overlay_server.trigger_widget_event("poll_update", {"poll": poll_data})

    def _on_poll_deleted(self):
        self._active_poll_data = None
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
    def _apply_dynamic_theme(self, base_size: int, immediate: bool = False):
        if hasattr(self, "_theme_timer") and self._theme_timer.isActive():
            self._theme_timer.stop()
        
        if immediate:
            QApplication.instance().setStyleSheet(get_global_qss(base_size))
            return

        self._theme_timer = QTimer(self)
        self._theme_timer.setSingleShot(True)
        self._theme_timer.timeout.connect(lambda: QApplication.instance().setStyleSheet(get_global_qss(base_size)))
        self._theme_timer.start(250)

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
                summary = self.container.commands_storage.get_active_features_summary()
                self._cached_total_usages = summary.get("total_command_usages", 0)
                self._cached_active_timers = summary.get("active_timers", 0)
            except Exception as e:
                self.logger.error(f"[Metrics] Error reading summary: {e}")
                self._cached_total_usages = self._cached_total_usages or 0
                self._cached_active_timers = self._cached_active_timers or 0

        self.view_dashboard.update_session_metrics(
            msg_count=self.session_metrics["messages_processed"],
            cmd_count=self._cached_total_usages,
            timer_count=self._cached_active_timers,
            spam_count=self.session_metrics["spam_blocked"]
        )
