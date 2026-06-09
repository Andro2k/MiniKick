# frontend/views/dashboard_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal, QUrl, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from frontend.theme import COLOR_ACCENT
from frontend.utils import create_circular_pixmap
from frontend.components.blocks import StatCard, ViewHeader, SettingRow
from frontend.components.controls import ModernButton, ModernSwitch

class DashboardView(QWidget):
    request_connection = Signal()
    auto_start_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self._on_avatar_downloaded)
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)

        self.header = ViewHeader(
            title_text="Dashboard",
            subtitle_text="Gestión de autenticación, conexión automática y estado general del sistema.",
            icon_name="kick.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        self._setup_connection_card()
        self._setup_profile_section()

        self.main_layout.addStretch()

    def _setup_connection_card(self):
        conn_card = QFrame()
        conn_card.setObjectName("Card")
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setContentsMargins(20, 20, 20, 20)
        conn_layout.setSpacing(18)

        self.sw_autostart = ModernSwitch()
        self.sw_autostart.toggled.connect(self.auto_start_toggled.emit)
        
        row_autostart = SettingRow(
            icon_name="plug.svg",
            title_text="Conexión Automática",
            desc_text="Inicia el bot y conecta al chat automáticamente al abrir la aplicación.",
            right_widget=self.sw_autostart
        )

        status_layout = QHBoxLayout()
        self.status_label = QLabel("Estado: Esperando conexión...")
        self.status_label.setProperty("role", "subtitle")

        self.btn_connect = ModernButton("Conectar a Kick", role="action_accent")
        self.btn_connect.setFixedSize(160, 36)
        self.btn_connect.clicked.connect(self.request_connection.emit)

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.btn_connect)

        conn_layout.addWidget(row_autostart)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255,255,255,0.05); margin: 4px 0;")
        conn_layout.addWidget(divider)
        
        conn_layout.addLayout(status_layout)
        self.main_layout.addWidget(conn_card)

    def _setup_profile_section(self):
        self.profile_container = QWidget()
        self.profile_container.setVisible(False)
        self.profile_container.setContentsMargins(0, 0, 0, 0)
        
        profile_layout = QVBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(10) 

        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(10)

        avatar_card = QFrame()
        avatar_card.setObjectName("Card")
        
        avatar_layout = QVBoxLayout(avatar_card)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(140, 140)
        self.lbl_avatar.setScaledContents(True) 
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setText("?")
        self.lbl_avatar.setObjectName("AvatarLabel")
        
        avatar_layout.addWidget(self.lbl_avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        info_card = QFrame()
        info_card.setObjectName("Card")
        info_card.setMinimumHeight(160)
        
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.lbl_username = QLabel("-")
        self.lbl_username.setProperty("role", "title")
        self.lbl_username.setStyleSheet("font-size: 26px; font-weight: 800;")

        self.lbl_bio = QLabel("-")
        self.lbl_bio.setProperty("role", "body")
        self.lbl_bio.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 14px; margin-top: 6px;")

        info_layout.addWidget(self.lbl_username)
        info_layout.addWidget(self.lbl_bio)
        info_layout.addStretch()
        
        top_row_layout.addWidget(avatar_card)
        top_row_layout.addWidget(info_card, stretch=1)

        stats_container = QWidget()
        stats_grid = QGridLayout(stats_container)
        stats_grid.setContentsMargins(0, 0, 0, 0)
        stats_grid.setSpacing(16)

        self.card_followers = StatCard("Seguidores", "users.svg")
        self.card_room = StatCard("ID Sala (Chat)", "hash.svg")
        self.card_category = StatCard("Última Categoría", "device-gamepad.svg") 
        self.card_affiliate = StatCard("Estado Afiliado", "star.svg")
        self.card_vods = StatCard("VODs", "video.svg")

        stats_grid.addWidget(self.card_followers, 0, 0)
        stats_grid.addWidget(self.card_room, 0, 1)
        stats_grid.addWidget(self.card_category, 0, 2)
        stats_grid.addWidget(self.card_affiliate, 1, 0)
        stats_grid.addWidget(self.card_vods, 1, 1)

        stats_grid.setColumnStretch(0, 1)
        stats_grid.setColumnStretch(1, 1)
        stats_grid.setColumnStretch(2, 1)

        profile_layout.addLayout(top_row_layout)
        profile_layout.addWidget(stats_container, stretch=1) 
        
        self.main_layout.addWidget(self.profile_container)

    @Slot(QNetworkReply)
    def _on_avatar_downloaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = create_circular_pixmap(data)
            if not pixmap.isNull():
                self.lbl_avatar.setPixmap(pixmap)
                self.lbl_avatar.setProperty("has_image", True)
                self.lbl_avatar.style().unpolish(self.lbl_avatar)
                self.lbl_avatar.style().polish(self.lbl_avatar)

        reply.deleteLater()

    def set_autostart_state(self, enabled: bool):
        self.sw_autostart.blockSignals(True)
        self.sw_autostart.setChecked(enabled)
        self.sw_autostart.blockSignals(False)

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
        if user_data.get("is_verified", False):
            username += " ✓"
            
        self.lbl_username.setText(username)
        self.lbl_bio.setText(user_data.get("bio", "Sin descripción"))

        self.card_followers.set_value(f"{user_data.get('followers', 0):,}")
        self.card_room.set_value(str(user_data.get("room_id", "-")))
        
        is_affiliate = user_data.get("is_affiliate", False)
        self.card_affiliate.set_value("Afiliado" if is_affiliate else "No Afiliado")

        vods_enabled = user_data.get("vod_enabled", False)
        self.card_vods.set_value("Sí" if vods_enabled else "No")
        self.card_category.set_value(user_data.get("last_category", "Ninguna"))

        url_str = user_data.get("avatar_url", "")
        if url_str:
            self.network_manager.get(QNetworkRequest(QUrl(url_str)))

        self.profile_container.setVisible(True)

    def set_error_state(self, error_message: str):
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setProperty("state", "error")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("Reintentar")
        self.profile_container.setVisible(False)