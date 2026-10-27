# frontend\components\dashboard\platform_distribution_ring.py

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget
from frontend.common import Palette, get_pixmap_colored


class PlatformDistributionRing(QWidget):
    DEFAULT_AVATAR_SIZE = 124

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments: list[tuple[int, str]] = []
        self._fallback_avatar = get_pixmap_colored(
            "user-filled.svg", self.DEFAULT_AVATAR_SIZE
        )
        self._avatar = self._fallback_avatar
        self._avatar_size = self.DEFAULT_AVATAR_SIZE
        self.setFixedSize(176, 176)

    def set_data(self, segments: list[tuple[int, str]]):
        normalized = [(max(0, int(count)), color) for count, color in segments if count > 0]
        if normalized == self._segments:
            return
        self._segments = normalized
        self.update()

    def set_avatar(self, avatar: QPixmap | None):
        self._avatar = avatar if avatar and not avatar.isNull() else self._fallback_avatar
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(9, 9, self.width() - 18, self.height() - 18)
        ring_width = 10
        painter.setPen(QPen(QColor(Palette.NEUTRAL_750), ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 0, 360 * 16)

        total = sum(count for count, _ in self._segments)
        if total:
            start_angle = 90 * 16
            gap = 2 * 16
            usable_angle = 360 * 16 - gap * len(self._segments)
            for count, color in self._segments:
                sweep = round(usable_angle * count / total)
                painter.setPen(QPen(QColor(color), ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawArc(rect, start_angle, -sweep)
                start_angle -= sweep + gap

        avatar_position = (self.width() - self._avatar_size) / 2
        avatar_rect = QRectF(avatar_position, avatar_position, self._avatar_size, self._avatar_size)
        path = QPainterPath()
        path.addEllipse(avatar_rect)
        painter.setClipPath(path)
        if self._avatar and not self._avatar.isNull():
            painter.drawPixmap(avatar_rect.toRect(), self._avatar)
        painter.end()
