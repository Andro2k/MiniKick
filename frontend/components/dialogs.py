# frontend/components/dialogs.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget, QProgressBar
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from frontend.theme import COLOR_ACCENT_HOVER, PATH_ICON_HELP, PATH_ICON_UPDATE

# ─── 1. CLASE BASE (Abstracción Estructural) ──────────────────────────────────

class ModernBaseDialog(QDialog):
    """Provee la estructura visual base: Ventana sin bordes, Tarjeta central y Cabecera con Icono."""
    def __init__(self, icon_path: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.container = QFrame()
        self.container.setObjectName("Card")
        self.container.setFixedWidth(400)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(0, 0, 0, 30)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self._setup_header(icon_path)
        self.main_layout.addWidget(self.container)

    def _setup_header(self, icon_path):
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
        icon_lbl.setPixmap(QIcon(icon_path).pixmap(30, 30))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_inner_layout.addWidget(icon_lbl)

        header_layout.addWidget(icon_container)
        self.content_layout.addWidget(header_widget)
        self.content_layout.setContentsMargins(24, -20, 24, 24)

    def add_action_buttons(self, btn_left: QPushButton, btn_right: QPushButton):
        """Método de utilidad para estandarizar la botonera inferior."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setAlignment(Qt.AlignCenter)
        if btn_left: btn_layout.addWidget(btn_left)
        if btn_right: btn_layout.addWidget(btn_right)
        self.content_layout.addLayout(btn_layout)


# ─── 2. IMPLEMENTACIONES ESPECÍFICAS ──────────────────────────────────────────

class ModernConfirmDialog(ModernBaseDialog):
    """Diálogo de confirmación simple."""
    def __init__(self, parent=None, title_text="Confirmar Acción", body_text="¿Estás seguro de que deseas continuar?"):
        super().__init__(PATH_ICON_HELP, parent)
        self.setWindowTitle(title_text)
        
        # Textos
        title_lbl = QLabel(title_text)
        title_lbl.setProperty("role", "title")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        self.content_layout.addWidget(title_lbl)
        self.content_layout.addSpacing(10)

        body_label = QLabel(body_text)
        body_label.setStyleSheet("color: #94A3B8; font-size: 14px; line-height: 1.5;")
        body_label.setAlignment(Qt.AlignCenter)
        body_label.setWordWrap(True)
        self.content_layout.addWidget(body_label)
        self.content_layout.addSpacing(30)

        # Botones
        self.btn_cancel = self._create_btn("Cancelar", "action_outlined", self.reject)
        self.btn_confirm = self._create_btn("Confirmar", "action_accent", self.accept)
        self.add_action_buttons(self.btn_cancel, self.btn_confirm)

    def _create_btn(self, text, role, callback):
        btn = QPushButton(text)
        btn.setProperty("role", role)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumWidth(120)
        btn.clicked.connect(callback)
        return btn


class UpdateDialog(ModernBaseDialog):
    """Diálogo interactivo para actualizaciones."""
    download_requested = Signal() 

    def __init__(self, parent=None):
        super().__init__(PATH_ICON_UPDATE, parent)
        self.setWindowTitle("Actualización del Sistema")
        
        self.title_lbl = QLabel("Buscando Actualizaciones")
        self.title_lbl.setProperty("role", "title")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.title_lbl)
        self.content_layout.addSpacing(10)

        self.status_label = QLabel("Conectando con el servidor...")
        self.status_label.setStyleSheet("color: #94A3B8; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.content_layout.addWidget(self.status_label)
        self.content_layout.addSpacing(25)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("UpdateProgress")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(300)
        sp = self.progress_bar.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.progress_bar.setSizePolicy(sp)
        self.content_layout.addWidget(self.progress_bar)
        self.content_layout.addSpacing(30)

        # Botones
        self.btn_close = QPushButton("Cancelar")
        self.btn_close.setProperty("role", "action_outlined")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setMinimumWidth(120)
        self.btn_close.clicked.connect(self.reject)

        self.action_button = QPushButton("Descargar e Instalar")
        self.action_button.setProperty("role", "action_accent")
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setMinimumWidth(160)
        self.action_button.setVisible(False)
        self.action_button.clicked.connect(self.download_requested.emit)

        self.add_action_buttons(self.btn_close, self.action_button)

    # ... (Los métodos de estado de UpdateDialog permanecen exactamente igual)
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