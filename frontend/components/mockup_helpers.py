# frontend\components\mockup_helpers.py

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtWidgets import QWidget
from frontend.common import COLOR_NEUTRAL_800, COLOR_NEUTRAL_950

def init_mockup_painter(widget: QWidget) -> tuple[QPainter, float, float]:
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    return painter, float(widget.width()), float(widget.height())

def draw_mockup_canvas(
    painter: QPainter,
    w: float,
    h: float,
    border_color: str = COLOR_NEUTRAL_800,
    bg_color: str = COLOR_NEUTRAL_950,
    radius: float = 10.0
) -> QRectF:
    canvas_rect = QRectF(0, 0, w, h)
    painter.setPen(QPen(QColor(border_color), 1, Qt.PenStyle.SolidLine))
    painter.setBrush(QBrush(QColor(bg_color)))
    painter.drawRoundedRect(canvas_rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
    return canvas_rect
