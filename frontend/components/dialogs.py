# frontend/components/dialogs.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from frontend.theme import COLOR_ACCENT_HOVER, PATH_ICON_HELP

class ModernConfirmDialog(QDialog):
    """
    Diálogo de confirmación con diseño plano (Flat) centralizado.
    """
    def __init__(self, parent=None, title_text="Confirmar Acción", body_text="¿Estás seguro de que deseas continuar?"):
        super().__init__(parent)
        self.setWindowTitle(title_text)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui(title_text, body_text)

    def _setup_ui(self, title_text, body_text):
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
        icon_lbl.setPixmap(QIcon(PATH_ICON_HELP).pixmap(30, 30))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_inner_layout.addWidget(icon_lbl)

        header_layout.addWidget(icon_container)
        
        layout.addWidget(header_widget)
        layout.setContentsMargins(24, -20, 24, 24) 

        # ─── Contenido Centrado ───
        title_lbl = QLabel(title_text)
        title_lbl.setProperty("role", "title") 
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)
        layout.addSpacing(10)

        self.body_label = QLabel(body_text)
        self.body_label.setStyleSheet("color: #94A3B8; font-size: 14px; line-height: 1.5;")
        self.body_label.setAlignment(Qt.AlignCenter)
        self.body_label.setWordWrap(True)
        layout.addWidget(self.body_label)
        layout.addSpacing(30)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("role", "action_outlined") 
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setMinimumWidth(120)
        self.btn_cancel.clicked.connect(self.reject) 

        self.btn_confirm = QPushButton("Confirmar")
        self.btn_confirm.setProperty("role", "action_accent") 
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setMinimumWidth(120)
        self.btn_confirm.clicked.connect(self.accept) 

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

        main_layout.addWidget(self.container)