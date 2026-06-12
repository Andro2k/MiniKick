# frontend/views/dashboard_view.py

from PySide6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from frontend.theme import COLOR_ACCENT
from frontend.utils import create_circular_pixmap
from frontend.components.blocks import StatCard, ViewHeader, SettingRow
from frontend.components.controls import ModernButton, ModernSwitch

class DashboardView(QWidget):
    # ─── CONTRATOS DE SALIDA ───
    connect_requested = Signal()
    autostart_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

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

        # ─── ENSAMBLAJE FINAL ───
        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def _setup_connection_card(self):
        # [El código de setup visual se mantiene idéntico a tu versión original]
        conn_card = QFrame()
        conn_card.setObjectName("Card")
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setContentsMargins(10, 10, 10, 10)
        conn_layout.setSpacing(10)

        self.sw_autostart = ModernSwitch()
        self.sw_autostart.toggled.connect(self.autostart_toggled.emit)
        
        row_autostart = SettingRow("plug.svg", "Conexión Automática", "Inicia el bot automáticamente.", self.sw_autostart)

        status_layout = QHBoxLayout()
        self.status_label = QLabel("Estado: Esperando conexión...")
        self.status_label.setProperty("role", "subtitle")

        self.btn_connect = ModernButton("Conectar a Kick", role="action_accent")
        self.btn_connect.setFixedSize(160, 36)
        self.btn_connect.clicked.connect(self.connect_requested.emit)

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
        # [El código de setup visual se mantiene idéntico]
        self.profile_container = QWidget()
        self.profile_container.setVisible(False)
        profile_layout = QVBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(10) 

        top_row_layout = QHBoxLayout()
        avatar_card = QFrame()
        avatar_card.setObjectName("Card")
        avatar_layout = QVBoxLayout(avatar_card)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(140, 140)
        self.lbl_avatar.setScaledContents(True) 
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar.setText("?")
        avatar_layout.addWidget(self.lbl_avatar)

        info_card = QFrame()
        info_card.setObjectName("Card")
        info_card.setMinimumHeight(160)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(10, 10, 10, 10)

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

        profile_layout.addLayout(top_row_layout)
        profile_layout.addWidget(stats_container) 
        self.main_layout.addWidget(self.profile_container)

    # ─── MÉTODOS PÚBLICOS PARA EL CONTROLADOR ───
    def set_autostart_state(self, enabled: bool):
        self.sw_autostart.blockSignals(True)
        self.sw_autostart.setChecked(enabled)
        self.sw_autostart.blockSignals(False)

    def update_connection_status(self, is_connecting: bool, has_error: bool = False, error_msg: str = ""):
        if is_connecting:
            self.status_label.setText("Estado: Autenticando...")
            self.btn_connect.setEnabled(False)
            self.profile_container.setVisible(False)
            self.lbl_avatar.setPixmap(QPixmap())
        elif has_error:
            self.status_label.setText(f"Error: {error_msg}")
            self.status_label.setProperty("state", "error")
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText("Reintentar")
            self.profile_container.setVisible(False)
        else:
            self.status_label.setText("Estado: Conectado y Escuchando")
            self.status_label.setObjectName("State_Connected") 
            self.btn_connect.setText("Sistema Activo")
            self.btn_connect.setEnabled(False)
            self.profile_container.setVisible(True)
            
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def update_profile_info(self, username: str, bio: str):
        self.lbl_username.setText(username)
        self.lbl_bio.setText(bio)

    def update_stats(self, followers: str, room_id: str, category: str, affiliate_text: str, vods_text: str):
        self.card_followers.set_value(followers)
        self.card_room.set_value(room_id)
        self.card_category.set_value(category)
        self.card_affiliate.set_value(affiliate_text)
        self.card_vods.set_value(vods_text)

    def set_avatar_from_bytes(self, image_data: bytes):
        pixmap = create_circular_pixmap(image_data)
        if not pixmap.isNull():
            self.lbl_avatar.setPixmap(pixmap)
            self.lbl_avatar.setProperty("has_image", True)
            self.lbl_avatar.style().unpolish(self.lbl_avatar)
            self.lbl_avatar.style().polish(self.lbl_avatar)
    
    def reset_to_disconnected(self):
        """Devuelve la interfaz al estado de reposo inicial sin conexión."""
        self.status_label.setText("Estado: Esperando conexión...")
        self.status_label.setProperty("state", "idle")
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("Conectar a Kick")
        self.profile_container.setVisible(False)
        self.lbl_avatar.setPixmap(QPixmap())
        
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)