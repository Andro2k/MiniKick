# frontend\components\stats\peak_hours_chart_widget.py
"""Distribución de actividad por hora del día, resaltando la hora más activa."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget
from frontend.common import BrandColors, Palette


class PeakHoursChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._values: list[int] = [0] * 24
        self._peak_hour: int | None = None

    def set_data(self, hourly_totals: list[int], peak_hour: int | None) -> None:
        self._values = list(hourly_totals)
        self._peak_hour = peak_hour
        self.update()

    def paintEvent(self, _event):
        peak = max(self._values, default=0)
        if peak <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        slot = self.width() / 24
        bar_w = max(slot * 0.6, 2.0)
        painter.setPen(Qt.PenStyle.NoPen)
        for hour, value in enumerate(self._values):
            if value <= 0:
                continue
            h = max(value / peak * (self.height() - 2), 2.0)
            painter.setBrush(QColor(BrandColors.GREEN if hour == self._peak_hour else Palette.NEUTRAL_600))
            painter.drawRoundedRect(
                QRectF(hour * slot + (slot - bar_w) / 2, self.height() - h, bar_w, h), 2, 2
            )
