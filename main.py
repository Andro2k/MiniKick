import os
import sys
import threading
from dotenv import load_dotenv

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow

from backend.auth import AuthManager
from backend.chat import ChatManager
from backend.tts import TTSManager
from frontend.theme import GLOBAL_QSS, COLOR_BG_BASE
from frontend.views.dashboard_view import DashboardView

load_dotenv()

# ==========================================
# HILO DE AUTENTICACIÓN (Evita que la UI se congele)
# ==========================================
class LoginWorker(QThread):
    success = Signal(dict, str, int)  # Emite: tokens, username, room_id
    error = Signal(str)

    def __init__(self, auth_manager, pusher_cluster, pusher_key):
        super().__init__()
        self.auth_manager = auth_manager
        self.pusher_cluster = pusher_cluster
        self.pusher_key = pusher_key

    def run(self):
        try:
            # 1. Obtiene tokens (abre navegador si es necesario)
            tokens = self.auth_manager.get_tokens()
            
            # 2. Inicia un ChatManager temporal para extraer datos de la cuenta
            temp_chat = ChatManager(tokens["access_token"], self.pusher_cluster, self.pusher_key)
            username, room_id = temp_chat.get_user_data()
            
            # 3. Envía los datos de vuelta a la UI
            self.success.emit(tokens, username, room_id)
        except Exception as e:
            self.error.emit(str(e))

# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
class KickBotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kick TTS Bot")
        self.setMinimumSize(1000, 650)
        self.setStyleSheet(f"background-color: {COLOR_BG_BASE};")

        client_id = os.getenv("KICK_CLIENT_ID")
        client_secret = os.getenv("KICK_CLIENT_SECRET")
        redirect_uri = os.getenv("KICK_REDIRECT_URI")
        self.pusher_key = os.getenv("KICK_PUSHER_KEY")
        self.pusher_cluster = os.getenv("KICK_PUSHER_CLUSTER")

        if not all([client_id, client_secret, redirect_uri]):
            print("[-] Error: Faltan credenciales en el archivo .env")
            sys.exit(1)

        self.auth_manager = AuthManager(client_id, client_secret, redirect_uri)
        self.tts_manager = TTSManager()
        self.chat_manager = None
        
        # Cargamos directamente el Dashboard como vista principal
        self.dashboard_view = DashboardView(self.tts_manager)
        self.dashboard_view.request_login.connect(self._start_login_process)
        self.setCentralWidget(self.dashboard_view)

        # Si ya existe un token.json, iniciamos la conexión automáticamente
        if os.path.exists("token.json"):
            self._start_login_process()

    def _start_login_process(self):
        """Inicia el trabajador en segundo plano para no congelar la app"""
        self.worker = LoginWorker(self.auth_manager, self.pusher_cluster, self.pusher_key)
        self.worker.success.connect(self._on_login_success)
        self.worker.error.connect(self.dashboard_view.set_error_state)
        self.worker.start()

    def _on_login_success(self, tokens: dict, username: str, room_id: int):
        print(f"[+] Autenticado como {username} (Sala: {room_id})")
        
        # Actualiza el título y el botón en el dashboard
        self.dashboard_view.set_connected_state(username, room_id)

        # Inicializa el Chat definitivo
        self.chat_manager = ChatManager(tokens["access_token"], self.pusher_cluster, self.pusher_key)
        
        # Inicia el WebSocket en un hilo separado
        threading.Thread(
            target=self.chat_manager.start_socket,
            args=(room_id, self.dashboard_view.trigger_new_message),
            daemon=True
        ).start()

    def closeEvent(self, event):
        print("[*] Cerrando aplicación...")
        self.tts_manager.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)
    
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)

    window = KickBotApp()
    window.show()
    
    sys.exit(app.exec())