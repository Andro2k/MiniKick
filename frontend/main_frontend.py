# frontend/main_frontend.py

import json
import re
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, 
                             QTabWidget, QLabel, QHBoxLayout, QSystemTrayIcon, 
                             QMenu, QApplication)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QTimer

# --- BACKEND (CORE & SERVICIOS) ---
from backend.core.db_manager import DBManager
from backend.core.kick_bot import KickBot
from backend.services.tts_worker import TTSWorker
from backend.services.trigger_worker import OverlayServer

# --- FRONTEND (PÁGINAS Y UTILIDADES) ---
from frontend.pages.chat_page import ChatPage
from frontend.pages.rewards_page import RewardsPage
from frontend.utils import get_icon, resource_path
from frontend.theme import STYLES

class MiniKickUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniKick")
        self.resize(1200, 700)
        self.setStyleSheet("background-color: #0b0e0f; color: #ffffff;")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        # --- 1. INICIALIZAR BASE DE DATOS Y SERVICIOS ---
        self.db = DBManager()     
        self.tts = TTSWorker()
        self.tts.start()  
        self.overlay = OverlayServer()
        self.overlay.start()
        self.backend = None
        self.re_emote_clean = re.compile(r'\[emote:\d+:[^\]]+\]')

        # --- 2. CONFIGURAR MODO SEGUNDO PLANO (TRAY ICON) ---
        self._configurar_tray_icon()

        # --- 3. DIBUJAR INTERFAZ ---
        self.init_ui()
        self._conectar_senales_servicios()
        
        # --- 4. AUTOCONEXIÓN ---
        # Si el botón quedó activado en la sesión anterior, conectamos automáticamente.
        # Usamos un QTimer de medio segundo para darle tiempo a la interfaz a dibujarse 
        # primero y así poder ver los mensajes en la consola.
        if self.btn_autoconectar.isChecked():
            QTimer.singleShot(500, self.iniciar_backend)

    def _configurar_tray_icon(self):
        """Prepara el icono en la bandeja del sistema (junto al reloj)."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("icon.ico")))
        
        tray_menu = QMenu()
        
        action_mostrar = QAction(get_icon("layers.svg"), "Mostrar Dashboard", self)
        action_mostrar.triggered.connect(self.mostrar_ventana)
        
        action_salir = QAction(get_icon("trash.svg"), "Cerrar MiniKick", self)
        action_salir.triggered.connect(self.cerrar_completamente)
        
        tray_menu.addAction(action_mostrar)
        tray_menu.addSeparator()
        tray_menu.addAction(action_salir)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activado)
        self.tray_icon.show()

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

        # Botón Autoconectar
        self.btn_autoconectar = QPushButton(" Autoconectar")
        self.btn_autoconectar.setIcon(get_icon("plug.svg"))
        self.btn_autoconectar.setToolTip("Conectar automáticamente al abrir la aplicación")
        self.btn_autoconectar.setCheckable(True)
        self.btn_autoconectar.setStyleSheet(STYLES["btn_toggle"])
        # Conectamos la señal aquí, pero NO cambiamos su estado todavía
        self.btn_autoconectar.toggled.connect(self.on_autoconect_toggled)

        self.btn_mini = QPushButton(" Segundo Plano")
        self.btn_mini.setIcon(get_icon("minimize.svg"))
        self.btn_mini.setStyleSheet(STYLES["btn_outlined"])
        self.btn_mini.clicked.connect(self.activar_modo_segundo_plano)

        header_layout.addWidget(self.btn_iniciar)
        header_layout.addWidget(self.lbl_status)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_autoconectar)
        header_layout.addWidget(self.btn_mini)

        # === PESTAÑAS (TABS) ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333333;}
            QTabBar::tab { background: #1a1d1e; color: #a0a0a0; padding: 10px 20px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #0b0e0f; color: #53fc18; font-weight: bold; }
        """)

        # ✅ IMPORTANTE: Primero creamos las páginas
        self.page_chat = ChatPage(self.tts, self.db)
        self.page_rewards = RewardsPage(self.db)

        self.tabs.addTab(self.page_chat, get_icon("chat.svg"), "Chat & Voz")
        self.tabs.addTab(self.page_rewards, get_icon("layers.svg"), "Canjes & Overlay")

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # ✅ AHORA SÍ: Cargamos el estado después de que page_chat ya existe
        is_auto = self.db.get_config("autoconnect", "False") == "True"
        self.btn_autoconectar.blockSignals(True)
        self.btn_autoconectar.setChecked(is_auto)
        self.btn_autoconectar.blockSignals(False)

    def _conectar_senales_servicios(self):
        self.tts.error_signal.connect(lambda msg: self.page_chat.log(f"[TTS ERROR] {msg}"))
        self.overlay.log_signal.connect(lambda msg: self.page_rewards.log(f"[OVERLAY] {msg}"))

    # --- LÓGICA DEL BOTÓN AUTOCONECTAR ---
    def on_autoconect_toggled(self, checked):
        """Guarda en la base de datos si queremos autoconectarnos en el futuro."""
        self.db.set_config("autoconnect", str(checked))
        if checked:
            self.page_chat.log("[SISTEMA] 🔌 Autoconexión activada para el próximo inicio.")
        else:
            self.page_chat.log("[SISTEMA] 🔌 Autoconexión desactivada.")

    # --- CONTROLES DEL TRAY (SEGUNDO PLANO) ---
    def activar_modo_segundo_plano(self):
        self.hide()
        self.tray_icon.showMessage(
            "MiniKick",
            "La aplicación sigue ejecutándose en segundo plano.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def mostrar_ventana(self):
        self.showNormal()
        self.activateWindow()

    def on_tray_activado(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.mostrar_ventana()

    def cerrar_completamente(self):
        self.close()

    # --- LÓGICA DE CONEXIÓN KICK ---   
    def iniciar_backend(self):
        # Si ya está corriendo, no hacemos nada (evita doble click o fallos del autoconnect)
        if self.btn_iniciar.text() == "Conectado":
            return
            
        try:
            with open("backend/config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            self.page_chat.log("[ERROR] Crea el archivo backend/config.json con tus claves.")
            return

        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        redirect_uri = config.get("redirect_uri")

        if not all([client_id, client_secret, redirect_uri]):
            self.page_chat.log("[ERROR] Faltan datos en config.json")
            return

        self.btn_iniciar.setEnabled(False)
        self.btn_iniciar.setText("Conectado")
        self.lbl_status.setText("Estado: En Línea")
        self.lbl_status.setStyleSheet("color: #53fc18; font-weight: bold; font-size: 14px; margin-left: 15px;")
        self.page_chat.log("[INFO] Conectando a los servidores de Kick...")

        self.backend = KickBot(client_id, client_secret, redirect_uri, self.db)
        self.backend.log_signal.connect(self.page_chat.log)
        self.backend.chat_signal.connect(self.on_chat_recibido)
        self.backend.redemption_signal.connect(self.on_canje_recibido)
        self.backend.rewards_list_signal.connect(self.page_rewards.cargar_recompensas_kick)
        self.page_rewards.request_kick_update.connect(self.backend.update_kick_reward_sync)
        self.backend.start()

    # --- PROCESAMIENTO DE EVENTOS EN VIVO ---
    def on_chat_recibido(self, usuario, mensaje):
        self.page_chat.log(f"[{usuario}]: {mensaje}")
        
        if usuario.startswith("@") or usuario.lower() in ["streamelements", "botrix", "nightbot"]:
            return
            
        if usuario.lower() in self.db.get_ignored_users():
            return

        mensaje_limpio = self.re_emote_clean.sub('', mensaje).strip()
        self.page_chat.procesar_mensaje_tts(usuario, mensaje_limpio)

    def on_canje_recibido(self, usuario, recompensa, input_texto):
        msg = f"[CANJE] {usuario} canjeó '{recompensa}'"
        if input_texto: 
            msg += f" (Mensaje: {input_texto})"
        self.page_rewards.log(msg)

        nombre_recompensa = recompensa.lower().strip()
        triggers_db = self.db.get_all_triggers()

        if nombre_recompensa in triggers_db:
            data = triggers_db[nombre_recompensa]
            
            if not data.get("enabled", True):
                self.page_rewards.log(f"[WARN] El trigger '{recompensa}' está desactivado.")
                return

            self.overlay.play_media(
                filepath=data.get("file"),
                media_type=data.get("type", "audio"), 
                volume=data.get("volume", 100),
                scale=data.get("scale", 1.0),
                pos_x=data.get("pos_x", 0),
                pos_y=data.get("pos_y", 0),
                random_pos=data.get("random", False)
            )
            self.page_rewards.log(f"[PLAY] Enviando alerta a OBS: {data.get('file')}")
        else:
            self.page_rewards.log(f"[WARN] '{recompensa}' no está configurado localmente.")
            self.page_chat.procesar_mensaje_tts("Sistema", f"{usuario} acaba de canjear {recompensa}")

    # --- CIERRE SEGURO ---
    def closeEvent(self, event):
        if self.backend and self.backend.isRunning(): self.backend.stop()
        if self.tts and self.tts.isRunning(): self.tts.stop()
        if self.overlay and self.overlay.isRunning(): self.overlay.stop()
        event.accept()