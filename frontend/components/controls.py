# frontend/components/controls.py

from PySide6.QtWidgets import QPushButton, QAbstractButton, QSizePolicy
from PySide6.QtCore import QRectF, Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath
from frontend.theme import COLOR_ACCENT, COLOR_BG_INPUT, COLOR_BORDER_SVELTE, RADIUS_MD, RADIUS_SM

class ModernButton(QPushButton):
    """Componente de botón reutilizable con roles de estilo."""
    def __init__(self, text: str, role: str = "action_accent", parent=None):
        super().__init__(text, parent)
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ModernSwitch(QAbstractButton):
    """Componente Switch dibujado nativamente adaptado al sistema de diseño."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.toggled.connect(self.update)

    def sizeHint(self) -> QSize:
        return QSize(48, 24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, self.width(), self.height())

        bg_color = QColor(COLOR_ACCENT) if self.isChecked() else QColor(COLOR_BG_INPUT)
        border_color = QColor(COLOR_ACCENT) if self.isChecked() else QColor(COLOR_BORDER_SVELTE)

        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS_MD, RADIUS_MD)
        painter.fillPath(path, bg_color)

        painter.setPen(border_color)
        painter.drawPath(path)

        padding = 3
        handle_size = self.height() - (padding * 2)
        handle_x = self.width() - handle_size - padding if self.isChecked() else padding
        
        handle_rect = QRectF(handle_x, padding, handle_size, handle_size)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#42474D") if self.isChecked() else QColor("#ffffff"))
        painter.drawRoundedRect(handle_rect, RADIUS_SM, RADIUS_SM)
        
        painter.end()
