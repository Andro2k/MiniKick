# frontend/components/update_dialog.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget, QProgressBar
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from frontend.theme import COLOR_ACCENT_HOVER, PATH_ICON_UPDATE

class UpdateDialog(QDialog):
    """
    Diálogo de actualización con diseño plano (Flat).
    """
    download_requested = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actualización del Sistema")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) 
        main_layout.setAlignment(Qt.AlignCenter)

        # --- Contenedor Principal (Tarjeta sin sombra) ---
        self.container = QFrame()
        self.container.setObjectName("Card")
        self.container.setFixedWidth(400)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 30)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # ─── Acento Superior (Círculo con Icono) ───
        header_widget = QWidget()
        header_widget.setFixedHeight(60) 
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignCenter)

        icon_container = QFrame()
        icon_size = 60
        icon_container.setFixedSize(icon_size, icon_size)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_ACCENT_HOVER};
                border-radius: {icon_size // 2}px;
                border: none;
            }}
        """)
        
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(10, 10, 10, 10)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QIcon(PATH_ICON_UPDATE).pixmap(30, 30))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_inner_layout.addWidget(icon_lbl)

        header_layout.addWidget(icon_container)
        
        layout.addWidget(header_widget)
        layout.setContentsMargins(24, -20, 24, 24)

        # ─── Contenido Centrado ───
        self.title_lbl = QLabel("Buscando Actualizaciones")
        self.title_lbl.setProperty("role", "title")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        layout.addWidget(self.title_lbl)
        layout.addSpacing(10)

        self.status_label = QLabel("Conectando con el servidor...")
        self.status_label.setStyleSheet("color: #94A3B8; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addSpacing(25)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("UpdateProgress")
        self.progress_bar.setRange(0, 0) 
        self.progress_bar.setFixedWidth(300)
        
        # --- AÑADE ESTAS 3 LÍNEAS AQUÍ ---
        sp = self.progress_bar.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.progress_bar.setSizePolicy(sp)
        # ---------------------------------
        
        layout.addWidget(self.progress_bar)
        layout.addSpacing(30)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.action_button = QPushButton("Descargar e Instalar")
        self.action_button.setProperty("role", "action_accent")
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setMinimumWidth(160)
        self.action_button.setVisible(False)
        self.action_button.clicked.connect(self.download_requested.emit) 

        self.btn_close = QPushButton("Cancelar")
        self.btn_close.setProperty("role", "action_outlined")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setMinimumWidth(120)
        self.btn_close.clicked.connect(self.reject) 

        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.action_button)
        layout.addLayout(btn_layout)

        main_layout.addWidget(self.container)

    def show_update_available(self, version: str):
        self.title_lbl.setText("Actualización Disponible")
        self.status_label.setText(f"¡Nueva versión {version} está lista para descargar!")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.action_button.setVisible(True) 
        self.btn_close.setText("Quizás luego")

    def show_downloading(self):
        self.title_lbl.setText("Descargando Actualización")
        self.status_label.setText("Por favor espera, no cierres la aplicación.")
        self.progress_bar.setRange(0, 0) 
        self.action_button.setEnabled(False)
        self.btn_close.setVisible(False) 

    def show_no_update(self):
        self.title_lbl.setText("Sistema Actualizado")
        self.status_label.setText("Tu versión de MiniKick ya es la última disponible.")
        self.progress_bar.setVisible(False)
        self.btn_close.setText("Cerrar")
        self.btn_close.setProperty("role", "action_accent") 

    def show_error(self, message: str):
        self.title_lbl.setText("Error de Actualización")
        self.status_label.setText(f"Ocurrió un fallo: {message}")
        self.progress_bar.hide()
        self.action_button.setVisible(False)
        self.btn_close.setText("Cerrar")
        self.btn_close.setVisible(True)
        self.btn_close.setEnabled(True)