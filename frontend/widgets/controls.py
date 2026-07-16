# frontend\widgets\controls.py

from PySide6.QtWidgets import QPushButton, QAbstractButton, QSizePolicy, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import QRectF, Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath
from frontend.common.theme import COLOR_GREEN, COLOR_NEUTRAL_850, COLOR_NEUTRAL_800, COLOR_WHITE
from frontend.common.utils import NoWheelSlider

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
        radius = self.height() / 1.8

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
        painter.setBrush(QColor(COLOR_WHITE))
        painter.drawRoundedRect(handle_rect, handle_radius, handle_radius)
        
        painter.end()

class CompactSlider(QWidget):
    def __init__(self, min_val: int, max_val: int, init_val: int, suffix: str = "", parent=None):
        super().__init__(parent)
        self.suffix = suffix
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self.slider = NoWheelSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(init_val)
        self.slider.setFixedWidth(140)
        
        self.label = QLabel(self._format_value(init_val))
        self.label.setFixedWidth(40)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.slider)
        layout.addWidget(self.label)
        
    def _format_value(self, val: int) -> str:
        if self.suffix == "s" and val == 0:
            return "Nunca"
        return f"{val}{self.suffix}"
        
    def _on_value_changed(self, val: int):
        self.label.setText(self._format_value(val))
        
    def value(self) -> int:
        return self.slider.value()
        
    def setValue(self, val: int):
        self.slider.setValue(val)
        self.label.setText(self._format_value(val))
