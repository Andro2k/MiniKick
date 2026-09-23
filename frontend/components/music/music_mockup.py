# frontend\components\music\music_mockup.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath, QLinearGradient, QFont
)
from frontend.components.mockup_helpers import init_mockup_painter, draw_mockup_canvas

class MusicOverlayMockupWidget(QWidget):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.layout_mode = "floating"
        self.theme_mode = "dynamic"
        self.setFixedHeight(160)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_configuration(self, layout: str, theme: str):
        if self.layout_mode != layout or self.theme_mode != theme:
            self.layout_mode = layout or "floating"
            self.theme_mode = theme or "dynamic"
            self.update()

    def paintEvent(self, _event):
        painter, w, h = init_mockup_painter(self)
        canvas_rect = draw_mockup_canvas(painter, w, h)

        bg_brush, border_pen, accent_color, text_main, text_sub = self._get_theme_palette()

        sample_title = self.i18n.get("music.overlay.preview_sample_title")
        sample_artist = self.i18n.get("music.overlay.preview_sample_artist")

        if self.layout_mode in ("floating", "vinyl"):
            self._draw_floating_layout(painter, w, h, bg_brush, border_pen, accent_color, text_main, text_sub, sample_title, sample_artist)
        elif self.layout_mode == "pill":
            self._draw_pill_layout(painter, w, h, bg_brush, border_pen, accent_color, text_main, text_sub, sample_title, sample_artist)
        else:
            self._draw_standard_layout(painter, w, h, bg_brush, border_pen, accent_color, text_main, text_sub, sample_title, sample_artist)

    def _get_theme_palette(self):
        if self.theme_mode == "dynamic":
            grad = QLinearGradient(0, 0, 300, 80)
            grad.setColorAt(0.0, QColor(48, 26, 38, 235))
            grad.setColorAt(1.0, QColor(24, 20, 28, 245))
            bg_brush = QBrush(grad)
            border_pen = QPen(QColor(255, 255, 255, 32), 1.25)
            accent_color = QColor("#FFFFFF")
            text_main = QColor("#FFFFFF")
            text_sub = QColor("#9CA3AF")

        elif self.theme_mode == "glass":
            bg_brush = QBrush(QColor(255, 255, 255, 28))
            border_pen = QPen(QColor(255, 255, 255, 75), 1.25)
            accent_color = QColor("#FFFFFF")
            text_main = QColor("#FFFFFF")
            text_sub = QColor(255, 255, 255, 175)

        elif self.theme_mode == "neon":
            bg_brush = QBrush(QColor(14, 22, 18, 245))
            border_pen = QPen(QColor("#2ECD70"), 2.0)
            accent_color = QColor("#2ECD70")
            text_main = QColor("#FFFFFF")
            text_sub = QColor("#9CA3AF")

        else:
            bg_brush = QBrush(QColor(30, 28, 34, 250))
            border_pen = QPen(QColor(62, 60, 68, 160), 1.25)
            accent_color = QColor("#FFFFFF")
            text_main = QColor("#FFFFFF")
            text_sub = QColor("#9CA3AF")

        return bg_brush, border_pen, accent_color, text_main, text_sub

    @staticmethod
    def _compute_centered_card(w: int, h: int, max_w: int, card_h: int) -> tuple[QRectF, float, float, float, float]:
        card_w = min(max_w, w - 30)
        card_x = (w - card_w) / 2
        card_y = (h - card_h) / 2
        return QRectF(card_x, card_y, card_w, card_h), card_x, card_y, card_w, card_h

    def _draw_album_art_placeholder(self, p: QPainter, art_x: float, art_y: float, art_size: float, corner_radius: float, with_third_stop: bool = False):
        art_grad = QLinearGradient(art_x, art_y, art_x + art_size, art_y + art_size)
        art_grad.setColorAt(0.0, QColor("#F43F5E"))
        if with_third_stop:
            art_grad.setColorAt(0.5, QColor("#A855F7"))
            art_grad.setColorAt(1.0, QColor("#6366F1"))
        else:
            art_grad.setColorAt(1.0, QColor("#A855F7"))
        p.setPen(QPen(QColor(255, 255, 255, 50), 1))
        p.setBrush(QBrush(art_grad))
        p.drawRoundedRect(QRectF(art_x, art_y, art_size, art_size), corner_radius, corner_radius)

    def _draw_mockup_text(self, p: QPainter, rect: QRectF, text: str, font: QFont, color: QColor, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
        p.setFont(font)
        p.setPen(color)
        p.drawText(rect, align, self._elide(text, font, rect.width()))

    def _draw_floating_layout(self, p: QPainter, w: int, h: int, bg_brush, border_pen, accent_color, text_main, text_sub, title: str, artist: str):
        card_rect, card_x, card_y, card_w, card_h = self._compute_centered_card(w, h, 340, 86)

        p.setPen(border_pen)
        p.setBrush(bg_brush)
        p.drawRoundedRect(card_rect, 20, 20)

        text_x = card_x + 16
        text_w = card_w - 110

        p.setFont(QFont("Google Sans", 6, QFont.Weight.Bold))
        p.setPen(text_sub)
        now_rect = QRectF(text_x, card_y + 10, text_w, 12)
        p.drawText(now_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "NOW PLAYING")

        self._draw_mockup_text(p, QRectF(text_x, card_y + 26, text_w, 13), artist.upper(), QFont("Google Sans", 7, QFont.Weight.DemiBold), text_sub)
        self._draw_mockup_text(p, QRectF(text_x, card_y + 39, text_w, 17), title, QFont("Google Sans", 10, QFont.Weight.Bold), text_main)

        bars_x = text_x
        bars_y = card_y + 67
        bar_heights = [3, 7, 10, 6, 8, 4, 9, 11, 7, 5, 8, 10, 6, 8, 4, 7, 9, 5, 8, 3]
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 210) if self.theme_mode != "neon" else accent_color))
        for i, bh in enumerate(bar_heights):
            bx = bars_x + i * 4.5
            by = bars_y - bh / 2
            p.drawRoundedRect(QRectF(bx, by, 2.5, bh), 1, 1)

        vinyl_cx = card_x + card_w - 48
        vinyl_cy = card_y + card_h / 2
        vinyl_r = 33
        p.setPen(QPen(QColor("#000000"), 1))
        p.setBrush(QBrush(QColor("#111114")))
        p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), vinyl_r, vinyl_r)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(48, 48, 56, 180), 0.75))
        for r in [28, 24, 20]:
            p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), r, r)
        label_grad = QLinearGradient(vinyl_cx - 16, vinyl_cy - 16, vinyl_cx + 16, vinyl_cy + 16)
        label_grad.setColorAt(0.0, QColor("#F43F5E"))
        label_grad.setColorAt(1.0, QColor("#A855F7"))
        p.setBrush(QBrush(label_grad))
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), 16, 16)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#09090B")))
        p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), 2.5, 2.5)
        pivot_x = vinyl_cx + 20
        pivot_y = vinyl_cy - 24
        base_grad = QLinearGradient(pivot_x - 5, pivot_y - 5, pivot_x + 5, pivot_y + 5)
        base_grad.setColorAt(0.0, QColor("#4B5563"))
        base_grad.setColorAt(1.0, QColor("#1F2937"))
        p.setBrush(QBrush(base_grad))
        p.setPen(QPen(QColor(255, 255, 255, 80), 1))
        p.drawEllipse(QPointF(pivot_x, pivot_y), 5.5, 5.5)
        rod_pen = QPen(QBrush(QColor("#D1D5DB")), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(rod_pen)
        head_x = vinyl_cx + 5
        head_y = vinyl_cy - 6
        p.drawLine(QPointF(pivot_x - 1, pivot_y + 3), QPointF(head_x + 3, head_y - 3))
        p.setPen(QPen(QColor("#374151"), 1))
        p.setBrush(QBrush(QColor("#111827")))
        head_path = QPainterPath()
        head_path.addRoundedRect(QRectF(head_x - 4, head_y - 5, 8, 12), 2, 2)
        p.save()
        p.translate(head_x, head_y)
        p.rotate(22)
        p.translate(-head_x, -head_y)
        p.drawPath(head_path)
        p.restore()

    def _draw_pill_layout(self, p: QPainter, w: int, h: int, bg_brush, border_pen, accent_color, text_main, text_sub, title: str, artist: str):
        card_rect, card_x, card_y, card_w, card_h = self._compute_centered_card(w, h, 320, 42)

        p.setPen(border_pen)
        p.setBrush(bg_brush)
        p.drawRoundedRect(card_rect, card_h / 2, card_h / 2)
        art_size = 28
        art_x = card_x + 7
        art_y = card_y + (card_h - art_size) / 2
        self._draw_album_art_placeholder(p, art_x, art_y, art_size, 7)

        text_x = art_x + art_size + 10
        text_w = card_w - art_size - 60
        self._draw_mockup_text(p, QRectF(text_x, card_y + 6, text_w, 15), title, QFont("Google Sans", 9, QFont.Weight.Bold), text_main)
        self._draw_mockup_text(p, QRectF(text_x, card_y + 21, text_w, 14), artist, QFont("Google Sans", 7, QFont.Weight.Medium), text_sub)

        play_x = card_x + card_w - 24
        play_y = card_y + card_h / 2
        p.setBrush(QBrush(QColor(255, 255, 255, 220) if self.theme_mode != "neon" else accent_color))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(play_x - 3, play_y - 6)
        path.lineTo(play_x + 5, play_y)
        path.lineTo(play_x - 3, play_y + 6)
        path.closeSubpath()
        p.drawPath(path)

    def _draw_standard_layout(self, p: QPainter, w: int, h: int, bg_brush, border_pen, accent_color, text_main, text_sub, title: str, artist: str):
        card_rect, card_x, card_y, card_w, card_h = self._compute_centered_card(w, h, 340, 76)

        p.setPen(border_pen)
        p.setBrush(bg_brush)
        p.drawRoundedRect(card_rect, 16, 16)
        art_size = 54
        art_x = card_x + 10
        art_y = card_y + (card_h - art_size) / 2
        self._draw_album_art_placeholder(p, art_x, art_y, art_size, 12, with_third_stop=True)

        text_x = art_x + art_size + 12
        text_w = card_w - art_size - 32

        self._draw_mockup_text(p, QRectF(text_x, card_y + 11, text_w, 14), artist, QFont("Google Sans", 7.5, QFont.Weight.Medium), text_sub)
        self._draw_mockup_text(p, QRectF(text_x, card_y + 25, text_w, 17), title, QFont("Google Sans", 10, QFont.Weight.Bold), text_main)
        prog_w = text_w
        prog_h = 3.5
        prog_y = card_y + 47
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 45)))
        p.drawRoundedRect(QRectF(text_x, prog_y, prog_w, prog_h), 2, 2)
        p.setBrush(QBrush(QColor("#FFFFFF") if self.theme_mode != "neon" else accent_color))
        p.drawRoundedRect(QRectF(text_x, prog_y, prog_w * 0.35, prog_h), 2, 2)
        p.setFont(QFont("Google Sans", 7, QFont.Weight.Bold))
        p.setPen(text_sub)
        p.drawText(QRectF(text_x, prog_y + 5, 40, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "0:34")
        p.drawText(QRectF(text_x + prog_w - 40, prog_y + 5, 40, 12), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "3:43")

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
