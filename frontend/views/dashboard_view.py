import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal, QUrl, Slot
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from frontend.theme import COLOR_BORDER_SVELTE
from frontend.utils import create_circular_pixmap, get_icon, get_icon_colored

class DashboardView(QWidget):
    # ─── CONTRATOS DE SALIDA ───
    request_connection = Signal()
    auto_start_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self._on_avatar_downloaded)
        self._setup_ui()

    def _setup_ui(self):
        """Construye la interfaz delegando en submétodos para mejor lectura"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self._setup_header(layout)
        self._setup_connection_card(layout)
        self._setup_profile_section(layout)

        layout.addStretch()

    def _setup_header(self, parent_layout: QVBoxLayout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        welcome = QLabel("Resumen del Sistema")
        welcome.setProperty("role", "title")
        desc = QLabel("Gestión de autenticación y estado del bot de lectura.")
        desc.setProperty("role", "subtitle")
        header_layout.addWidget(welcome)
        header_layout.addWidget(desc)
        parent_layout.addLayout(header_layout)

    def _setup_connection_card(self, parent_layout: QVBoxLayout):
        conn_card = QFrame()
        conn_card.setObjectName("Card")
        conn_layout = QHBoxLayout(conn_card)
        conn_layout.setContentsMargins(20, 20, 20, 20)

        self.status_label = QLabel("Estado: Esperando conexión...")
        self.status_label.setProperty("role", "subtitle")
        
        self.btn_autostart = QPushButton()
        self.btn_autostart.setFixedSize(40, 40)
        self.btn_autostart.setCheckable(True) 
        self.btn_autostart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_autostart.toggled.connect(self._update_autostart_visuals)
        
        # Forzamos estado inicial visual (falso por defecto)
        self._update_autostart_visuals(False)

        # Conectamos la señal de salida para el Controlador (MainWindow)
        self.btn_autostart.toggled.connect(self.auto_start_toggled.emit)

        self.btn_connect = QPushButton("Conectar a Kick")
        self.btn_connect.setProperty("role", "action_accent")
        self.btn_connect.setFixedSize(160, 40)
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self.request_connection.emit)

        conn_layout.addWidget(self.status_label)
        conn_layout.addStretch() 
        conn_layout.addWidget(self.btn_autostart) 
        conn_layout.addWidget(self.btn_connect)
        parent_layout.addWidget(conn_card)

    def _setup_profile_section(self, parent_layout: QVBoxLayout):
        self.profile_container = QWidget()
        self.profile_container.setVisible(False)
        self.profile_container.setContentsMargins(0, 0, 0, 0)
        
        profile_layout = QHBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(8) 

        # --- Tarjeta 1: Avatar (Anclado a la izquierda) ---
        avatar_card = QFrame()
        avatar_card.setObjectName("Card") 
        avatar_card.setFixedSize(140, 140) 
        avatar_layout = QVBoxLayout(avatar_card)
        avatar_layout.setContentsMargins(10, 10, 10, 10) 

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setScaledContents(True) 
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_avatar.setText("?")
        self.lbl_avatar.setStyleSheet(f"font-size: 40px; color: {COLOR_BORDER_SVELTE}; font-weight: bold;")
        
        avatar_layout.addWidget(self.lbl_avatar)
        profile_layout.addWidget(avatar_card)
 
        # --- Tarjeta 2: Estadísticas ---
        stats_card = QFrame()
        stats_card.setObjectName("Card")
        stats_prof_layout = QVBoxLayout(stats_card)
        stats_prof_layout.setContentsMargins(16, 16, 16, 16)
        stats_prof_layout.setSpacing(8)

        prof_title = QLabel("ESTADÍSTICAS DEL CANAL")
        prof_title.setProperty("role", "section")
        stats_prof_layout.addWidget(prof_title)

        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(60)
        stats_grid.setVerticalSpacing(8)

        def make_header(text):
            lbl = QLabel(text)
            lbl.setProperty("role", "section")
            return lbl

        self.lbl_username = QLabel("-")
        self.lbl_username.setProperty("role", "stat_value")
        stats_grid.addWidget(make_header("STREAMER"), 0, 0)
        stats_grid.addWidget(self.lbl_username, 1, 0)

        self.lbl_followers = QLabel("0")
        self.lbl_followers.setProperty("role", "stat_value")
        stats_grid.addWidget(make_header("SEGUIDORES"), 0, 1)
        stats_grid.addWidget(self.lbl_followers, 1, 1)

        self.lbl_room = QLabel("-")
        self.lbl_room.setProperty("role", "stat_value")
        stats_grid.addWidget(make_header("ID DE SALA"), 0, 2)
        stats_grid.addWidget(self.lbl_room, 1, 2)

        stats_prof_layout.addLayout(stats_grid)
        profile_layout.addWidget(stats_card) 

        parent_layout.addWidget(self.profile_container)

    @Slot(QNetworkReply)
    def _on_avatar_downloaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = create_circular_pixmap(data)
            if not pixmap.isNull():
                self.lbl_avatar.setPixmap(pixmap)
                self.lbl_avatar.setStyleSheet("border: none;") 
        reply.deleteLater()

   # ─── NUEVO SLOT INTERNO USANDO UTILS.PY ───
    @Slot(bool)
    def _update_autostart_visuals(self, checked: bool):
        """Maneja el cambio de icono usando la utilidad centralizada de frontend/utils.py"""
        
        if checked:
            icon = get_icon_colored("plug.svg", "black", size=22)
            self.btn_autostart.setToolTip("Desactivar Inicio Automático")
        else:
            icon = get_icon("plug.svg") 
            self.btn_autostart.setToolTip("Activar Inicio Automático")
            
        self.btn_autostart.setIcon(icon)


    # ─── CONTRATOS DE ESTADO (Controlador -> Vista) ───
    def set_autostart_state(self, enabled: bool):
        self.btn_autostart.blockSignals(True)
        self.btn_autostart.setChecked(enabled)
        self._update_autostart_visuals(enabled) 
        self.btn_autostart.blockSignals(False)

    def set_connecting_state(self):
        self.status_label.setText("Estado: Autenticando...")
        self.btn_connect.setEnabled(False)
        self.profile_container.setVisible(False)
        self.lbl_avatar.setPixmap(QPixmap()) 

    def set_connected_state(self, user_data: dict):
        self.status_label.setText("Estado: Conectado y Escuchando")
        self.status_label.setObjectName("State_Connected") 
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        self.btn_connect.setText("Sistema Activo")
        self.btn_connect.setEnabled(False)

        username = user_data.get("username", "Desconocido")
        if user_data.get("is_verified"):
            username += " ✓"
            
        self.lbl_username.setText(username)
        self.lbl_followers.setText(f"{user_data.get('followers', 0):,}")
        self.lbl_room.setText(str(user_data.get("room_id", "-")))

        url_str = user_data.get("avatar_url", "")
        if url_str:
            self.network_manager.get(QNetworkRequest(QUrl(url_str)))

        self.profile_container.setVisible(True)

    def set_error_state(self, error_message: str):
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #ff6b6b;") 
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("Reintentar")
        self.profile_container.setVisible(False)