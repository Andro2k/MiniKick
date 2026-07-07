# frontend\views\main_window_view.py

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QStackedWidget, 
                               QSystemTrayIcon, QApplication)
from PySide6.QtCore import Slot, QEvent

from backend.services.chat.pipeline import ChatMessageDTO
from backend.services.stream.rewards_service import RewardsService
from backend.services.chat.chat_service import ChatService
from backend.services.chat.command_service import CommandService
from backend.services.system.dashboard_service import AvatarService
from backend.services.system.log_service import LogService
from backend.services.system.settings_service import SettingsService
from backend.services.chat.spam_service import SpamService
from backend.services.chat.timer_service import TimerService
from backend.controllers.rewards_controller import RewardsController
from backend.controllers.chat_controller import ChatController
from backend.controllers.command_controller import CommandController
from backend.controllers.dashboard_controller import DashboardController
from backend.controllers.timer_controller import TimerController
from backend.controllers.log_controller import LogController
from backend.controllers.music_controller import MusicController
from backend.controllers.settings_controller import SettingsController
from backend.controllers.spam_controller import SpamController
from backend.controllers.update_controller import UpdateController
from backend.controllers.network_controller import NetworkController
from backend.providers.kick.kick_client import KickAPIClient

from frontend.core.app_container_core import AppContainer
from frontend.core.app_logger_core import setup_application_logging
from frontend.common.theme import COLOR_ACCENT, get_global_qss
from frontend.navigation.sidebar_component import Sidebar
from frontend.navigation.toast_component import ToastManager
from frontend.navigation.tray_menu_component import SystemTrayManager
from frontend.views.rewards_view import RewardsView
from frontend.views.command_view import CommandView
from frontend.views.dashboard_view import DashboardView
from frontend.views.timers_view import TimersView
from frontend.views.chat_view import ChatView
from frontend.views.log_view import LogView
from frontend.views.music_view import MusicView
from frontend.views.settings_view import SettingsView
from frontend.views.spam_view import SpamView
from frontend.views.network_view import NetworkView
from frontend.dialogs import ModernConfirmDialog
from frontend.workers.auth_worker import AuthWorker
from frontend.workers.chat_worker import ChatWorker
from frontend.workers.rewards_worker import FetchRewardsWorker, RewardWorker
from frontend.workers.timers_worker import TimerWorker

try:
    from backend.config.api_keys import KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY
except ImportError:
    KICK_PUSHER_CLUSTER = "us2"
    KICK_PUSHER_KEY = "32cbd69e4b950bf97679"

