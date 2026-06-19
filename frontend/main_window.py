# frontend/main_window.py

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QStackedWidget, 
                               QSystemTrayIcon, QApplication)
from PySide6.QtCore import Slot, QEvent

from backend.services.alerts_service import AlertsService
from backend.services.backup_service import BackupService
from backend.services.chat_service import ChatService
from backend.services.command_service import CommandService
from backend.services.dashboard_service import AvatarService
from backend.services.log_service import LogService
from backend.services.media_trigger_service import MediaTriggerService
from backend.services.overlay_server import OverlayServerManager
from backend.services.settings_service import SettingsService
from backend.services.spam_service import SpamService
from backend.services.translation_service import TranslationService
from frontend.components.log_handler import QLogHandler, StreamToLogger
from frontend.components.sidebar import Sidebar
from frontend.components.tray_menu import SystemTrayManager
from frontend.controllers.alerts_controller import AlertsController
from frontend.controllers.chat_controller import ChatController
from frontend.controllers.command_controller import CommandController
from frontend.controllers.dashboard_controller import DashboardController
from frontend.controllers.log_controller import LogController
from frontend.controllers.settings_controller import SettingsController
from frontend.controllers.spam_controller import SpamController
from frontend.views.alerts_view import AlertsView
from frontend.views.command_view import CommandView
from frontend.views.dashboard_view import DashboardView
from frontend.views.chat_view import ChatView
from frontend.views.log_view import LogView
from frontend.views.settings_view import SettingsView
from frontend.views.spam_view import SpamView
from frontend.components.dialogs import UpdateDialog

from backend.auth_manager import AuthManager
from backend.sql_manager import DatabaseManager, SQLiteCommandsStorage, SQLiteTokenStorage, SQLiteSettingsStorage, SQLiteAlertsStorage, SQLiteSpamStorage
from backend.kick_api_client import KickAPIClient
from backend.tts_manager import TTSManager

from frontend.components.dialogs import ModernConfirmDialog
from frontend.utils import resource_path
from frontend.workers.auth_worker import AuthWorker
from frontend.workers.chat_worker import ChatWorker
from frontend.workers.fetch_rewards_worker import FetchRewardsWorker
from frontend.workers.update_worker import UpdateCheckWorker, UpdateDownloadWorker

