import sys
import json
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QPushButton, QTabWidget, QLabel, QHBoxLayout)

# --- BACKEND (CORE & SERVICIOS) ---
from backend.core.db_manager import DBManager
from backend.core.kick_bot import KickBot
from backend.services.tts_worker import TTSWorker
from backend.services.trigger_worker import OverlayServer

# --- FRONTEND (PÁGINAS) ---
from frontend.pages.chat_page import ChatPage
from frontend.pages.rewards_page import RewardsPage

class KickMonitorLiteUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KickMonitor Lite")
        self.resize(700, 450)
        self.setStyleSheet("background-color: #0b0e0f; color: #ffffff;")

        # --- 1. INICIALIZAR BASE DE DATOS Y SERVICIOS ---
        self.db = DBManager()  # ✅ Ahora la BD se inicializa primero
        
        self.tts = TTSWorker()
        self.tts.start()
        
        self.overlay = OverlayServer()
        self.overlay.start()

        self.backend = None # El bot de Kick se inicia al pulsar el botón
        
        # Filtro de emotes (para el TTS)
        self.re_emote_clean = re.compile(r'\[emote:\d+:[^\]]+\]')

        # --- 2. DIBUJAR INTERFAZ ---
        self.init_ui()
        self._conectar_senales_servicios()

    def init_ui(self):
        """Construye la interfaz principal y las pestañas."""
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

        # === PESTAÑAS (TABS) ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333333; border-radius: 5px; top: -1px; }
            QTabBar::tab { background: #1a1d1e; color: #a0a0a0; padding: 10px 20px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #0b0e0f; color: #53fc18; font-weight: bold; }
        """)

        # Instanciar las páginas modulares
        self.page_chat = ChatPage(self.tts, self.db)
        # 💡 Nota: En el futuro próximo le pasaremos self.db a RewardsPage
        self.page_rewards = RewardsPage(self.db)

        self.tabs.addTab(self.page_chat, "💬 Chat & Voz")
        self.tabs.addTab(self.page_rewards, "🎁 Canjes & Overlay")

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def _conectar_senales_servicios(self):
        """Conecta los logs de los servicios en segundo plano a las consolas visuales."""
        self.tts.error_signal.connect(lambda msg: self.page_chat.log(f"❌ [TTS Error] {msg}"))
        self.overlay.log_signal.connect(lambda msg: self.page_rewards.log(f"🖥️ {msg}"))

    # === 3. LÓGICA DE CONEXIÓN KICK ===
    
    def iniciar_backend(self):
        """Lee credenciales, instancia el bot de Kick y conecta sus señales."""
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

        # Actualizar UI
        self.btn_iniciar.setEnabled(False)
        self.btn_iniciar.setText("Conectado")
        self.lbl_status.setText("Estado: 🟢 En Línea")
        self.lbl_status.setStyleSheet("color: #53fc18; font-weight: bold; font-size: 14px; margin-left: 15px;")
        self.page_chat.log("🚀 Conectando a los servidores de Kick...")

        # Iniciar y conectar el Bot (Pasándole la BD)
        self.backend = KickBot(client_id, client_secret, redirect_uri, self.db)
        self.backend.log_signal.connect(self.page_chat.log)
        self.backend.chat_signal.connect(self.on_chat_recibido)
        self.backend.redemption_signal.connect(self.on_canje_recibido)
        self.backend.rewards_list_signal.connect(self.page_rewards.cargar_recompensas_kick)
        self.page_rewards.request_kick_update.connect(self.backend.update_kick_reward_sync)
        self.backend.start()

    # === 4. PROCESAMIENTO DE EVENTOS EN VIVO ===

    def on_chat_recibido(self, usuario, mensaje):
        """Procesa los mensajes de chat entrantes."""
        self.page_chat.log(f"[{usuario}]: {mensaje}")
        
        # Ignorar bots
        if usuario.startswith("@") or usuario.lower() in ["streamelements", "botrix", "nightbot"]:
            return
            
        # ✅ VERIFICAR BLACKLIST EN LA BASE DE DATOS
        if usuario.lower() in self.db.get_ignored_users():
            return

        # Limpiar emotes y enviar al TTS
        mensaje_limpio = self.re_emote_clean.sub('', mensaje).strip()
        self.page_chat.procesar_mensaje_tts(usuario, mensaje_limpio)

    def on_canje_recibido(self, usuario, recompensa, input_texto):
        """Procesa los canjes y dispara el overlay."""
        msg = f"🎁 {usuario} canjeó '{recompensa}'"
        if input_texto: 
            msg += f" (Mensaje: {input_texto})"
        self.page_rewards.log(msg)

        nombre_recompensa = recompensa.lower().strip()
        
        # ✅ LEER TRIGGERS DESDE SQLITE EN LUGAR DE JSON
        triggers_db = self.db.get_all_triggers()

        if nombre_recompensa in triggers_db:
            data = triggers_db[nombre_recompensa]
            
            # Verificar si el trigger está activado en la base de datos
            if not data.get("enabled", True):
                self.page_rewards.log(f"⚠️ El trigger '{recompensa}' está desactivado.")
                return

            # Mandamos toda la info al servidor del overlay
            self.overlay.play_media(
                filepath=data.get("file"), # Cambiado de 'filename' a 'filepath'
                media_type=data.get("type", "audio"), 
                volume=data.get("volume", 100),
                scale=data.get("scale", 1.0),
                pos_x=data.get("pos_x", 0),  # Añadimos X
                pos_y=data.get("pos_y", 0),  # Añadimos Y
                random_pos=data.get("random", False)
                # Eliminamos la línea de duration
            )
            self.page_rewards.log(f"▶️ Enviando alerta a OBS: {data.get('file')}")
        else:
            self.page_rewards.log(f"⚠️ '{recompensa}' no está configurado localmente.")
            self.page_chat.procesar_mensaje_tts("Sistema", f"{usuario} acaba de canjear {recompensa}")

    # === 5. CIERRE SEGURO ===

    def closeEvent(self, event):
        """Apaga los hilos de forma segura al cerrar la ventana."""
        if self.backend and self.backend.isRunning(): self.backend.stop()
        if self.tts and self.tts.isRunning(): self.tts.stop()
        if self.overlay and self.overlay.isRunning(): self.overlay.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = KickMonitorLiteUI()
    ventana.show()
    sys.exit(app.exec())