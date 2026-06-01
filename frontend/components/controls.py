# frontend/components/controls.py

from PySide6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QAbstractButton, QSizePolicy
from PySide6.QtCore import QRectF, Qt, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath
from frontend.theme import COLOR_ACCENT, COLOR_BG_SURFACE, COLOR_BORDER_SVELTE

# ─── BOTONES BÁSICOS ─────────────────────────────────────────────────────────
class ModernButton(QPushButton):
    """Componente de botón reutilizable con roles de estilo."""
    def __init__(self, text: str, role: str = "action_accent", parent=None):
        super().__init__(text, parent)
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ModernSwitch(QAbstractButton):
    """Componente Switch dibujado nativamente (Alta Cohesión, cero dependencias SVG)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._position = 0.5
        self.toggled.connect(self.update)

    def sizeHint(self) -> QSize:
        return QSize(48, 24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2

        # Colores
        bg_color = QColor(COLOR_ACCENT) if self.isChecked() else QColor(COLOR_BG_SURFACE)
        border_color = QColor(COLOR_ACCENT) if self.isChecked() else QColor(COLOR_BORDER_SVELTE)
        
        # Dibujar Fondo (Pill)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, bg_color)
        
        # Dibujar Borde
        painter.setPen(border_color)
        painter.drawPath(path)

        # Dibujar el "Handle" (Círculo blanco)
        handle_radius = radius - 3
        handle_y = 3
        handle_x = self.width() - handle_radius * 2 - 3 if self.isChecked() else 3
        
        handle_rect = QRectF(handle_x, handle_y, handle_radius * 2, handle_radius * 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFFFFF") if self.isChecked() else QColor("#8C8E96"))
        painter.drawEllipse(handle_rect)
        
        painter.end()

# ─── CONTROLES DE ESTADO (TOGGLES Y SWITCHES) ────────────────────────────────
class SegmentedToggle(QWidget):
    """Control segmentado reutilizable."""
    toggled = Signal(bool)

    def __init__(self, text_left: str, text_right: str, default_right=False, parent=None):
        super().__init__(parent)
        self.is_right_active = default_right
        self._setup_ui(text_left, text_right)

    def _setup_ui(self, text_left, text_right):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_left = QPushButton(text_left)
        self.btn_left.setObjectName("ToggleLeft")
        self.btn_left.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_left.clicked.connect(lambda: self.set_state(False))

        self.btn_right = QPushButton(text_right)
        self.btn_right.setObjectName("ToggleRight")
        self.btn_right.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_right.clicked.connect(lambda: self.set_state(True))

        layout.addWidget(self.btn_left)
        layout.addWidget(self.btn_right)
        self._update_styles()

    def set_state(self, is_right: bool):
        if self.is_right_active != is_right:
            self.is_right_active = is_right
            self._update_styles()
            self.toggled.emit(self.is_right_active)

    def isChecked(self) -> bool:
        return self.is_right_active
        
    def setChecked(self, is_right: bool):
        self.set_state(is_right)

    def _update_styles(self):
        self.btn_left.setProperty("active", not self.is_right_active)
        self.btn_right.setProperty("active", self.is_right_active)
        for btn in (self.btn_left, self.btn_right):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

