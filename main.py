import sys
import json
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QPushButton, QTabWidget, QLabel, QHBoxLayout)

# --- BACKEND ---
from backend.core.kick_core import KickMinimalBackend
from backend.services.chat.tts_worker import TTSWorker
from backend.services.triggers.overlay_server import OverlayMinimalServer

# --- FRONTEND ---
from frontend.pages.chat_page import ChatPage
from frontend.pages.rewards_page import RewardsPage

class KickMonitorLiteUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KickMonitor Lite")
        self.resize(700, 450)
        self.setStyleSheet("background-color: #0b0e0f; color: #ffffff;")

        # --- MOTORES INTERNOS ---
        self.backend = None
        self.tts = TTSWorker()
        self.tts.start()
        self.overlay = OverlayMinimalServer()
        self.overlay.start()

        # Filtro de emotes
        self.re_emote_clean = re.compile(r'\[emote:\d+:[^\]]+\]')

        # --- DIBUJAR INTERFAZ ---
        self.init_ui()
        
        # Conectar errores/logs internos a las páginas
        self.tts.error_signal.connect(lambda msg: self.page_chat.log(f"❌ [TTS Error] {msg}"))
        self.overlay.log_signal.connect(lambda msg: self.page_rewards.log(f"🖥️ {msg}"))

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # === CABECERA ===
        header_layout = QHBoxLayout()
        self.btn_iniciar = QPushButton("Conectar a Kick")
        self.btn_iniciar.setStyleSheet("""
            QPushButton { background-color: #53fc18; color: black; font-weight: bold; padding: 10px; border-radius: 5px; }
            QPushButton:disabled { background-color: #2c5914; color: #888888; }
        """)
        self.btn_iniciar.clicked.connect(self.iniciar_backend)

        self.lbl_status = QLabel("Estado: Desconectado")
        self.lbl_status.setStyleSheet("color: #a0a0a0; font-weight: bold; font-size: 14px; margin-left: 15px;")

        header_layout.addWidget(self.btn_iniciar)
        header_layout.addWidget(self.lbl_status)
        header_layout.addStretch()

        # === PESTAÑAS (TABS) IMPORTADAS ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333333; border-radius: 5px; top: -1px; }
            QTabBar::tab { background: #1a1d1e; color: #a0a0a0; padding: 10px 20px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #0b0e0f; color: #53fc18; font-weight: bold; }
        """)

        # Instanciar las páginas modulares
        self.page_chat = ChatPage(self.tts)
        self.page_rewards = RewardsPage()

        self.tabs.addTab(self.page_chat, "💬 Chat & Voz")
        self.tabs.addTab(self.page_rewards, "🎁 Canjes & Overlay")

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    # === LÓGICA DE CONEXIÓN ===
    def iniciar_backend(self):
        try:
            with open("backend/config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            self.page_chat.log("❌ ERROR: Crea el archivo backend/config.json con tus claves.")
            return

        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        redirect_uri = config.get("redirect_uri")

        if not all([client_id, client_secret, redirect_uri]):
            self.page_chat.log("❌ ERROR: Faltan datos en config.json")
            return

        self.btn_iniciar.setEnabled(False)
        self.btn_iniciar.setText("Conectado")
        self.lbl_status.setText("Estado: 🟢 En Línea")
        self.lbl_status.setStyleSheet("color: #53fc18; font-weight: bold; font-size: 14px; margin-left: 15px;")
        self.page_chat.log("🚀 Conectando a los servidores de Kick...")

        self.backend = KickMinimalBackend(client_id, client_secret, redirect_uri)
        self.backend.log_signal.connect(self.page_chat.log)
        self.backend.chat_signal.connect(self.on_chat_recibido)
        self.backend.redemption_signal.connect(self.on_canje_recibido)
        self.backend.start()

    def on_chat_recibido(self, usuario, mensaje):
        self.page_chat.log(f"[{usuario}]: {mensaje}")
        
        # Ignorar bots
        if usuario.startswith("@") or usuario.lower() in ["streamelements", "botrix", "nightbot"]:
            return

        # Limpiar emotes y delegar al ChatPage para que hable si el TTS está activo
        mensaje_limpio = self.re_emote_clean.sub('', mensaje).strip()
        self.page_chat.procesar_mensaje_tts(usuario, mensaje_limpio)

    def on_canje_recibido(self, usuario, recompensa, input_texto):
        msg = f"🎁 {usuario} canjeó '{recompensa}'"
        if input_texto: msg += f" (Mensaje: {input_texto})"
        self.page_rewards.log(msg)

        try:
            with open("triggers.json", "r", encoding="utf-8") as f:
                triggers = json.load(f)
        except:
            triggers = {}

        nombre_recompensa = recompensa.lower().strip()

        if nombre_recompensa in triggers:
            data = triggers[nombre_recompensa]
            self.overlay.play_media(data["file"], data.get("type", "audio"), data.get("volume", 100))
            self.page_rewards.log(f"▶️ Enviando alerta a OBS: {data['file']}")
        else:
            self.page_rewards.log(f"⚠️ '{recompensa}' no está en triggers.json.")
            self.page_chat.procesar_mensaje_tts("Sistema", f"{usuario} acaba de canjear {recompensa}")

    def closeEvent(self, event):
        if self.backend and self.backend.isRunning(): self.backend.stop()
        if self.tts and self.tts.isRunning(): self.tts.stop()
        if self.overlay and self.overlay.isRunning(): self.overlay.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = KickMonitorLiteUI()
    ventana.show()
    sys.exit(app.exec())