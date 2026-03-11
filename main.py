import sys
import json
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout,
                             QWidget, QPushButton, QTabWidget, QLabel, QHBoxLayout, QCheckBox)
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt

# Importamos nuestros 3 motores del backend
from backend.kick_core import KickMinimalBackend
from backend.tts_worker import TTSWorker
from backend.overlay_server import OverlayMinimalServer

class KickMonitorLiteUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KickMonitor Lite")
        self.resize(700, 450)
        self.setStyleSheet("background-color: #0b0e0f; color: #ffffff;")

        # --- MOTORES INTERNOS ---
        self.backend = None
        
        # 1. Motor de Voz (TTS)
        self.tts = TTSWorker()
        self.tts.error_signal.connect(lambda msg: self.log(self.consola_chat, f"❌ [TTS Error] {msg}"))
        self.tts_enabled = True
        self.tts.start()

        # 2. Servidor Overlay (OBS)
        self.overlay = OverlayMinimalServer()
        self.overlay.log_signal.connect(lambda msg: self.log(self.consola_canjes, f"🖥️ {msg}"))
        self.overlay.start()

        # Filtro de emotes
        self.re_emote_clean = re.compile(r'\[emote:\d+:[^\]]+\]')

        # --- DIBUJAR INTERFAZ ---
        self.init_ui()

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

        # === PESTAÑAS (TABS) ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333333; border-radius: 5px; top: -1px; }
            QTabBar::tab { background: #1a1d1e; color: #a0a0a0; padding: 10px 20px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #0b0e0f; color: #53fc18; font-weight: bold; }
        """)

        # -- PESTAÑA 1: CHAT & VOZ --
        tab_chat = QWidget()
        layout_chat = QVBoxLayout()
        
        self.chk_tts = QCheckBox("Habilitar Lectura de Chat (Voz IA)")
        self.chk_tts.setChecked(True)
        self.chk_tts.setStyleSheet("color: #53fc18; font-weight: bold; margin-bottom: 5px;")
        self.chk_tts.toggled.connect(self.toggle_tts)

        self.consola_chat = QTextEdit()
        self.consola_chat.setReadOnly(True)
        self.consola_chat.setStyleSheet("background-color: #121516; color: #ffffff; font-family: Consolas; font-size: 13px; border: none;")
        
        layout_chat.addWidget(self.chk_tts)
        layout_chat.addWidget(self.consola_chat)
        tab_chat.setLayout(layout_chat)

        # -- PESTAÑA 2: CANJES & OBS --
        tab_canjes = QWidget()
        layout_canjes = QVBoxLayout()
        
        info_obs = QLabel("URL para OBS (Fuente de Navegador): <b style='color:#53fc18;'>http://127.0.0.1:8081</b> (Ancho 1920, Alto 1080)")
        info_obs.setTextFormat(Qt.TextFormat.RichText)
        info_obs.setStyleSheet("background-color: #121516; padding: 10px; border: 1px solid #333; border-radius: 4px; margin-bottom: 5px;")
        info_obs.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.consola_canjes = QTextEdit()
        self.consola_canjes.setReadOnly(True)
        self.consola_canjes.setStyleSheet("background-color: #121516; color: #00e5ff; font-family: Consolas; font-size: 13px; border: none;")

        layout_canjes.addWidget(info_obs)
        layout_canjes.addWidget(self.consola_canjes)
        tab_canjes.setLayout(layout_canjes)

        # Añadir las pestañas al widget principal
        self.tabs.addTab(tab_chat, "💬 Chat & Voz")
        self.tabs.addTab(tab_canjes, "🎁 Canjes & Overlay")

        # Armar ventana
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    # === FUNCIONES DE LÓGICA ===
    def toggle_tts(self, checked):
        self.tts_enabled = checked
        if not checked:
            self.tts.immediate_stop()
        self.log(self.consola_chat, f"🎙️ [SISTEMA] TTS {'Activado' if checked else 'Desactivado'}.")

    def log(self, consola, mensaje):
        consola.append(mensaje)
        consola.moveCursor(QTextCursor.MoveOperation.End)

    def iniciar_backend(self):
        try:
            with open("backend/config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            self.log(self.consola_chat, "❌ ERROR: Crea el archivo backend/config.json con tus claves.")
            return

        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        redirect_uri = config.get("redirect_uri")

        if not all([client_id, client_secret, redirect_uri]):
            self.log(self.consola_chat, "❌ ERROR: Faltan datos en config.json")
            return

        self.btn_iniciar.setEnabled(False)
        self.btn_iniciar.setText("Conectado")
        self.lbl_status.setText("Estado: 🟢 En Línea")
        self.lbl_status.setStyleSheet("color: #53fc18; font-weight: bold; font-size: 14px; margin-left: 15px;")
        self.log(self.consola_chat, "🚀 Conectando a los servidores de Kick...")

        self.backend = KickMinimalBackend(client_id, client_secret, redirect_uri)
        self.backend.log_signal.connect(lambda msg: self.log(self.consola_chat, msg))
        self.backend.chat_signal.connect(self.on_chat_recibido)
        self.backend.redemption_signal.connect(self.on_canje_recibido)
        self.backend.start()

    def on_chat_recibido(self, usuario, mensaje):
        self.log(self.consola_chat, f"[{usuario}]: {mensaje}")
        
        # Ignorar bots
        if usuario.startswith("@") or usuario.lower() in ["streamelements", "botrix", "nightbot"]:
            return

        # Mandar al TTS
        if self.tts_enabled:
            mensaje_limpio = self.re_emote_clean.sub('', mensaje).strip()
            if mensaje_limpio:
                self.tts.add_message(f"{usuario} dice: {mensaje_limpio}")

    def on_canje_recibido(self, usuario, recompensa, input_texto):
        # 1. Registrar en la consola secundaria
        msg = f"🎁 {usuario} canjeó '{recompensa}'"
        if input_texto: msg += f" (Mensaje: {input_texto})"
        self.log(self.consola_canjes, msg)

        # 2. Leer archivo de Triggers local
        try:
            with open("triggers.json", "r", encoding="utf-8") as f:
                triggers = json.load(f)
        except:
            triggers = {}

        nombre_recompensa = recompensa.lower().strip()

        # 3. Disparar multimedia si existe, o leer por TTS si no existe
        if nombre_recompensa in triggers:
            data = triggers[nombre_recompensa]
            self.overlay.play_media(data["file"], data.get("type", "audio"), data.get("volume", 100))
            self.log(self.consola_canjes, f"▶️ Enviando alerta a OBS: {data['file']}")
        else:
            self.log(self.consola_canjes, f"⚠️ '{recompensa}' no está en triggers.json.")
            if self.tts_enabled:
                self.tts.add_message(f"{usuario} acaba de canjear {recompensa}")

    def closeEvent(self, event):
        """Apaga los 3 motores de forma limpia."""
        if self.backend and self.backend.isRunning(): self.backend.stop()
        if self.tts and self.tts.isRunning(): self.tts.stop()
        if self.overlay and self.overlay.isRunning(): self.overlay.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = KickMonitorLiteUI()
    ventana.show()
    sys.exit(app.exec())