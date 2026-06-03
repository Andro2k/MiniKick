# frontend/components/controls.py

from PySide6.QtWidgets import QPushButton, QAbstractButton, QSizePolicy
from PySide6.QtCore import QRectF, Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath
from frontend.theme import COLOR_ACCENT, COLOR_BG_INPUT, COLOR_BORDER_SVELTE

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
        self._position = 0.0
        self.toggled.connect(self.update)

    def sizeHint(self) -> QSize:
        return QSize(48, 24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2

        # Colores
        bg_color = QColor(COLOR_ACCENT) if self.isChecked() else QColor(COLOR_BG_INPUT)
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
