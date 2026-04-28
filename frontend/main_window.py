# frontend/main_window.py

import os
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PySide6.QtCore import Slot, QThread, Signal
# Importamos las Vistas (Frontend)
from backend.database import DatabaseManager, SQLiteTokenStorage
from frontend.sidebar import Sidebar
from frontend.utils import resource_path
from frontend.views.dashboard_view import DashboardView
from frontend.views.chat_view import ChatView
from frontend.views.settings_view import SettingsView
# Importamos el Backend
from backend.auth import AuthManager, FileTokenStorage
from backend.chat import KickAPIClient, ChatSocketManager
from backend.tts import TTSManager, Pyttsx3Engine

class ChatWorker(QThread):
    message_received = Signal(str, str)
    error_occurred = Signal(str)
    # NUEVO: Contrato para enviar los datos de la API a la vista
    connection_success = Signal(dict) 

    def __init__(self, token: str, cluster: str, key: str):
        super().__init__()
        self.token = token
        self.cluster = cluster
        self.key = key
        self.chat_manager = None

    def run(self):
        try:
            # 1. Obtenemos el nuevo diccionario completo
            user_data = KickAPIClient.fetch_user_data(self.token)            
            # 2. Avisamos a la interfaz que ya tenemos la data
            self.connection_success.emit(user_data)            
            # 3. Iniciamos Websockets extrayendo el room_id
            room_id = user_data.get("room_id")
            self.chat_manager = ChatSocketManager(self.cluster, self.key)

            def on_msg(user: str, msg: str):
                self.message_received.emit(user, msg)

            self.chat_manager.start_socket(room_id, on_message=on_msg)
        except Exception as e:
            self.error_occurred.emit(str(e))

# ─── CONTROLADOR PRINCIPAL ───
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniKick - Version 1.0")
        self.resize(1100, 750)

        # 1. Inicializar componentes del Backend (Capa de Negocio)
        html_path = resource_path(os.path.join("assets", "web", "success.html"))

        # Inyectamos el nuevo Storage basado en SQLite en la carpeta AppData
        self.db_manager = DatabaseManager()
        self.token_storage = SQLiteTokenStorage(self.db_manager)
        
        self.auth_manager = AuthManager(
            client_id=os.getenv("KICK_CLIENT_ID", ""),
            client_secret=os.getenv("KICK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("KICK_REDIRECT_URI", ""),
            storage=self.token_storage,
            success_html_path=html_path
        )

        # 2. Inyectar dependencias de TTS (Desacoplado)
        self.tts_engine = Pyttsx3Engine(rate=150)
        self.tts_manager = TTSManager(self.tts_engine)
        
        # Referencia al hilo de chat (comienza vacío)
        self.chat_worker = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Estructura principal de la aplicación"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = Sidebar()
        self.sidebar.add_tab("Dashboard", "home.svg", is_active=True)
        self.sidebar.add_tab("Chat", "chat.svg")
        self.sidebar.add_tab("Settings", "settings.svg")
        
        # --- Contenedor de Vistas (Stacked Widget) ---
        self.content_stack = QStackedWidget()
        
        self.view_dashboard = DashboardView()
        self.view_chat = ChatView()
        self.view_settings = SettingsView()

        self.content_stack.addWidget(self.view_dashboard)
        self.content_stack.addWidget(self.view_chat)
        self.content_stack.addWidget(self.view_settings)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack)

    def _connect_signals(self):
        """Conecta eventos de la interfaz con los procesos lógicos"""
        self.sidebar.view_selected.connect(self._handle_navigation)
        self.view_dashboard.request_connection.connect(self._handle_auth_process)
        self.view_chat.volume_changed.connect(self._update_tts_volume)

    @Slot(str)
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
            
            if tokens and "access_token" in tokens:
                cluster = os.getenv("KICK_PUSHER_CLUSTER", "")
                key = os.getenv("KICK_PUSHER_KEY", "")
                
                self.chat_worker = ChatWorker(tokens["access_token"], cluster, key)

                self.chat_worker.connection_success.connect(self.view_dashboard.set_connected_state)
                
                self.chat_worker.message_received.connect(self._on_chat_message)
                self.chat_worker.error_occurred.connect(self.view_dashboard.set_error_state)
                
                self.chat_worker.start()

        except Exception as e:
            self.view_dashboard.set_error_state(str(e))
            print(f"[Controller] Error en auth: {e}")

    @Slot(int)
    def _update_tts_volume(self, value):
        # Convertimos de 0-100 (UI) a 0.0-1.0 (Engine)
        self.tts_engine.set_volume(value / 100.0)

    @Slot(str, str)
    def _on_chat_message(self, user: str, message: str):
        # 1. Mostrar siempre en la UI
        self.view_chat.append_message(user, message)

        # 2. Lógica de Filtrado TTS (Reglas de Negocio)
        settings = self.view_chat.get_tts_settings()
        
        if not settings["enabled"]:
            return

        final_message = message.strip()
        
        # Filtro de Comando
        if settings["use_command"]:
            cmd = settings["command"]
            if not final_message.lower().startswith(cmd):
                return
            # Removemos el comando del audio (ej: "!tts hola" -> "hola")
            final_message = final_message[len(cmd):].strip()

        # Construcción de la frase (Lectura de nombre)
        if settings["read_name"]:
            text_to_speak = f"{user} dice: {final_message}"
        else:
            text_to_speak = final_message

        # 3. Ejecutar audio
        self.tts_manager.say(text_to_speak)

    def closeEvent(self, event):
        """Regla de limpieza: Asegurarnos de cerrar los hilos al salir de la app"""
        self.tts_manager.stop()
        if self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.terminate()
            self.chat_worker.wait()
        super().closeEvent(event)