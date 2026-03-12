# frontend/main_frontend.py

import re
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, 
                             QLabel, QHBoxLayout, QSystemTrayIcon, QStackedWidget,
                             QMenu, QFrame)
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
        
        # Establecemos la fuente y un fondo base para toda la ventana
        self.setStyleSheet("background-color: #0E0E0E; color: #ffffff; font-family: 'Segoe UI', Ubuntu, sans-serif;")
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
        
        if self.btn_autoconectar.isChecked():
            QTimer.singleShot(500, self.iniciar_backend)

    def _configurar_tray_icon(self):
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
        # Contenedor principal que dividirá la pantalla en Izquierda (Sidebar) y Derecha (Contenido)
        main_widget = QWidget()
        main_h_layout = QHBoxLayout(main_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # ==========================================
        # 1. BARRA LATERAL (SIDEBAR)
        # ==========================================
        sidebar = QFrame()
        sidebar.setFixedWidth(64)
        sidebar.setStyleSheet("""
            QFrame { background-color: #121212; border-right: 1px solid #1E1E1E; }
            QPushButton { background: transparent; border: none; padding: 15px 0px; margin: 4px 0px; }
            QPushButton:checked { border-left: 3px solid #53fc18; background-color: #1A1A1A; }
            QPushButton:hover:!checked { background-color: #1A1A1A; border-left: 3px solid #333; }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(5)

        # Logo o icono decorativo superior
        lbl_logo = QLabel()
        lbl_logo.setPixmap(get_icon("kick.svg").pixmap(24, 24))
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("border: none;")
        
        sidebar_layout.addWidget(lbl_logo)
        sidebar_layout.addSpacing(30)

        # Botones de navegación
        self.btn_nav_chat = QPushButton()
        self.btn_nav_chat.setIcon(get_icon("chat.svg"))
        self.btn_nav_chat.setCheckable(True)
        self.btn_nav_chat.setChecked(True) # Inicia activo
        self.btn_nav_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_chat.setToolTip("Chat & Voz (TTS)")
        
        self.btn_nav_rewards = QPushButton()
        self.btn_nav_rewards.setIcon(get_icon("layers.svg"))
        self.btn_nav_rewards.setCheckable(True)
        self.btn_nav_rewards.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_rewards.setToolTip("Canjes & Overlay")

        sidebar_layout.addWidget(self.btn_nav_chat)
        sidebar_layout.addWidget(self.btn_nav_rewards)
        sidebar_layout.addStretch() # Empuja todo hacia arriba

        # ==========================================
        # 2. ÁREA DE CONTENIDO PRINCIPAL (DERECHA)
        # ==========================================
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # --- CABECERA SUPERIOR ---
        header_layout = QHBoxLayout()
        
        self.btn_iniciar = QPushButton(" Conectar")
        self.btn_iniciar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_iniciar.setStyleSheet("""
            QPushButton { background-color: #53fc18; color: black; font-weight: bold; padding: 8px 16px; border-radius: 6px; }
            QPushButton:disabled { background-color: #2c5914; color: #888888; }
            QPushButton:hover:!disabled { background-color: #4ceb15; }
        """)
        self.btn_iniciar.clicked.connect(self.iniciar_backend)

        self.lbl_status = QLabel("Desconectado")
        self.lbl_status.setStyleSheet("color: #777; font-weight: bold; font-size: 13px; margin-left: 10px;")

        # Botón Autoconectar (Icono Plug)
        self.btn_autoconectar = QPushButton(" Auto")
        self.btn_autoconectar.setIcon(get_icon("plug.svg"))
        self.btn_autoconectar.setToolTip("Autoconectar al abrir la app")
        self.btn_autoconectar.setCheckable(True)
        self.btn_autoconectar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_autoconectar.setStyleSheet("""
            QPushButton { background-color: transparent; color: #A0A0A0; border: 1px solid #333; padding: 6px 12px; border-radius: 6px; font-weight: bold; }
            QPushButton:checked { color: #53fc18; border: 1px solid #53fc18; background-color: rgba(83, 252, 24, 0.05); }
            QPushButton:hover:!checked { background-color: #1A1A1A; color: #FFF; border: 1px solid #555; }
        """)
        self.btn_autoconectar.toggled.connect(self.on_autoconect_toggled)

        self.btn_mini = QPushButton(" Ocultar")
        self.btn_mini.setIcon(get_icon("minimize.svg"))
        self.btn_mini.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mini.setStyleSheet("""
            QPushButton { background-color: transparent; color: #A0A0A0; border: 1px solid #333; padding: 6px 12px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #1A1A1A; color: #FFF; border: 1px solid #555; }
        """)
        self.btn_mini.clicked.connect(self.activar_modo_segundo_plano)

        header_layout.addWidget(self.btn_iniciar)
        header_layout.addWidget(self.lbl_status)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_autoconectar)
        header_layout.addWidget(self.btn_mini)

        # --- GESTOR DE PÁGINAS (QStackedWidget) ---
        self.stacked_widget = QStackedWidget()
        
        self.page_chat = ChatPage(self.tts, self.db)
        self.page_rewards = RewardsPage(self.db)

        self.stacked_widget.addWidget(self.page_chat)    # Índice 0
        self.stacked_widget.addWidget(self.page_rewards) # Índice 1

        # Agregar cabecera y páginas al layout de contenido
        content_layout.addLayout(header_layout)
        content_layout.addWidget(self.stacked_widget)

        # ENSAMBLAR TODO
        main_h_layout.addWidget(sidebar)
        main_h_layout.addWidget(content_frame, stretch=1)
        
        self.setCentralWidget(main_widget)

        # Conectar botones del sidebar para cambiar de página
        self.btn_nav_chat.clicked.connect(lambda: self.cambiar_pagina(0, self.btn_nav_chat))
        self.btn_nav_rewards.clicked.connect(lambda: self.cambiar_pagina(1, self.btn_nav_rewards))

        # Cargamos el estado de autoconexión
        is_auto = self.db.get_config("autoconnect", "False") == "True"
        self.btn_autoconectar.blockSignals(True)
        self.btn_autoconectar.setChecked(is_auto)
        self.btn_autoconectar.blockSignals(False)

    def cambiar_pagina(self, index, boton_activo):
        """Maneja el cambio de páginas y el estado visual de los botones del sidebar."""
        self.stacked_widget.setCurrentIndex(index)
        
        # Apagamos todos
        self.btn_nav_chat.setChecked(False)
        self.btn_nav_rewards.setChecked(False)
        
        # Encendemos solo el seleccionado
        boton_activo.setChecked(True)

    def _conectar_senales_servicios(self):
        self.tts.error_signal.connect(lambda msg: self.page_chat.log(f"[TTS ERROR] {msg}"))
        self.overlay.log_signal.connect(lambda msg: self.page_rewards.log(f"[OVERLAY] {msg}"))

    def on_autoconect_toggled(self, checked):
        self.db.set_config("autoconnect", str(checked))
        if checked:
            self.page_chat.log("[SISTEMA] 🔌 Autoconexión activada para el próximo inicio.")
        else:
            self.page_chat.log("[SISTEMA] 🔌 Autoconexión desactivada.")

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

    def iniciar_backend(self):
        if self.btn_iniciar.text() == " Conectado":
            return
        try:
            from backend.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
        except ImportError:
            self.page_chat.log("[ERROR] No se encontró el archivo backend/config.py")
            return

        if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]) or CLIENT_ID == "tu_client_id_aqui":
            self.page_chat.log("[ERROR] Faltan datos en backend/config.py. Por favor, pon tus claves.")
            return

        self.btn_iniciar.setEnabled(False)
        self.btn_iniciar.setText(" Conectado")
        self.lbl_status.setText("En Línea")
        self.lbl_status.setStyleSheet("color: #53fc18; font-weight: bold; font-size: 13px; margin-left: 10px;")
        self.page_chat.log("[INFO] Conectando a los servidores de Kick...")

        self.backend = KickBot(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, self.db)
        self.backend.log_signal.connect(self.page_chat.log)
        self.backend.chat_signal.connect(self.on_chat_recibido)
        self.backend.redemption_signal.connect(self.on_canje_recibido)
        self.backend.rewards_list_signal.connect(self.page_rewards.cargar_recompensas_kick)
        self.page_rewards.request_kick_update.connect(self.backend.update_kick_reward_sync)
        self.backend.start()

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

    def closeEvent(self, event):
        if self.backend and self.backend.isRunning(): self.backend.stop()
        if self.tts and self.tts.isRunning(): self.tts.stop()
        if self.overlay and self.overlay.isRunning(): self.overlay.stop()
        event.accept()