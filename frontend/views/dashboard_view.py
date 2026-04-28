# frontend/views/dashboard_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGridLayout)
from PySide6.QtCore import QByteArray, Qt, Signal, QUrl, Slot
from PySide6.QtGui import QPixmap, QImage, QPainter, QPainterPath, QColor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from frontend.theme import COLOR_BORDER_SVELTE

class DashboardView(QWidget):
    # ─── CONTRATOS DE SALIDA ───
    request_connection = Signal()

    def __init__(self):
        super().__init__()
        # Gestor de red local a la vista para descargar el avatar asíncronamente (SoR)
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self._on_avatar_downloaded)
        self._setup_ui()

    def _setup_ui(self):
        """Construye la interfaz respetando la cohesión visual del tema oscuro"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # --- Encabezado ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        welcome = QLabel("Resumen del Sistema")
        welcome.setProperty("role", "title")
        desc = QLabel("Gestión de autenticación y estado del bot de lectura.")
        desc.setProperty("role", "subtitle")
        header_layout.addWidget(welcome)
        header_layout.addWidget(desc)
        layout.addLayout(header_layout)

        # --- Tarjeta de Conexión ---
        conn_card = QFrame()
        conn_card.setObjectName("Card")
        conn_layout = QHBoxLayout(conn_card)
        conn_layout.setContentsMargins(20, 20, 20, 20)

        self.status_label = QLabel("Estado: Esperando conexión...")
        self.status_label.setProperty("role", "subtitle")
        
        self.btn_connect = QPushButton("Conectar a Kick")
        self.btn_connect.setProperty("role", "action_accent")
        self.btn_connect.setFixedSize(160, 40)
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self.request_connection.emit)

        conn_layout.addWidget(self.status_label)
        conn_layout.addStretch() # Empuja el botón a la derecha
        conn_layout.addWidget(self.btn_connect)
        layout.addWidget(conn_card)

        # =========================================================================
        # --- NUEVA ESTRUCTURA DE PERFIL (Horizontal: Avatar + Stats) ---
        # =========================================================================
        self.profile_container = QWidget() # Contenedor maestro oculto por defecto
        self.profile_container.setVisible(False)
        self.profile_container.setContentsMargins(0, 0, 0, 0)
        
        profile_layout = QHBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(12) # Espacio entre la tarjeta de avatar y la de stats

        # --- Tarjeta 1: Avatar (Anclado a la izquierda) ---
        avatar_card = QFrame()
        avatar_card.setObjectName("Card") # DRY: Reutiliza estilo de tarjeta
        avatar_card.setFixedSize(140, 140) # Tamaño fijo y minimalista
        avatar_layout = QVBoxLayout(avatar_card)
        avatar_layout.setContentsMargins(10, 10, 10, 10) # Padding interno svelte

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setScaledContents(True) # Se expande para llenar
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Placeholder sutil (Alta Cohesión visual)
        self.lbl_avatar.setText("?")
        self.lbl_avatar.setStyleSheet(f"font-size: 40px; color: {COLOR_BORDER_SVELTE}; font-weight: bold;")
        
        avatar_layout.addWidget(self.lbl_avatar)
        profile_layout.addWidget(avatar_card)


        # --- Tarjeta 2: Estadísticas (El Grid existente) ---
        stats_card = QFrame()
        stats_card.setObjectName("Card")
        stats_prof_layout = QVBoxLayout(stats_card)
        stats_prof_layout.setContentsMargins(18, 18, 18, 18)
        stats_prof_layout.setSpacing(12)

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

        # Column 0: Streamer
        self.lbl_username = QLabel("-")
        self.lbl_username.setProperty("role", "stat_value")
        stats_grid.addWidget(make_header("STREAMER"), 0, 0)
        stats_grid.addWidget(self.lbl_username, 1, 0)

        # Column 1: Seguidores
        self.lbl_followers = QLabel("0")
        self.lbl_followers.setProperty("role", "stat_value")
        stats_grid.addWidget(make_header("SEGUIDORES"), 0, 1)
        stats_grid.addWidget(self.lbl_followers, 1, 1)

        # Column 2: ID de Sala
        self.lbl_room = QLabel("-")
        self.lbl_room.setProperty("role", "stat_value")
        stats_grid.addWidget(make_header("ID DE SALA"), 0, 2)
        stats_grid.addWidget(self.lbl_room, 1, 2)

        stats_prof_layout.addLayout(stats_grid)
        profile_layout.addWidget(stats_card) # Añadimos al layout horizontal principal

        layout.addWidget(self.profile_container)
        # =========================================================================

        layout.addStretch() # Resorte final para empujar todo hacia arriba

    # ─── MÉTODOS PRIVADOS DE RENDERIZADO (Alta Cohesión) ───

    def _apply_circular_mask(self, img_data: QByteArray) -> QPixmap:
        """Toma los datos crudos y devuelve un Pixmap circular svelte"""
        image = QImage.fromData(img_data)
        
        if image.isNull():
            return QPixmap()

        # Asegurar un cuadrado perfecto para que el círculo no sea un óvalo
        size = min(image.width(), image.height())
        image = image.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        
        # Salida transparente
        out_img = QImage(size, size, QImage.Format.Format_ARGB32)
        out_img.fill(Qt.GlobalColor.transparent)
        
        # Pintor con Antialiasing (Svelte)
        painter = QPainter(out_img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Crear máscara circular
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        # Dibujar la imagen recortada
        painter.drawImage(0, 0, image)
        
        # Borde ultra-fino opcional (para que no se pierda en el fondo)
        # painter.setPen(QPen(QColor(COLOR_BORDER_SVELTE), 1))
        # painter.drawEllipse(0, 0, size - 1, size - 1)
        
        painter.end()
        return QPixmap.fromImage(out_img)

    @Slot(QNetworkReply)
    def _on_avatar_downloaded(self, reply: QNetworkReply):
        """Callback asíncrono para procesar la imagen (Separación)"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = self._apply_circular_mask(data)
            if not pixmap.isNull():
                self.lbl_avatar.setPixmap(pixmap)
                # Ocultar placeholder de texto si hay imagen
                self.lbl_avatar.setStyleSheet("border: none;") 
        reply.deleteLater()


    # ─── CONTRATOS DE ESTADO (Controlador -> Vista) ───
    def set_connecting_state(self):
        self.status_label.setText("Estado: Autenticando...")
        self.btn_connect.setEnabled(False)
        self.profile_container.setVisible(False)
        self.lbl_avatar.setPixmap(QPixmap()) # Resetear avatar previo

    def set_connected_state(self, user_data: dict):
        """Recibe el diccionario limpio del backend y pinta la interfaz"""
        self.status_label.setText("Estado: Conectado y Escuchando")
        self.status_label.setObjectName("State_Connected") 
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        self.btn_connect.setText("Sistema Activo")
        self.btn_connect.setEnabled(False)

        # Parsear los datos numéricos/texto
        username = user_data.get("username", "Desconocido")
        if user_data.get("is_verified"):
            username += " ✓"
            
        self.lbl_username.setText(username)
        self.lbl_followers.setText(f"{user_data.get('followers', 0):,}")
        self.lbl_room.setText(str(user_data.get("room_id", "-")))

        # --- NUEVO: Iniciar descarga asíncrona del avatar ---
        url_str = user_data.get("avatar_url", "")
        if url_str:
            self.network_manager.get(QNetworkRequest(QUrl(url_str)))
        # ---------------------------------------------------

        # Revelar el contenedor completo (Avatar + Stats)
        self.profile_container.setVisible(True)

    def set_error_state(self, error_message: str):
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #ff6b6b;") 
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("Reintentar")
        self.profile_container.setVisible(False)