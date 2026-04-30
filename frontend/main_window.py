# frontend/main_window.py

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QStackedWidget, 
                               QSystemTrayIcon, QMenu, QApplication)
from PySide6.QtCore import Slot, QThread, Signal, QEvent
from PySide6.QtGui import QIcon

# Importamos las Vistas (Frontend)
from backend import updater_manager
from backend.services.updater_services import GithubUpdateProvider, WindowsInstaller
from frontend.sidebar import Sidebar
from frontend.views.dashboard_view import DashboardView
from frontend.views.chat_view import ChatView
from frontend.views.settings_view import SettingsView

# Importamos Componentes de Actualización (Frontend)
from frontend.components.update_dialog import UpdateDialog

# Importamos el Backend
from backend.auth import AuthManager
from backend.database import DatabaseManager, SQLiteTokenStorage, SQLiteSettingsStorage
from backend.chat import KickAPIClient, ChatSocketManager
from backend.tts import TTSManager, Pyttsx3Engine

# Importamos el Sistema de Actualizaciones (Backend)
from backend.updater_manager import UpdateManager

# Importamos Componentes Modernos y Utilidades
from frontend.components.dialogs import ModernConfirmDialog
from frontend.utils import resource_path

# --- Hilo de Trabajo (Alta Cohesión & SoR) ---
class ChatWorker(QThread):
    message_received = Signal(str, str) 
    error_occurred = Signal(str)        
    connection_success = Signal(dict)   

    def __init__(self, api_client: KickAPIClient, cluster: str, key: str):
        super().__init__()
        self.api_client = api_client 
        self.cluster = cluster
        self.key = key
        self.chat_manager = None

    def run(self):
        try:
            user_data = self.api_client.fetch_user_data()
            self.connection_success.emit(user_data)
            room_id = user_data.get("room_id")
            if not room_id:
                raise ValueError("No se pudo obtener el ID de la sala desde la API.")
                
            self.chat_manager = ChatSocketManager(self.cluster, self.key)

            def on_msg(user: str, msg: str):
                self.message_received.emit(user, msg)

            self.chat_manager.start_socket(room_id, on_message=on_msg)
        except Exception as e:
            self.error_occurred.emit(str(e))

