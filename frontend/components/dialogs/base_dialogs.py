# frontend/components/dialogs/base_dialogs.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor

from frontend.theme import PATH_ICON_HELP

class ModernBaseDialog(QDialog):
    """Clase madre de la que heredan todos los diálogos de la aplicación."""
    def __init__(self, title: str = "", icon_path: str = "", icon_bg_color: str = "", width: int = 420, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame()
        self.container.setProperty("role", "dialog")
        self.container.setProperty("state", "neutral")
        self.container.setFixedWidth(width)
        self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(30)
        self.glow.setOffset(0, 0)
        self.glow.setColor(QColor(0, 0, 0, 0))
        self.container.setGraphicsEffect(self.glow)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(12)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        if icon_path:
            self._setup_header(icon_path, icon_bg_color)
        
        if title:
            self.title_lbl = QLabel(title)
            self.title_lbl.setProperty("role", "h1")
            self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_lbl.setWordWrap(True)
            self.content_layout.addWidget(self.title_lbl)
            self.content_layout.addSpacing(12)

        self.main_layout.addWidget(self.container)

    def set_dialog_state(self, state: str, glow_color: QColor = None):
        """Cambia el borde y el color del glow de forma dinámica."""
        self.container.setProperty("state", state)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        
        if glow_color:
            self.glow.setColor(glow_color)
        else:
            self.glow.setColor(QColor(0, 0, 0, 0))

    def _setup_header(self, icon_path: str, bg_color: str):
        icon_wrapper = QHBoxLayout()
        icon_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_container = QFrame()
        icon_container.setFixedSize(52, 52)
        role = "danger_icon" if bg_color == "#EF4444" else "accent_icon"
        icon_container.setProperty("dialog_role", role)
        
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(0, 0, 0, 0)
        icon_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QIcon(icon_path).pixmap(24, 24))
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
    def __init__(self, i18n, parent=None, title_text="", body_text=""):
        super().__init__(title=title_text, icon_path=PATH_ICON_HELP, icon_bg_color="#EF4444", width=420, parent=parent)
        self.i18n = i18n
        self.set_dialog_state("danger", QColor(239, 68, 68, 60))
        
        body_label = QLabel(body_text)
        body_label.setProperty("role", "body")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        body_label.setMinimumHeight(60) 
        
        self.content_layout.addWidget(body_label)
        self.btn_confirm = self._create_btn(self.i18n.get("dialogs.confirm.btn_continue"), "action_danger", self.accept)
        self.btn_cancel = self._create_btn(self.i18n.get("dialogs.confirm.btn_cancel"), "action_outlined", self.reject)
        self.add_action_buttons(self.btn_confirm, self.btn_cancel)

    def _create_btn(self, text, role, callback):
        btn = QPushButton(text)
        btn.setProperty("role", role)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumWidth(120)
        btn.clicked.connect(callback)
        return btn