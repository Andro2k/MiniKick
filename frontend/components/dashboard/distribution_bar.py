# frontend\components\dashboard\distribution_bar.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QColor, QPainterPath
from frontend.common import COLOR_NEUTRAL_800

class SegmentedDistributionBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self._segments = []
        self._cached_clip_path = None
        self._cached_rect = None

    def set_data(self, data: list[tuple[float, str]]):
        self._segments = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        if self._cached_rect != rect:
            self._cached_rect = rect
            self._cached_clip_path = QPainterPath()
            self._cached_clip_path.addRoundedRect(QRectF(rect), 8, 8)
            
        painter.setClipPath(self._cached_clip_path)
        
        total_p = sum(p for p, _ in self._segments)
        if total_p <= 0:
            painter.fillRect(rect, QColor(COLOR_NEUTRAL_800))
            return
            
        current_x = 0.0
        w = float(self.width())
        h = float(self.height())
        for p, color in self._segments:
            seg_width = (p / total_p) * w
            painter.fillRect(QRectF(current_x, 0, seg_width, h), QColor(color))
            current_x += seg_width
