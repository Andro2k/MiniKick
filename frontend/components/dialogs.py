# frontend/components/dialogs.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from frontend.theme import COLOR_ACCENT, PATH_ICON_HELP, PATH_ICON_UPDATE

# ─── 1. CLASE BASE (Abstracción Estructural - SoR & DRY) ──────────────────────
class ModernBaseDialog(QDialog):
    """Provee la estructura visual base inspirada en el diseño centrado."""
    
    def __init__(self, icon_path: str, icon_bg_color: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Forzar al diálogo a adaptarse dinámicamente al contenido (Evita cortes de texto)
        self.main_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        self.container = QFrame()
        # Se elimina objectName("Card") para no heredar los bordes redondeados de theme.py
        self.container.setObjectName("SquareDialog")
        # Alta Cohesión: El estilo cuadrado vive estrictamente en el componente que lo necesita
        self.container.setStyleSheet(f"""
            QFrame#SquareDialog {{
                background-color: #1E2329;
                border: 1px solid #333333; 
            }}
        """)
        self.container.setFixedWidth(420)
        self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(32, 32, 32, 32)
        self.content_layout.setSpacing(12)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._setup_header(icon_path, icon_bg_color)
        self.main_layout.addWidget(self.container)

    def _setup_header(self, icon_path: str, bg_color: str):
        icon_wrapper = QHBoxLayout()
        icon_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_container = QFrame()
        icon_size = 52
        icon_container.setFixedSize(icon_size, icon_size)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: {icon_size // 2}px;
                border: none;
            }}
        """)
        
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(0, 0, 0, 0)
        icon_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QIcon(icon_path).pixmap(24, 24))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_inner_layout.addWidget(icon_lbl)

        icon_wrapper.addWidget(icon_container)
        
        self.content_layout.addLayout(icon_wrapper)
        self.content_layout.addSpacing(8) 

    def add_action_buttons(self, btn_primary: QPushButton, btn_secondary: QPushButton):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if btn_primary: btn_layout.addWidget(btn_primary)
        if btn_secondary: btn_layout.addWidget(btn_secondary)
        
        self.content_layout.addSpacing(16)
        self.content_layout.addLayout(btn_layout)


# ─── 2. IMPLEMENTACIONES ESPECÍFICAS (Alta Cohesión) ──────────────────────────
class ModernConfirmDialog(ModernBaseDialog):
    
    def __init__(self, parent=None, title_text="Desvincular Cuenta", body_text="¿Estás seguro de que deseas continuar? Esta acción no se puede deshacer."):
        super().__init__(PATH_ICON_HELP, "#EF4444", parent)
        self.setWindowTitle(title_text)
        
        title_lbl = QLabel(title_text)
        title_lbl.setProperty("role", "title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setWordWrap(True)
        self.content_layout.addWidget(title_lbl)

        body_label = QLabel(body_text)
        body_label.setStyleSheet("color: #9CA3AF; font-size: 13px; line-height: 1.5;")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        # Política para asegurar que empuje el layout hacia abajo en lugar de cortarse
        body_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.content_layout.addWidget(body_label)

        self.btn_confirm = self._create_btn("Continuar", "action_danger", self.accept)
        self.btn_cancel = self._create_btn("Cancelar", "action_outlined", self.reject)
        self.add_action_buttons(self.btn_confirm, self.btn_cancel)

    def _create_btn(self, text, role, callback):
        btn = QPushButton(text)
        btn.setProperty("role", role)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumWidth(120)
        btn.clicked.connect(callback)
        return btn


class UpdateDialog(ModernBaseDialog):
    download_requested = Signal() 

    def __init__(self, parent=None):
        super().__init__(PATH_ICON_UPDATE, COLOR_ACCENT, parent)
        self.setWindowTitle("Actualización del Sistema")
        
        self.title_lbl = QLabel("Buscando Actualizaciones")
        self.title_lbl.setProperty("role", "title")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.title_lbl)

        self.status_label = QLabel("Conectando con el servidor...")
        self.status_label.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.content_layout.addWidget(self.status_label)

        pb_layout = QHBoxLayout()
        pb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("UpdateProgress")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(280)
        sp = self.progress_bar.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.progress_bar.setSizePolicy(sp)
        
        pb_layout.addWidget(self.progress_bar)
        self.content_layout.addSpacing(10)
        self.content_layout.addLayout(pb_layout)

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

        self.add_action_buttons(self.action_button, self.btn_close)

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
        self.btn_close.style().unpolish(self.btn_close)
        self.btn_close.style().polish(self.btn_close)

    def show_error(self, message: str):
        self.title_lbl.setText("Error de Actualización")
        self.status_label.setText(f"Ocurrió un fallo: {message}")
        self.progress_bar.hide()
        self.action_button.setVisible(False)
        self.btn_close.setText("Cerrar")
        self.btn_close.setVisible(True)
        self.btn_close.setEnabled(True)