class MainWindow(QMainWindow):
    SETTING_MINIMIZE_TRAY = "minimize_to_tray"
    SETTING_AUTOSTART = "dashboard_autostart"

    def __init__(self, updater_manager, app_version: str):
        super().__init__()
        self._is_shutting_down = False
        self.updater_manager = updater_manager
        self.app_version = app_version
        self.container = AppContainer(self)
        self.db_manager = self.container.db_manager
        self.token_storage = self.container.kick_token_storage
        self.settings_storage = self.container.settings_storage 
        self.rewards_storage = self.container.rewards_storage
        self.commands_storage = self.container.commands_storage
        self.spam_storage = self.container.spam_storage
        self.timers_storage = self.container.timers_storage
        self.backup_service = self.container.backup_service
        self.i18n = self.container.i18n
        self.auth_manager = self.container.auth_manager
        self.tts_manager = self.container.tts_manager
        self.media_trigger_service = self.container.media_trigger_service
        self.overlay_server = self.container.overlay_server
        
        title_template = self.i18n.get("main.window.title")
        self.setWindowTitle(title_template.replace("{version}", app_version))
        self.resize(1100, 750)
        
        self.chat_worker = None
        self.reward_worker = None
        self.auth_worker = None
        self.fetch_rewards_worker = None
        self._nav_mapping: dict[str, QWidget] = {}

        self.logger, self.q_log_handler = setup_application_logging()  
        self.toast = ToastManager(self)
        self._setup_ui()
        self._setup_tray() 
        
        self.update_controller = UpdateController(self, self.updater_manager, self.i18n)
        self.update_controller.check_updates_silently(self.sidebar)
        
        self._connect_signals()     
        self._load_settings_into_ui()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sidebar = Sidebar(self.i18n, app_version=self.app_version)
        self.sidebar.add_tab("Dashboard", "dashboard.svg", is_active=True)
        self.sidebar.add_tab("Chat", "message.svg")
        self.sidebar.add_tab("Comandos", "code.svg")
        self.sidebar.add_tab("Spam Filters", "shield-half.svg")
        self.sidebar.add_tab("Timers", "clock.svg")
        self.sidebar.add_tab("Music", "music.svg")
        self.sidebar.add_tab("Triggers", "layout-dashboard.svg")
        self.sidebar.add_tab("Network Status", "access-point.svg", position="bottom")
        self.sidebar.add_tab("Settings", "settings.svg", position="bottom")
        self.sidebar.add_tab("Developer", "brand-tabler.svg", position="bottom")

        self.content_stack = QStackedWidget()
        self.avatar_service = AvatarService(self.container.db_manager)
        self.chat_service = ChatService(self.tts_manager, self.settings_storage)
        self.settings_service = SettingsService(self.settings_storage, self.backup_service)
        self.rewards_service = RewardsService(self.rewards_storage, self.overlay_server)
        
        self.command_service = CommandService(self.commands_storage, api_client=None)
        self.spam_service = SpamService(self.spam_storage, api_client=None)
        self.timer_service = TimerService(self.timers_storage, api_client=None)
        self.log_service = LogService(self.container.db_manager)
        self.timers_worker = None

        self.view_dashboard = DashboardView(self.i18n)
        self.view_chat = ChatView(self.i18n)
        self.view_music = MusicView(self.i18n)
        self.view_rewards = RewardsView(self.i18n, overlay_url=self.overlay_server.get_overlay_url())
        self.view_commands = CommandView(self.i18n)
        self.view_spam = SpamView(self.i18n)
        self.view_timers = TimersView(self.i18n)
        self.view_settings = SettingsView(self.i18n)
        self.view_logs = LogView(self.i18n)
        self.view_network = NetworkView(self.i18n)

        self._nav_mapping = {
            "Dashboard": self.view_dashboard,
            "Chat": self.view_chat,
            "Comandos": self.view_commands,
            "Spam Filters": self.view_spam,
            "Timers": self.view_timers,
            "Music": self.view_music,
            "Triggers": self.view_rewards,
            "Settings": self.view_settings,
            "Developer": self.view_logs,
            "Network Status": self.view_network,
        }

        self.dashboard_controller = DashboardController(
            view=self.view_dashboard, 
            avatar_service=self.avatar_service
        )
        self.chat_controller = ChatController(
            view=self.view_chat, 
            service=self.chat_service,
            command_service=self.command_service,
            spam_service=self.spam_service,
            i18n=self.i18n,
            timer_service=self.timer_service
        )
        self.music_controller = MusicController(
            view=self.view_music,
            spotify_auth=self.container.spotify_auth,
            command_service=self.command_service,
            toast_manager=self.toast,
            i18n=self.i18n,
            settings_storage=self.container.settings_storage
        )
        self.rewards_controller = RewardsController(
            view=self.view_rewards, 
            service=self.rewards_service
        )
        self.command_controller = CommandController(
            self.view_commands, 
            self.command_service
        )
        self.spam_controller = SpamController(
            self.view_spam, 
            self.spam_service
        )
        self.timer_controller = TimerController(
            self.view_timers,
            self.timer_service
        )
        self.settings_controller = SettingsController(
            view=self.view_settings, 
            service=self.settings_service
        )
        self.log_controller = LogController(
            view=self.view_logs, 
            service=self.log_service
        )
        self.network_controller = NetworkController(
            view=self.view_network, 
            overlay_port=self.overlay_server.port
        )
        self.session_metrics = {
            "messages_processed": 0,
            "commands_executed": 0,
            "timers_sent": 0,
            "spam_blocked": 0
        }

        self.content_stack.addWidget(self.view_dashboard)
        self.content_stack.addWidget(self.view_chat)
        self.content_stack.addWidget(self.view_music)
        self.content_stack.addWidget(self.view_rewards)
        self.content_stack.addWidget(self.view_commands)
        self.content_stack.addWidget(self.view_spam)
        self.content_stack.addWidget(self.view_timers)
        self.content_stack.addWidget(self.view_settings)
        self.content_stack.addWidget(self.view_logs)
        self.content_stack.addWidget(self.view_network)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

        self._update_dashboard_metrics()

    def _setup_tray(self):
        self.tray_manager = SystemTrayManager(self.i18n, self)
        self.tray_manager.restore_requested.connect(self._restore_from_tray)
        self.tray_manager.quit_requested.connect(self._force_quit)
        self.tray_manager.tts_toggled.connect(self._handle_tray_tts_toggle)
        self.tray_manager.show()

    @Slot()
    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    @Slot(bool)
    def _handle_tray_tts_toggle(self, enabled: bool):
        settings = self.chat_service.get_settings()
        settings["enabled"] = enabled
        self.chat_service.save_settings(settings)
        self.view_chat.set_initial_states(settings)
        self.chat_controller.sync_settings_cache()
        estado = (self.i18n.get("main.tray.tts_on") if enabled else self.i18n.get("main.tray.tts_off"))
        msg_template = self.i18n.get("main.tray.tts_msg")       
        self.tray_manager.showMessage("MiniKick", msg_template.replace("{estado}", estado), QSystemTrayIcon.MessageIcon.Information, 2000)

    def _connect_signals(self):
        self.settings_controller.style_reload_requested.connect(self._apply_dynamic_theme)
        self.sidebar.view_selected.connect(self._handle_navigation)
        self.dashboard_controller.request_connection.connect(self._handle_auth_process)
        self.dashboard_controller.auto_start_toggled.connect(self._handle_autostart_change)
        self.dashboard_controller.reauth_requested.connect(self._force_reauth)
        self.chat_controller.tts_state_changed.connect(self.tray_manager.set_tts_state)
        self.chat_controller.spam_blocked.connect(lambda: self._increment_metric("spam_blocked"))
        self.chat_controller.command_executed.connect(self._update_dashboard_metrics)
        self.view_rewards.refresh_rewards_requested.connect(self._fetch_api_rewards)
        self.settings_controller.unlink_account_requested.connect(self._handle_unlink_account)
        self.settings_controller.check_update_requested.connect(self.update_controller.handle_update_check)
        self.settings_controller.notification_requested.connect(
            lambda title, msg: self.tray_manager.showMessage(title, msg)
        )
        self.settings_controller.backup_restored.connect(self._load_settings_into_ui)
        self.q_log_handler.emitter.log_received.connect(self.log_controller.process_incoming_log)
        self.avatar_service.avatar_downloaded.connect(self.sidebar.update_profile_avatar)

    def _load_settings_into_ui(self):
        self.rewards_controller.load_initial_data()
        tts_enabled = self.settings_storage.load_bool("tts_enabled", True)
        self.tray_manager.set_tts_state(tts_enabled)
        autostart_enabled = self.settings_storage.load_bool(self.SETTING_AUTOSTART, False)
        self.view_dashboard.set_autostart_state(autostart_enabled)
        self.command_service.reload_cache()
        self.spam_controller.load_initial_data()
        self.timer_controller.load_initial_data()
        self.chat_controller.load_initial_data()
        self.chat_controller.sync_settings_cache()
        self._apply_dynamic_theme(self.settings_service.get_font_size())
        if autostart_enabled:
            self._handle_auth_process()

    def _handle_navigation(self, view_name):
        target_view = self._nav_mapping.get(view_name)
        if target_view:
            self.content_stack.setCurrentWidget(target_view)

    @Slot()
    def _handle_auth_process(self):
        self._stop_worker_safely("Worker_Auth", getattr(self, 'auth_worker', None))
        self._stop_worker_safely("Worker_Chat_Socket", getattr(self, 'chat_worker', None))
        self._stop_worker_safely("Worker_Reward_Polling", getattr(self, 'reward_worker', None))
        self._stop_worker_safely("Worker_Timers", getattr(self, 'timers_worker', None))
        self.dashboard_controller.handle_connecting_state()

        self.auth_worker = AuthWorker(self.i18n, self.auth_manager)
        self.auth_worker.setParent(self)
        self.auth_worker.auth_success.connect(self._on_auth_success)
        self.auth_worker.auth_error.connect(self.dashboard_controller.handle_error_state)
        self.auth_worker.finished.connect(self.auth_worker.deleteLater)
        self.auth_worker.start()

    def _on_auth_success(self, tokens):
        api_client = KickAPIClient(auth_provider=self.auth_manager)
        self.dashboard_controller.evaluate_scopes(self.auth_manager.get_missing_scopes())
        
        self.command_service.api_client = api_client
        self.spam_service.api_client = api_client
        self.timer_service.api_client = api_client
        
        self.command_service.reload_cache()
        self.spam_service.reload_filters()

        self.chat_worker = ChatWorker(self.i18n, api_client, KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY, parent=self)
        self.chat_worker.connection_success.connect(self._on_web_socket_connected)
        self.chat_worker.message_received.connect(self._route_incoming_message)
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

    @Slot()
    def _force_reauth(self):
        self.auth_manager.logout()
        self._handle_auth_process()

    @Slot(str, str, list, str, str, int)
    def _route_incoming_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int):
        self._increment_metric("messages_processed")
        dto = ChatMessageDTO(user, msg, badges, color, msg_id, sender_id)
        self.chat_controller.process_message(dto)

    @Slot(str, str, str)
    def _on_reward_redeemed(self, user: str, reward_name: str, message: str):
        toast_template = self.i18n.get("main.toasts.reward_msg")
        self.toast.show_toast(
            title=self.i18n.get("main.toasts.reward_title"), 
            message=toast_template.replace("{user}", user).replace("{reward_name}", reward_name), 
            state="success"
        )
        
        canje_template = self.i18n.get("main.chat.reward_redeemed")
        texto_canje = canje_template.replace("{reward_name}", reward_name)
        msg_sistema = f'<span style="color: #00e701;">{texto_canje}</span>'
        tag = self.i18n.get("main.chat.points_tag")
        self.view_chat.append_message(f"[{tag}] {user}", msg_sistema, COLOR_ACCENT)
        
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
            dto = ChatMessageDTO(user, message, [], "", "", 0)
            self.chat_controller.process_message(dto)

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
            
    @Slot(bool)
    def _handle_autostart_change(self, enabled: bool):
        self.settings_storage.save_bool(self.SETTING_AUTOSTART, enabled)

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
            self._stop_worker_safely("Worker_Chat_Socket", getattr(self, 'chat_worker', None))
            self._stop_worker_safely("Worker_Reward_Polling", getattr(self, 'reward_worker', None))
            self._stop_worker_safely("Worker_Timers", getattr(self, 'timers_worker', None))
            self.chat_worker = None
            self.reward_worker = None
            self.timers_worker = None

            self.auth_manager.logout()
            self.dashboard_controller.reset_to_disconnected()
            self.sidebar.reset_profile_info()
            
            self.view_chat.chat_display.clear()
            self._handle_navigation("Dashboard")
            
            for btn in self.sidebar.nav_buttons:
                if btn.property("view_name") == "Dashboard":
                    btn.setChecked(True)
                    break
        
    def _notify_background(self):
        self.tray_manager.showMessage(
            self.i18n.get("main.tray.bg_title"),
            self.i18n.get("main.tray.bg_desc"),
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False):
                self.hide()
                self._notify_background()
        super().changeEvent(event)

    def _force_quit(self):
        self._cleanup()
        QApplication.quit()

    def _stop_worker_safely(self, worker_name: str, worker_instance):
        if not worker_instance:
            return
        try:
            if worker_instance.isRunning():
                stop_template = self.i18n.get("main.logs.worker_stopping")
                self.logger.info(stop_template.replace("{worker}", worker_name))

                if hasattr(worker_instance, 'stop'):
                    worker_instance.stop()

                if not worker_instance.wait(1500):
                    stuck_template = self.i18n.get("main.logs.worker_stuck")
                    self.logger.warning(stuck_template.replace("{worker}", worker_name))
                    worker_instance.terminate()
                    worker_instance.wait()
                else:
                    stopped_template = self.i18n.get("main.logs.worker_stopped")
                    self.logger.info(stopped_template.replace("{worker}", worker_name))
        except RuntimeError:
            pass

    def _cleanup(self):
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        
        self.logger.info(self.i18n.get("main.logs.shutdown_init"))
        
        if hasattr(self, 'music_controller') and self.music_controller:
            self.music_controller.shutdown()

        self.logger.info(self.i18n.get("main.logs.shutdown_tts_overlay"))
        self.tts_manager.stop()        
        self.overlay_server.stop() 

        self._stop_worker_safely("Worker_Chat_Socket", self.chat_worker)
        self._stop_worker_safely("Worker_Reward_Polling", self.reward_worker)
        self._stop_worker_safely("Worker_Auth", getattr(self, 'auth_worker', None))
        self._stop_worker_safely("Worker_Fetch_Rewards", getattr(self, 'fetch_rewards_worker', None))
        self._stop_worker_safely("Worker_Timers", getattr(self, 'timers_worker', None))

        self.logger.info(self.i18n.get("main.logs.shutdown_complete"))

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
                event.accept() 
                self._force_quit() 
            else:
                event.ignore()

    def _start_timers_worker(self, channel_slug: str):
        self._stop_worker_safely("Worker_Timers", getattr(self, 'timers_worker', None))
        
        api_client = KickAPIClient(auth_provider=self.auth_manager)
        self.timers_worker = TimerWorker(self.timer_service, api_client, channel_slug, parent=self)
        self.timers_worker.post_message_requested.connect(self._send_timer_message)
        self.timers_worker.start()

    @Slot(str)
    def _send_timer_message(self, message: str):
        if self.timer_service.api_client:
            try:
                self.timer_service.api_client.post_chat_message(content=message, msg_type="bot")
            except Exception as e:
                self.logger.error(f"[Timer] Error posting message: {e}")

    @Slot(int)
    def _apply_dynamic_theme(self, base_size: int):
        new_stylesheet = get_global_qss(base_size)
        QApplication.instance().setStyleSheet(new_stylesheet)

    def _increment_metric(self, name: str):
        if hasattr(self, 'session_metrics') and name in self.session_metrics:
            self.session_metrics[name] += 1
        self._update_dashboard_metrics()

    @Slot()
    def _update_dashboard_metrics(self):
        try:
            summary = self.container.commands_storage.get_active_features_summary()
            total_usages = summary.get("total_command_usages", 0)
            active_timers = summary.get("active_timers", 0)
        except Exception as e:
            self.logger.error(f"[Metrics] Error reading summary: {e}")
            total_usages = 0
            active_timers = 0

        self.view_dashboard.update_session_metrics(
            msg_count=self.session_metrics["messages_processed"],
            cmd_count=total_usages,
            timer_count=active_timers,
            spam_count=self.session_metrics["spam_blocked"]
        )
    