# ─── CONTROLADOR PRINCIPAL ───
class MainWindow(QMainWindow):
    SETTING_MINIMIZE_TRAY = "minimize_to_tray"

    def __init__(self, updater_manager):
        super().__init__()
        self.updater_manager = updater_manager
        
        self.setWindowTitle("MiniKick - Folderly")
        self.resize(1100, 750)

        self.updater_manager = updater_manager

        # --- 1. Inicializar componentes del Backend ---
        html_path = resource_path(os.path.join("assets", "web", "success.html"))

        self.db_manager = DatabaseManager()
        self.token_storage = SQLiteTokenStorage(self.db_manager)
        self.settings_storage = SQLiteSettingsStorage(self.db_manager) 
        
        self.auth_manager = AuthManager(
            client_id=os.getenv("KICK_CLIENT_ID", ""),
            client_secret=os.getenv("KICK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("KICK_REDIRECT_URI", ""),
            storage=self.token_storage,
            success_html_path=html_path
        )

        self.tts_engine = Pyttsx3Engine(rate=150)
        self.tts_manager = TTSManager(self.tts_engine)

        self.chat_worker = None

        # --- 2. Ensamblar e iniciar UI ---
        self._setup_ui()
        self._setup_tray() 
        self._connect_signals()
        self._load_settings_into_ui()

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.add_tab("Dashboard", "home.svg", is_active=True)
        self.sidebar.add_tab("Chat", "chat.svg")
        self.sidebar.add_tab("Settings", "settings.svg")
        
        self.content_stack = QStackedWidget()
        
        self.view_dashboard = DashboardView()
        self.view_chat = ChatView()
        self.view_settings = SettingsView()

        self.content_stack.addWidget(self.view_dashboard)
        self.content_stack.addWidget(self.view_chat)
        self.content_stack.addWidget(self.view_settings)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = resource_path(os.path.join("assets", "icons", "icon.ico"))
        self.tray_icon.setIcon(QIcon(icon_path))

        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Abrir Panel")
        restore_action.triggered.connect(self.showNormal)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Cerrar MiniKick")
        quit_action.triggered.connect(self._force_quit) 

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _connect_signals(self):
        self.sidebar.view_selected.connect(self._handle_navigation)
        self.view_dashboard.request_connection.connect(self._handle_auth_process)
        self.view_chat.volume_changed.connect(self._update_tts_volume)
        self.view_chat.voice_changed.connect(self._handle_voice_change)
        
        # Conexiones de SettingsView
        self.view_settings.minimize_tray_toggled.connect(self._handle_minimize_tray_change)
        self.view_settings.unlink_account_requested.connect(self._handle_unlink_account)
        # NUEVA CONEXIÓN: Atrapamos la señal del botón de actualizar
        self.view_settings.check_update_requested.connect(self._handle_update_check)

    # ─── REGLAS DE NEGOCIO Y ORQUESTACIÓN ───

    def _load_settings_into_ui(self):
        enabled = self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False)
        self.view_settings.set_minimize_tray_enabled(enabled)
        
        saved_voice_id = self.settings_storage.load_string("tts_voice", "")
        available_voices = self.tts_engine.get_available_voices()
        
        self.view_chat.populate_voices(available_voices, saved_voice_id)
        if saved_voice_id:
            self.tts_engine.set_voice(saved_voice_id)

    @Slot()
    def _handle_update_check(self):
        """Abre el diálogo de actualizaciones cuando el usuario lo solicita."""
        dialog = UpdateDialog(manager=self.updater_manager, parent=self)
        dialog.exec() # Abre la ventana en modo modal (bloquea la ventana principal hasta que se cierre)

    @Slot(bool)
    def _handle_minimize_tray_change(self, enabled: bool):
        self.settings_storage.save_bool(self.SETTING_MINIMIZE_TRAY, enabled)

    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def _handle_navigation(self, view_name):
        mapping = {
            "Dashboard": self.view_dashboard,
            "Chat": self.view_chat,
            "Settings": self.view_settings
        }
        target_view = mapping.get(view_name)
        if target_view:
            self.content_stack.setCurrentWidget(target_view)

    @Slot()
    def _handle_auth_process(self):
        self.view_dashboard.set_connecting_state()

        try:
            tokens = self.auth_manager.get_tokens()
            
            if tokens:
                cluster = os.getenv("KICK_PUSHER_CLUSTER", "")
                key = os.getenv("KICK_PUSHER_KEY", "")

                api_client = KickAPIClient(auth_provider=self.auth_manager)
                
                self.chat_worker = ChatWorker(api_client, cluster, key)
                
                self.chat_worker.connection_success.connect(self.view_dashboard.set_connected_state)
                self.chat_worker.message_received.connect(self._on_chat_message)
                self.chat_worker.error_occurred.connect(self.view_dashboard.set_error_state)
                
                self.chat_worker.start()
            else:
                self.view_dashboard.set_error_state("No se pudo obtener autorización.")
                
        except Exception as e:
            self.view_dashboard.set_error_state(str(e))

    @Slot()
    def _handle_unlink_account(self):
        dialog = ModernConfirmDialog(
            self, 
            title_text="Desvincular Cuenta", 
            body_text="¿Estás seguro de que deseas cerrar sesión? Tendrás que volver a autorizar a MiniKick la próxima vez que te conectes."
        )
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            if self.chat_worker and self.chat_worker.isRunning():
                self.chat_worker.terminate()
                self.chat_worker.wait()
                self.chat_worker = None

            self.auth_manager.logout()

            self.view_dashboard.status_label.setText("Estado: Esperando conexión...")
            self.view_dashboard.status_label.setStyleSheet("") 
            self.view_dashboard.btn_connect.setEnabled(True)
            self.view_dashboard.btn_connect.setText("Conectar a Kick")
            self.view_dashboard.profile_container.setVisible(False)
            
            self.view_chat.chat_display.clear()

            self._handle_navigation("Dashboard")
            
            for btn in self.sidebar.nav_buttons:
                if btn.text().strip() == "Dashboard":
                    btn.setChecked(True)
                    break

    @Slot(int)
    def _update_tts_volume(self, value):
        self.tts_engine.set_volume(value / 100.0)

    @Slot(str, str)
    def _on_chat_message(self, user: str, message: str):
        self.view_chat.append_message(user, message)
        
        settings = self.view_chat.get_tts_settings()
        if not settings.get("enabled", False):
            return

        final_message = message.strip()
        
        if settings.get("use_command", False):
            cmd = settings.get("command", "")
            if not final_message.lower().startswith(cmd):
                return
            final_message = final_message[len(cmd):].strip()

        text_to_speak = f"{user} dice: {final_message}" if settings.get("read_name", False) else final_message
        self.tts_manager.say(text_to_speak)

    @Slot(str)
    def _handle_voice_change(self, voice_id: str):
        self.tts_engine.set_voice(voice_id)
        self.settings_storage.save_string("tts_voice", voice_id)
        self.tts_manager.say("Voz actualizada.")
        
    def _notify_background(self):
        self.tray_icon.showMessage(
            "MiniKick en segundo plano",
            "Seguiré leyendo el chat por ti. Haz doble clic para volver.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    # ─── GESTIÓN DE EVENTOS NATIVOS ───
    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False):
                self.hide()
                self._notify_background()
        super().changeEvent(event)

    def _force_quit(self):
        self._cleanup()
        QApplication.quit()

    def _cleanup(self):
        self.tts_manager.stop()
        if self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.terminate()
            self.chat_worker.wait()

    def closeEvent(self, event):
        if self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False):
            self.hide()
            self._notify_background()
            event.ignore() 
        else:
            dialog = ModernConfirmDialog(self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                event.accept() 
                self._force_quit() 
            else:
                event.ignore()