# frontend\widgets\controls_component.py

from PySide6.QtWidgets import QPushButton, QAbstractButton, QSizePolicy
from PySide6.QtCore import QRectF, Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath
from frontend.common.theme import COLOR_GREEN, COLOR_NEUTRAL_850, COLOR_NEUTRAL_800, COLOR_NEUTRAL_100

class ModernButton(QPushButton):
    def __init__(self, text: str, role: str = "action_accent", parent=None):
        super().__init__(text, parent)
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ModernSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.toggled.connect(self.update)

    def sizeHint(self) -> QSize:
        return QSize(44, 22)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 1.7

        bg_color = QColor(COLOR_GREEN) if self.isChecked() else QColor(COLOR_NEUTRAL_850)
        border_color = QColor(COLOR_GREEN) if self.isChecked() else QColor(COLOR_NEUTRAL_800)

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, bg_color)

        painter.setPen(border_color)
        painter.drawPath(path)

        padding = 3
        handle_size = self.height() - (padding * 2)
        handle_x = self.width() - handle_size - padding if self.isChecked() else padding
        
        handle_rect = QRectF(handle_x, padding, handle_size, handle_size)
        handle_radius = handle_size / 2.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLOR_NEUTRAL_100))
        painter.drawRoundedRect(handle_rect, handle_radius, handle_radius)
        
        painter.end()