class MainWindow(QMainWindow):
    SETTING_MINIMIZE_TRAY = "minimize_to_tray"
    SETTING_AUTOSTART = "dashboard_autostart"

    def __init__(self, updater_manager, app_version: str):
        super().__init__()
        self._is_shutting_down = False
        self.updater_manager = updater_manager
        self.app_version = app_version
        self.db_manager = DatabaseManager()
        self.token_storage = SQLiteTokenStorage(self.db_manager)
        self.settings_storage = SQLiteSettingsStorage(self.db_manager) 
        self.alerts_storage = SQLiteAlertsStorage(self.db_manager)
        self.commands_storage = SQLiteCommandsStorage(self.db_manager)
        self.spam_storage = SQLiteSpamStorage(self.db_manager)
        self.backup_service = BackupService(self.settings_storage, self.alerts_storage, self.commands_storage, self.spam_storage)

        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        install_lang_path = os.path.join(app_dir, ".install_lang")
        if os.path.exists(install_lang_path):
            try:
                with open(install_lang_path, 'r', encoding='utf-8') as f:
                    install_lang = f.read().strip()
                if install_lang in ["es", "en"]:
                    self.settings_storage.save_string("app_language", install_lang)
                os.remove(install_lang_path)
            except Exception as e:
                pass
        saved_lang = self.settings_storage.load_string("app_language", "es")
        self.i18n = TranslationService(default_lang=saved_lang)
        title = self.i18n.get("main.window.title").replace("{version}", app_version)
        self.setWindowTitle(title)
        self.resize(1100, 750)
        html_path = resource_path(os.path.join("assets", "web", "success.html"))
        self.auth_manager = AuthManager(
            client_id=os.getenv("KICK_CLIENT_ID", ""),
            client_secret=os.getenv("KICK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("KICK_REDIRECT_URI", ""),
            storage=self.token_storage,
            success_html_path=html_path
        )

        self.tts_manager = TTSManager()
        self.chat_worker = None
        self.reward_worker = None
        self.media_trigger_service = MediaTriggerService(self)
        self.overlay_server = OverlayServerManager(port=8090)
        self.overlay_server.start()

        self._setup_logging()
        self._setup_ui()
        self._setup_tray() 
        self._connect_signals()
        self._load_settings_into_ui()
        self._check_updates_silently()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sidebar = Sidebar(self.i18n, app_version=self.app_version)
        self.sidebar.add_tab("Dashboard", "home.svg", is_active=True)
        self.sidebar.add_tab("Chat", "bubble-text.svg")
        self.sidebar.add_tab("Triggers", "layout-dashboard.svg")
        self.sidebar.add_tab("Comandos", "code.svg")
        self.sidebar.add_tab("Spam Filters", "shield-half.svg")
        self.sidebar.add_tab("Settings", "settings.svg", position="bottom")
        self.sidebar.add_tab("Developer", "terminal.svg", position="bottom")

        self.content_stack = QStackedWidget()
        
        self.view_dashboard = DashboardView(self.i18n)
        self.avatar_service = AvatarService()
        self.dashboard_controller = DashboardController(
            view=self.view_dashboard, 
            avatar_service=self.avatar_service
        )
        
        self.view_chat = ChatView(self.i18n)
        self.chat_service = ChatService(self.tts_manager, self.settings_storage)
        self.chat_controller = ChatController(view=self.view_chat, service=self.chat_service)
        
        self.view_settings = SettingsView(self.i18n)
        self.settings_service = SettingsService(self.settings_storage, self.backup_service)
        self.settings_controller = SettingsController(view=self.view_settings, service=self.settings_service)
        
        self.view_alerts = AlertsView(self.i18n)
        self.alerts_service = AlertsService(self.alerts_storage, self.overlay_server)
        self.alerts_controller = AlertsController(view=self.view_alerts, service=self.alerts_service)
        
        self.view_commands = CommandView(self.i18n)
        self.command_service = CommandService(self.commands_storage, api_client=None)
        self.command_controller = CommandController(self.view_commands, self.command_service)
        
        self.view_spam = SpamView(self.i18n)
        self.spam_service = SpamService(self.spam_storage, api_client=None)
        self.spam_controller = SpamController(self.view_spam, self.spam_service)
        
        self.view_logs = LogView(self.i18n)
        self.log_service = LogService()
        self.log_controller = LogController(view=self.view_logs, service=self.log_service)
        
        self.content_stack.addWidget(self.view_dashboard)
        self.content_stack.addWidget(self.view_chat)
        self.content_stack.addWidget(self.view_settings)
        self.content_stack.addWidget(self.view_logs) 
        self.content_stack.addWidget(self.view_alerts) 
        self.content_stack.addWidget(self.view_commands)
        self.content_stack.addWidget(self.view_spam)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

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
        estado = self.i18n.get("main.tray.tts_on") if enabled else self.i18n.get("main.tray.tts_off")
        msg = self.i18n.get("main.tray.tts_msg").replace("{estado}", estado)
        self.tray_manager.showMessage("MiniKick", msg, QSystemTrayIcon.MessageIcon.Information, 2000)

    def _connect_signals(self):
        self.sidebar.view_selected.connect(self._handle_navigation)
        self.dashboard_controller.request_connection.connect(self._handle_auth_process)
        self.dashboard_controller.auto_start_toggled.connect(self._handle_autostart_change)
        self.dashboard_controller.reauth_requested.connect(self._force_reauth)
        self.chat_controller.tts_state_changed.connect(self.tray_manager.set_tts_state)
        self.view_alerts.refresh_rewards_requested.connect(self._fetch_api_rewards)
        self.settings_controller.unlink_account_requested.connect(self._handle_unlink_account)
        self.settings_controller.check_update_requested.connect(self._handle_update_check)
        self.settings_controller.notification_requested.connect(
            lambda title, msg: self.tray_manager.showMessage(title, msg)
        )
        self.settings_controller.backup_restored.connect(self._load_settings_into_ui)
        self.q_log_handler.emitter.log_received.connect(self.view_logs.append_log)

    def _load_settings_into_ui(self):
        self.alerts_controller.load_initial_data()
        tts_enabled = self.settings_storage.load_bool("tts_enabled", True)
        self.tray_manager.set_tts_state(tts_enabled)
        autostart_enabled = self.settings_storage.load_bool(self.SETTING_AUTOSTART, False)
        self.view_dashboard.set_autostart_state(autostart_enabled)
        self.command_controller.load_initial_data()
        self.spam_controller.load_initial_data()
        chat_settings = self.chat_service.get_settings()
        self.view_chat.set_initial_states(chat_settings)
        if autostart_enabled:
            self._handle_auth_process()

    @Slot()
    def _handle_update_check(self):
        dialog = UpdateDialog(self.i18n, parent=self)       
        update_info = {"url": ""}
        
        self.check_worker = UpdateCheckWorker(self.updater_manager)
        
        def on_update_found(info):
            update_info["url"] = info['download_url']
            dialog.show_update_available(info['version'])
            
        self.check_worker.update_found.connect(on_update_found)
        self.check_worker.no_update.connect(dialog.show_no_update)
        self.check_worker.error.connect(dialog.show_error)

        def on_download_requested():
            dialog.show_downloading()
            self.download_worker = UpdateDownloadWorker(self.updater_manager, update_info["url"])
            self.download_worker.progress.connect(dialog.update_progress)

            def on_download_finished(success):
                if success:
                    dialog.show_complete()
                else:
                    error_msg = self.i18n.get("main.dialogs.update.msg_unexpected_error")
                    dialog.show_error(error_msg)
                    
            self.download_worker.finished.connect(on_download_finished)
            self.download_worker.error.connect(dialog.show_error)
            self.download_worker.start()

        def on_restart_requested():
            dialog.accept()
            self._force_quit()
            
        dialog.download_requested.connect(on_download_requested)
        dialog.restart_requested.connect(on_restart_requested)
        self.check_worker.start()
        dialog.exec()

    def _check_updates_silently(self):
        self.bg_update_worker = UpdateCheckWorker(self.updater_manager)
        self.bg_update_worker.update_found.connect(
            lambda info: self.sidebar.set_update_available(True)
        )
        self.bg_update_worker.start()

    def _handle_navigation(self, view_name):
        mapping = {
            "Dashboard": self.view_dashboard,
            "Chat": self.view_chat,
            "Triggers": self.view_alerts,
            "Comandos": self.view_commands,
            "Spam Filters": self.view_spam,
            "Settings": self.view_settings,
            "Developer": self.view_logs,
        }
        target_view = mapping.get(view_name)
        if target_view:
            self.content_stack.setCurrentWidget(target_view)

    @Slot()
    def _handle_auth_process(self):
        self._stop_worker_safely("Worker_Auth", getattr(self, 'auth_worker', None))
        self._stop_worker_safely("Worker_Chat_Socket", getattr(self, 'chat_worker', None))
        self._stop_worker_safely("Worker_Reward_Polling", getattr(self, 'reward_worker', None))
        self.dashboard_controller.handle_connecting_state()

        self.auth_worker = AuthWorker(self.i18n, self.auth_manager)
        self.auth_worker.setParent(self)
        
        def on_auth_success(tokens):
            cluster = os.getenv("KICK_PUSHER_CLUSTER", "")
            key = os.getenv("KICK_PUSHER_KEY", "")
            api_client = KickAPIClient(auth_provider=self.auth_manager)
            is_missing_scopes = self.auth_manager.has_missing_scopes()
            self.dashboard_controller.evaluate_scopes(is_missing_scopes)
            self.command_service.api_client = api_client
            self.spam_service.api_client = api_client 
            self.chat_controller.command_service = self.command_service
            self.chat_worker = ChatWorker(self.i18n, api_client, cluster, key, parent=self)               

            def on_connection_success(user_data):
                self.spam_service.broadcaster_id = user_data.get("broadcaster_id", 0)
                self.dashboard_controller.handle_connection_success(user_data)
                
            self.chat_worker.connection_success.connect(on_connection_success)
            self.chat_worker.message_received.connect(self._route_incoming_message)
            self.chat_worker.error_occurred.connect(self.dashboard_controller.handle_error_state)                
            self.chat_worker.start()

        self.auth_worker.auth_success.connect(on_auth_success)
        self.auth_worker.auth_error.connect(self.dashboard_controller.handle_error_state)
        self.auth_worker.start()

    @Slot()
    def _force_reauth(self):
        self.auth_manager.logout()
        self._handle_auth_process()

    @Slot(str, str, list, str, str, int)
    def _route_incoming_message(self, user: str, msg: str, badges: list, color: str, msg_id: str, sender_id: int):
        if self.spam_service.is_spam(user, msg, badges, msg_id, sender_id):
            log_msg = self.i18n.get("main.logs.automod_sanction").replace("{user}", user).replace("{msg}", msg)
            self.logger.debug(log_msg)
            return 
            
        self.chat_controller.handle_incoming_message(user, msg, badges, color)

    @Slot(str, str, str)
    def _on_reward_redeemed(self, user: str, reward_name: str, message: str):
        texto_canje = self.i18n.get("main.chat.reward_redeemed").replace("{reward_name}", reward_name)
        msg_sistema = f'<span style="color: #00e701;">{texto_canje}</span>'
        tag = self.i18n.get("main.chat.points_tag")
        self.view_chat.append_message(f"[{tag}] {user}", msg_sistema, "#53FC18")
        
        mappings = self.alerts_service.get_mappings()
        if reward_name in mappings:
            config = mappings[reward_name]
            self.alerts_service.trigger_preview(reward_name, config)
        else:
            log_msg = self.i18n.get("main.logs.reward_no_alert").replace("{reward_name}", reward_name)
            self.logger.debug(log_msg)

        settings = self.chat_service.get_settings()
        if settings.get("enabled", False) and message:
            self.chat_controller.handle_incoming_message(user, message, [], "")

    @Slot()
    def _fetch_api_rewards(self):
        if not self.auth_manager.get_tokens():
            self.logger.error(self.i18n.get("main.logs.api_offline"))
            self.alerts_controller.update_rewards_list([])
            return

        if hasattr(self, 'fetch_rewards_worker') and self.fetch_rewards_worker.isRunning():
            self.logger.warning(self.i18n.get("main.logs.api_fetching"))
            return

        try:
            api_client = KickAPIClient(auth_provider=self.auth_manager)
            self.fetch_rewards_worker = FetchRewardsWorker(api_client, parent=self)
            self.fetch_rewards_worker.rewards_fetched.connect(self.alerts_controller.update_rewards_list)
            self.fetch_rewards_worker.error_occurred.connect(self._handle_rewards_error)
            self.fetch_rewards_worker.start()
        except Exception as e:
            self.logger.error(self.i18n.get("main.logs.api_error_setup").replace("{error}", str(e)))

    @Slot(str)
    def _handle_rewards_error(self, error_msg: str):
        self.logger.error(self.i18n.get("main.logs.api_error").replace("{error}", error_msg))
        self.alerts_controller.update_rewards_list([])
            
    @Slot(bool)
    def _handle_autostart_change(self, enabled: bool):
        self.settings_storage.save_bool(self.SETTING_AUTOSTART, enabled)

    @Slot()
    def _handle_unlink_account(self):
        dialog = ModernConfirmDialog(
            self.i18n,
            self, 
            title_text=self.i18n.get("main.dialogs.unlink_title"), 
            body_text=self.i18n.get("main.dialogs.unlink_desc")
        )
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._stop_worker_safely("Worker_Chat_Socket", getattr(self, 'chat_worker', None))
            self._stop_worker_safely("Worker_Reward_Polling", getattr(self, 'reward_worker', None))
            self.chat_worker = None
            self.reward_worker = None

            self.auth_manager.logout()
            self.dashboard_controller.reset_to_disconnected()
            
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
        if worker_instance and worker_instance.isRunning():
            self.logger.info(self.i18n.get("main.logs.worker_stopping").replace("{worker}", worker_name))

            if hasattr(worker_instance, 'stop'):
                worker_instance.stop()
            if not worker_instance.wait(2000):
                self.logger.warning(self.i18n.get("main.logs.worker_stuck").replace("{worker}", worker_name))
                worker_instance.terminate()
                worker_instance.wait()
            else:
                self.logger.info(self.i18n.get("main.logs.worker_stopped").replace("{worker}", worker_name))

    def _cleanup(self):
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        
        self.logger.info(self.i18n.get("main.logs.shutdown_init"))
        self.logger.info(self.i18n.get("main.logs.shutdown_tts_overlay"))
        self.tts_manager.stop()        
        self.overlay_server.stop() 

        self._stop_worker_safely("Worker_Chat_Socket", self.chat_worker)
        self._stop_worker_safely("Worker_Auth", getattr(self, 'auth_worker', None))
        self._stop_worker_safely("Worker_Reward_Polling", getattr(self, 'reward_worker', None))
        self._stop_worker_safely("Worker_Fetch_Rewards", getattr(self, 'fetch_rewards_worker', None))

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
                title_text=self.i18n.get("main.dialogs.close_title"), 
                body_text=self.i18n.get("main.dialogs.close_desc")
            )
            if dialog.exec() == dialog.DialogCode.Accepted:
                event.accept() 
                self._force_quit() 
            else:
                event.ignore()

    def _setup_logging(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG) 
        
        self.q_log_handler = QLogHandler()
        self.logger.addHandler(self.q_log_handler)
        
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        log_dir = os.path.join(app_data_dir, '.Minikick', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'minikick.log')
        
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',
            interval=1,
            backupCount=7, 
            encoding='utf-8'
        )
        
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)   
        self.logger.addHandler(file_handler)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("cloudscraper").setLevel(logging.WARNING)
        logging.getLogger("comtypes").setLevel(logging.WARNING)

        sys.stdout = StreamToLogger(self.logger, logging.INFO)
        sys.stderr = StreamToLogger(self.logger, logging.ERROR)