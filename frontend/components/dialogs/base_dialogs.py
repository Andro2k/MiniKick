# frontend/components/dialogs/base_dialogs.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from frontend.theme import PATH_ICON_HELP

class ModernBaseDialog(QDialog):
    """Clase madre de la que heredan todos los diálogos de la aplicación."""
    def __init__(self, title: str, icon_path: str, icon_bg_color: str, width: int = 420, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame()
        self.container.setObjectName("SquareDialog")
        self.container.setFixedWidth(width)
        self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(12)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._setup_header(icon_path, icon_bg_color)
        
        if title:
            self.title_lbl = QLabel(title)
            self.title_lbl.setProperty("role", "title")
            self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_lbl.setWordWrap(True)
            self.content_layout.addWidget(self.title_lbl)
            self.content_layout.addSpacing(12)

        self.main_layout.addWidget(self.container)

    def _setup_header(self, icon_path: str, bg_color: str):
        icon_wrapper = QHBoxLayout()
        icon_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_container = QFrame()
        icon_size = 52
        icon_container.setFixedSize(icon_size, icon_size)
        role = "danger_icon" if bg_color == "#EF4444" else "accent_icon"
        icon_container.setProperty("dialog_role", role)
        
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
        
        self.content_layout.addSpacing(12)
        self.content_layout.addLayout(btn_layout)

class ModernConfirmDialog(ModernBaseDialog):
    """Diálogo genérico para confirmar acciones destructivas o importantes."""
    def __init__(self, parent=None, title_text="Desvincular Cuenta", body_text="¿Estás seguro de que deseas continuar? Esta acción no se puede deshacer."):
        super().__init__(title=title_text, icon_path=PATH_ICON_HELP, icon_bg_color="#EF4444", width=420, parent=parent)
        
        body_label = QLabel(body_text)
        body_label.setProperty("role", "body")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        body_label.setMinimumHeight(60) 
        
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