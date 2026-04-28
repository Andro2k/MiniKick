# frontend/components/dialogs.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class ModernConfirmDialog(QDialog):
    """
    Diálogo de confirmación con estética Minimalista Svelte (1px border).
    Imita el look de image_e10234.png.
    """
    def __init__(self, parent=None, title_text="Cerrar Aplicación", body_text="¿Estás seguro de que quieres cerrar MiniKick?"):
        super().__init__(parent)
        self.setWindowTitle(title_text)
        # Importante: Ocultar barra de título nativa y fondo transparente para esquinas redondeadas
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._setup_ui(title_text, body_text)

    def _setup_ui(self, title_text, body_text):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) # Espacio para la sombra

        # --- El Contenedor Real (Simula la imagen) ---
        self.container = QFrame()
        self.container.setObjectName("Card") # Hereda el borde de 1px profunda svelte
        
        # Efecto de sombra sutil (Svelte look)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # Icono o Título Principal (Imitando el ! de la imagen)
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("!")
        icon_lbl.setStyleSheet("font-size: 32px; font-weight: bold; color: #ff6b6b; margin-right: 10px;") # Rojo svelte
        
        title_lbl = QLabel(title_text)
        title_lbl.setProperty("role", "subtitle") # Usamos rol svelte
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 700;")
        
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Texto del Cuerpo
        self.body_label = QLabel(body_text)
        self.body_label.setProperty("role", "subtitle") # Color slate svelte
        self.body_label.setWordWrap(True)
        self.body_label.setStyleSheet("font-size: 13px; line-height: 1.5; margin-left: 36px;") # Alineado con el titulo
        layout.addWidget(self.body_label)

        # Botones de Acción (Anclados a la derecha)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        # Botón Cancelar (Svelte Muted Look)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFixedSize(100, 36)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #2D3748;
                border-radius: 6px;
                color: #94A3B8;
            }
            QPushButton:hover {
                background: rgba(148, 163, 184, 0.1);
                color: #f0f0f0;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject) # QDialog.reject

        # Botón Confirmar (Kick Green Accent Pill Shape)
        self.btn_confirm = QPushButton("Sí, cerrar")
        self.btn_confirm.setProperty("role", "action_accent") # Usamos tu estilo pill green
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setFixedSize(110, 36)
        self.btn_confirm.clicked.connect(self.accept) # QDialog.accept

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

        main_layout.addWidget(self.container)