# frontend\components\stats\comparison_bar_chart_widget.py
"""Gráfico de barras que superpone el período actual sobre el anterior."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget
from frontend.common import BrandColors, Palette

_AXIS_HEIGHT = 22
_MIN_LABEL_GAP = 56


class ComparisonBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self._labels: list[str] = []
        self._current: list[int] = []
        self._previous: list[int] = []
        self._current_name = ""
        self._previous_name = ""

    def set_data(self, labels, current, previous, current_name: str = "", previous_name: str = "") -> None:
        self._labels, self._current, self._previous = list(labels), list(current), list(previous)
        self._current_name, self._previous_name = current_name, previous_name
        self.update()

    def _slot_width(self) -> float:
        return self.width() / max(len(self._labels), 1)

    def paintEvent(self, _event):
        count = len(self._labels)
        if not count:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        plot_h = max(self.height() - _AXIS_HEIGHT, 1)
        peak = max(max(self._current, default=0), max(self._previous, default=0), 1)
        slot = self._slot_width()
        bar_w = max(slot * 0.62, 2.0)
        radius = min(bar_w / 2, 3.0)
        prev_color, cur_color = QColor(Palette.NEUTRAL_700), QColor(BrandColors.GREEN)

        for i in range(count):
            x = i * slot + (slot - bar_w) / 2
            for value, color in ((self._previous[i], prev_color), (self._current[i], cur_color)):
                if value <= 0:
                    continue
                h = max(value / peak * (plot_h - 4), 2.0)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(QRectF(x, plot_h - h, bar_w, h), radius, radius)

        painter.setPen(QColor(Palette.NEUTRAL_500))
        step = max(1, int(_MIN_LABEL_GAP / max(slot, 1)) + 1)
        for i in range(0, count, step):
            label_w = max(slot, _MIN_LABEL_GAP)
            left = min(max(i * slot + slot / 2 - label_w / 2, 0.0), max(self.width() - label_w, 0.0))
            rect = QRectF(left, plot_h + 4, label_w, _AXIS_HEIGHT - 4)
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._labels[i])

    def mouseMoveEvent(self, event):
        count = len(self._labels)
        if not count:
            return
        index = min(max(int(event.position().x() / self._slot_width()), 0), count - 1)
        QToolTip.showText(
            event.globalPosition().toPoint(),
            f"{self._labels[index]}\n{self._current_name}: {self._current[index]:,}\n"
            f"{self._previous_name}: {self._previous[index]:,}",
            self,
        )
