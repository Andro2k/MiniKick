# frontend/main_window.py

import logging
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QStackedWidget, 
                               QSystemTrayIcon, QMenu, QApplication)
from PySide6.QtCore import Slot, QThread, Signal, QEvent
from PySide6.QtGui import QIcon

# Importamos las Vistas (Frontend)
from frontend.components.log_handler import QLogHandler
from frontend.components.sidebar import Sidebar
from frontend.views.dashboard_view import DashboardView
from frontend.views.chat_view import ChatView
from frontend.views.log_view import LogView
from frontend.views.settings_view import SettingsView

# Importamos Componentes de Actualización (Frontend)
from frontend.components.dialogs import UpdateDialog

# Importamos el Backend
from backend.auth_manager import AuthManager
from backend.sql_manager import DatabaseManager, SQLiteTokenStorage, SQLiteSettingsStorage
from backend.chat_manager import KickAPIClient, ChatSocketManager
from backend.tts_manager import TTSManager

# Importamos Componentes Modernos y Utilidades
from frontend.components.dialogs import ModernConfirmDialog
from frontend.utils import resource_path
from frontend.workers.auth_worker import AuthWorker
from frontend.workers.update_worker import UpdateCheckWorker, UpdateDownloadWorker

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
    SETTING_AUTOSTART = "dashboard_autostart"

    def __init__(self, updater_manager, app_version: str):
        super().__init__()
        self.updater_manager = updater_manager
        
        self.setWindowTitle(f"MiniKick - Versión {app_version}")
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

        self.tts_manager = TTSManager()
        self.chat_worker = None

        # --- 2. Ensamblar e iniciar UI ---
        self._setup_logging() # Configurar logs ANTES de ensamblar la UI
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
        self.sidebar.add_tab("Developer", "terminal.svg") # NUEVA PESTAÑA

        self.content_stack = QStackedWidget()
        
        self.view_dashboard = DashboardView()
        self.view_chat = ChatView()
        self.view_settings = SettingsView()
        self.view_logs = LogView() # NUEVA VISTA

        self.content_stack.addWidget(self.view_dashboard)
        self.content_stack.addWidget(self.view_chat)
        self.content_stack.addWidget(self.view_settings)
        self.content_stack.addWidget(self.view_logs) # AÑADIDA AL STACK

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
        # Conexiones de DashboardView
        self.view_dashboard.request_connection.connect(self._handle_auth_process)
        self.view_dashboard.auto_start_toggled.connect(self._handle_autostart_change)
        # Conexiones de ChatView
        self.view_chat.volume_changed.connect(self._update_tts_volume)
        self.view_chat.voice_changed.connect(self._handle_voice_change)
        self.view_chat.provider_changed.connect(self._handle_provider_change)
        self.view_chat.settings_changed.connect(self._handle_chat_settings_change)
        # Conexiones de SettingsView
        self.view_settings.minimize_tray_toggled.connect(self._handle_minimize_tray_change)
        self.view_settings.unlink_account_requested.connect(self._handle_unlink_account)
        self.view_settings.check_update_requested.connect(self._handle_update_check)
        # Conectar el emisor de logs a la vista visual
        self.q_log_handler.emitter.log_received.connect(self.view_logs.append_log)

    # ─── REGLAS DE NEGOCIO Y ORQUESTACIÓN ───
    def _load_settings_into_ui(self):
        # 1. Cargar y aplicar volumen (Persistencia)
        saved_volume = self.settings_storage.load_string("tts_volume", "100")
        vol_int = int(saved_volume)
        self.view_chat.slider_vol.setValue(vol_int)
        self.tts_manager.set_volume(vol_int / 100.0)

        # 2. Recopilar TODAS las configuraciones del Chat desde la base de datos
        saved_provider = self.settings_storage.load_string("tts_provider", "local")
        chat_settings = {
            "enabled": self.settings_storage.load_bool("tts_enabled", True),
            "read_name": self.settings_storage.load_bool("tts_read_name", True),
            "use_command": self.settings_storage.load_bool("tts_use_command", False),
            "command": self.settings_storage.load_string("tts_command", "!tts"),
            "provider": saved_provider,
            "ignored_users": self.settings_storage.load_string("tts_ignored_users", "")
        }
        
        # Enviar las configuraciones a la vista del chat (Esto era lo que faltaba)
        self.view_chat.set_initial_settings(chat_settings)

        # 3. Cargar configuraciones de otras vistas (Dashboard y Settings) para persistencia total
        self.view_settings.set_minimize_tray_enabled(
            self.settings_storage.load_bool(self.SETTING_MINIMIZE_TRAY, False)
        )
        self.view_dashboard.set_autostart_state(
            self.settings_storage.load_bool(self.SETTING_AUTOSTART, False)
        )

        # 4. Iniciamos carga asíncrona de voces para no trabar el inicio
        self._handle_provider_change(saved_provider, is_initial_load=True)

    @Slot()
    def _handle_update_check(self):
        """Orquesta la búsqueda y descarga de actualizaciones (SoR)."""
        # 1. Instanciamos el diálogo pasivo (sin enviarle el manager)
        dialog = UpdateDialog(parent=self)       
        # Variable local para almacenar la URL de descarga si se encuentra
        update_info = {"url": ""}
        
        # 2. Creamos los workers de búsqueda aquí en el controlador
        self.check_worker = UpdateCheckWorker(self.updater_manager)
        
        # 3. Conectamos señales del worker de búsqueda a las vistas del diálogo
        def on_update_found(info):
            update_info["url"] = info['download_url']
            dialog.show_update_available(info['version'])
            
        self.check_worker.update_found.connect(on_update_found)
        self.check_worker.no_update.connect(dialog.show_no_update)
        self.check_worker.error.connect(dialog.show_error)

        # 4. Conectamos el botón de descarga del diálogo al worker de descarga
        def on_download_requested():
            dialog.show_downloading()
            self.download_worker = UpdateDownloadWorker(self.updater_manager, update_info["url"])
            
            def on_download_finished(success):
                if success:
                    dialog.status_label.setText("Instalación en marcha. Cerrando aplicación...")
                    dialog.progress_bar.setRange(0, 100)
                    dialog.progress_bar.setValue(100)

                    self._force_quit() 
                else:
                    dialog.show_error("Fallo inesperado al descargar el archivo.")
                    
            self.download_worker.finished.connect(on_download_finished)
            self.download_worker.error.connect(dialog.show_error)
            self.download_worker.start()

        # Atrapamos la señal del botón "Descargar e Instalar" de la vista
        dialog.download_requested.connect(on_download_requested)

        # 5. Iniciamos la búsqueda en 2do plano y mostramos la ventana modal
        self.check_worker.start()
        dialog.exec()

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
            "Settings": self.view_settings,
            "Developer": self.view_logs # NUEVA RUTA
        }
        target_view = mapping.get(view_name)
        if target_view:
            self.content_stack.setCurrentWidget(target_view)

    @Slot()
    def _handle_auth_process(self):
        self.view_dashboard.set_connecting_state()

        # Instanciamos el worker de autenticación
        self.auth_worker = AuthWorker(self.auth_manager)
        
        def on_auth_success(tokens):
            # Una vez autenticado, iniciamos el ChatWorker
            cluster = os.getenv("KICK_PUSHER_CLUSTER", "")
            key = os.getenv("KICK_PUSHER_KEY", "")
            api_client = KickAPIClient(auth_provider=self.auth_manager)
            
            self.chat_worker = ChatWorker(api_client, cluster, key)                
            self.chat_worker.connection_success.connect(self.view_dashboard.set_connected_state)
            self.chat_worker.message_received.connect(self._on_chat_message)
            self.chat_worker.error_occurred.connect(self.view_dashboard.set_error_state)                
            self.chat_worker.start()

        self.auth_worker.auth_success.connect(on_auth_success)
        self.auth_worker.auth_error.connect(self.view_dashboard.set_error_state)
        
        # Iniciamos la autenticación sin congelar la UI
        self.auth_worker.start()

    @Slot(bool)
    def _handle_autostart_change(self, enabled: bool):
        self.settings_storage.save_bool(self.SETTING_AUTOSTART, enabled)

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
    
    @Slot(str)
    def _handle_provider_change(self, provider: str, is_initial_load=False):
        self.tts_manager.set_provider(provider)
        self.settings_storage.save_string("tts_provider", provider)
        
        # Usamos un Worker para obtener voces (SoR)
        # Esto evita que la app se quede "En blanco" al abrir
        def on_voices_ready(voices):
            saved_voice_id = self.settings_storage.load_string(f"tts_voice_{provider}", "")
            # Pasamos un flag a la vista para que sepa si debe silenciar el saludo
            self.view_chat.populate_voices(voices, saved_voice_id, mute_signal=is_initial_load)

        # Aquí podrías crear un hilo rápido o usar QThread. 
        # Por brevedad, simulamos la respuesta asíncrona:
        voices = self.tts_manager.get_available_voices(provider)
        on_voices_ready(voices)
    
    @Slot(int)
    def _update_tts_volume(self, value):
        # Guardar en DB y aplicar en tiempo real
        self.settings_storage.save_string("tts_volume", str(value))
        self.tts_manager.set_volume(value / 100.0)

    # 4. Slot para persistir configuraciones
    @Slot(dict)
    def _handle_chat_settings_change(self, settings: dict):
        self.settings_storage.save_bool("tts_enabled", settings["enabled"])
        self.settings_storage.save_bool("tts_read_name", settings["read_name"])
        self.settings_storage.save_bool("tts_use_command", settings["use_command"])
        self.settings_storage.save_string("tts_command", settings["command"])
        self.settings_storage.save_string("tts_ignored_users", settings["ignored_users"])

    # 5. Modificar la lógica de recepción para aplicar la lista de ignorados
    @Slot(str, str)
    def _on_chat_message(self, user: str, message: str):
        self.view_chat.append_message(user, message)
        
        settings = self.view_chat.get_tts_settings()
        if not settings.get("enabled", False):
            return

        # NUEVO: Lógica de usuarios ignorados (DRY: parsear lista)
        ignored_string = settings.get("ignored_users", "")
        ignored_list = [u.strip().lower() for u in ignored_string.split(",") if u.strip()]
        
        if user.lower() in ignored_list:
            return # Evitamos mandar al TTS si es un bot

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
        # Solo hablamos si el cambio NO viene del arranque automático
        # La lógica de decisión ahora es más clara
        current_provider = "web" if self.view_chat.chk_provider.isChecked() else "local"
        self.settings_storage.save_string(f"tts_voice_{current_provider}", voice_id)
        self.tts_manager.set_voice(voice_id)
        
        # Evitamos el spam: solo decir "Voz actualizada" si la ventana está activa
        # o si no estamos en el proceso de carga inicial.
        if self.isVisible():
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

    def _setup_logging(self):
        """Configura el logger global de Python (SoR)"""
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG) # Nivel mínimo a capturar
        
        # Instanciamos el handler visual
        self.q_log_handler = QLogHandler()
        self.logger.addHandler(self.q_log_handler)
        
        # Opcional: Evitar que librerías de terceros (como requests) hagan spam
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("cloudscraper").setLevel(logging.WARNING)