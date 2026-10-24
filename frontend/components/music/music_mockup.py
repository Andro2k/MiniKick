# frontend\components\music\music_mockup.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QLinearGradient, QFont, QFontMetrics
from frontend.common import get_qcolor_with_alpha, Palette, BrandColors, MusicTheme
from frontend.components.mockup_helpers import init_mockup_painter, draw_mockup_canvas

class MusicOverlayMockupWidget(QWidget):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.layout_mode = "classic"
        self.setFixedHeight(160)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_configuration(self, layout: str):
        if self.layout_mode != layout:
            self.layout_mode = layout or "classic"
            self.update()

    def paintEvent(self, _event):
        painter, w, h = init_mockup_painter(self)
        canvas_rect = draw_mockup_canvas(painter, w, h)

        bg_brush, border_pen, accent_color, text_main, text_sub = self._get_theme_palette()

        sample_title = self.i18n.get("music.overlay.preview_sample_title")
        sample_artist = self.i18n.get("music.overlay.preview_sample_artist")

        if self.layout_mode == "vinyl":
            self._draw_floating_layout(painter, w, h, bg_brush, border_pen, text_main, text_sub, sample_title, sample_artist)
        else:
            self._draw_standard_layout(painter, w, h, bg_brush, border_pen, accent_color, text_main, text_sub, sample_title, sample_artist)

    def _get_theme_palette(self):
        if self.layout_mode == "vinyl":
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0.0, QColor(MusicTheme.MUSIC_VINYL_BG_TOP))
            gradient.setColorAt(1.0, QColor(MusicTheme.MUSIC_VINYL_BG_BOTTOM))
            return (
                QBrush(gradient),
                QPen(get_qcolor_with_alpha(Palette.NEUTRAL_000, 70), 1.25),
                QColor(MusicTheme.MUSIC_VINYL_ACCENT),
                QColor(Palette.NEUTRAL_000),
                get_qcolor_with_alpha(Palette.NEUTRAL_000, 170),
            )
        bg_brush = QBrush(QColor(MusicTheme.MUSIC_CARD_LIGHT))
        border_pen = QPen(QColor(MusicTheme.MUSIC_CARD_BORDER), 1.25)
        accent_color = QColor(MusicTheme.MUSIC_CARD_ACCENT)
        text_main = QColor(MusicTheme.MUSIC_CARD_TEXT)
        text_sub = QColor(MusicTheme.MUSIC_CARD_TEXT_SUB)
        return bg_brush, border_pen, accent_color, text_main, text_sub

    @staticmethod
    def _compute_centered_card(w: int, h: int, max_w: int, card_h: int) -> tuple[QRectF, float, float, float, float]:
        card_w = max(0, min(max_w, w - 24))
        card_h = max(0, min(card_h, h - 16))
        card_x = (w - card_w) / 2
        card_y = (h - card_h) / 2
        return QRectF(card_x, card_y, card_w, card_h), card_x, card_y, card_w, card_h

    def _draw_card_background(self, p: QPainter, w: int, h: int, bg_brush, border_pen, card_h: int, corner_radius: int) -> tuple[float, float, float, float]:
        card_rect, card_x, card_y, card_w, card_h = self._compute_centered_card(w, h, 440, card_h)
        p.setPen(border_pen)
        p.setBrush(bg_brush)
        p.drawRoundedRect(card_rect, corner_radius, corner_radius)
        return card_x, card_y, card_w, card_h

    def _draw_album_art_placeholder(self, p: QPainter, art_x: float, art_y: float, art_size: float, corner_radius: float, with_third_stop: bool = False):
        art_grad = QLinearGradient(art_x, art_y, art_x + art_size, art_y + art_size)
        art_grad.setColorAt(0.0, QColor(MusicTheme.MUSIC_ART_ACCENT))
        if with_third_stop:
            art_grad.setColorAt(0.5, QColor(BrandColors.PURPLE))
            art_grad.setColorAt(1.0, QColor(BrandColors.INDIGO_DARK))
        else:
            art_grad.setColorAt(1.0, QColor(BrandColors.PURPLE))
        p.setPen(QPen(get_qcolor_with_alpha(Palette.NEUTRAL_000, 50), 1))
        p.setBrush(QBrush(art_grad))
        p.drawRoundedRect(QRectF(art_x, art_y, art_size, art_size), corner_radius, corner_radius)

    def _draw_mockup_text(self, p: QPainter, rect: QRectF, text: str, font: QFont, color: QColor, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
        p.setFont(font)
        p.setPen(color)
        p.drawText(rect, align, self._elide(text, font, rect.width()))

    def _draw_floating_layout(self, p: QPainter, w: int, h: int, bg_brush, border_pen, text_main, text_sub, title: str, artist: str):
        card_x, card_y, card_w, card_h = self._draw_card_background(p, w, h, bg_brush, border_pen, 144, 28)

        scale = min(card_w / 440, card_h / 144)
        pad = 22 * scale
        disc_size = min(card_h * 0.84, card_w * 0.34)
        gap = 12 * scale
        text_x = card_x + pad
        text_w = max(0, card_w - (pad * 2) - disc_size - gap)
        disc_cx = card_x + card_w - pad - (disc_size / 2)
        disc_cy = card_y + card_h / 2

        p.setFont(QFont("Google Sans", max(5, round(8 * scale)), QFont.Weight.Bold))
        p.setPen(text_sub)
        now_rect = QRectF(text_x, card_y + card_h * 0.12, text_w, card_h * 0.14)
        p.drawText(now_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "NOW PLAYING")

        self._draw_mockup_text(p, QRectF(text_x, card_y + card_h * 0.34, text_w, card_h * 0.19), artist, QFont("Google Sans", max(6, round(11 * scale)), QFont.Weight.DemiBold), text_sub)
        self._draw_mockup_text(p, QRectF(text_x, card_y + card_h * 0.55, text_w, card_h * 0.29), title, QFont("Google Sans", max(7, round(16 * scale)), QFont.Weight.Bold), text_main)

        bars_x = text_x
        bars_y = card_y + card_h * 0.91
        bar_heights = [3, 7, 10, 6, 8, 4, 9, 11, 7, 5, 8, 10, 6, 8, 4, 7, 9, 5, 8, 3]
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(get_qcolor_with_alpha(Palette.NEUTRAL_000, 210)))
        bars_width = min(text_w, len(bar_heights) * 4.5 * scale)
        visible_bars = min(len(bar_heights), int(bars_width / max(1, 4.5 * scale)))
        for i, bh in enumerate(bar_heights[:visible_bars]):
            bar_height = bh * scale
            bx = bars_x + i * 4.5 * scale
            by = bars_y - bar_height / 2
            p.drawRoundedRect(QRectF(bx, by, max(1, 2.5 * scale), bar_height), 1, 1)

        vinyl_cx = disc_cx
        vinyl_cy = disc_cy
        vinyl_r = disc_size / 2
        p.setPen(QPen(QColor(Palette.NEUTRAL_999), 1))
        p.setBrush(QBrush(QColor(MusicTheme.MUSIC_VINYL_BLACK)))
        p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), vinyl_r, vinyl_r)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(get_qcolor_with_alpha(MusicTheme.MUSIC_GROOVE, 180), 0.75))
        for ratio in (0.86, 0.76, 0.66):
            p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), vinyl_r * ratio, vinyl_r * ratio)
        label_radius = vinyl_r * 0.48
        label_grad = QLinearGradient(vinyl_cx - label_radius, vinyl_cy - label_radius, vinyl_cx + label_radius, vinyl_cy + label_radius)
        label_grad.setColorAt(0.0, QColor(MusicTheme.MUSIC_ART_ACCENT))
        label_grad.setColorAt(1.0, QColor(BrandColors.PURPLE))
        p.setBrush(QBrush(label_grad))
        p.setPen(QPen(get_qcolor_with_alpha(Palette.NEUTRAL_000, 60), 1))
        p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), label_radius, label_radius)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(MusicTheme.MUSIC_VINYL_HOLE)))
        p.drawEllipse(QPointF(vinyl_cx, vinyl_cy), max(1.5, vinyl_r * 0.07), max(1.5, vinyl_r * 0.07))
        pivot_x = vinyl_cx + vinyl_r * 0.64
        pivot_y = vinyl_cy - vinyl_r * 0.72
        base_radius = max(2, vinyl_r * 0.095)
        base_grad = QLinearGradient(pivot_x - base_radius, pivot_y - base_radius, pivot_x + base_radius, pivot_y + base_radius)
        base_grad.setColorAt(0.0, QColor(Palette.NEUTRAL_600))
        base_grad.setColorAt(1.0, QColor(MusicTheme.MUSIC_METAL_DARK))
        p.setBrush(QBrush(base_grad))
        p.setPen(QPen(get_qcolor_with_alpha(Palette.NEUTRAL_000, 80), 1))
        p.drawEllipse(QPointF(pivot_x, pivot_y), base_radius, base_radius)
        rod_pen = QPen(QBrush(QColor(MusicTheme.MUSIC_TONEARM)), max(1, 2.2 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(rod_pen)
        head_x = vinyl_cx + vinyl_r * 0.08
        head_y = vinyl_cy - vinyl_r * 0.1
        p.drawLine(QPointF(pivot_x, pivot_y + base_radius * 0.5), QPointF(head_x + vinyl_r * 0.05, head_y - vinyl_r * 0.05))
        p.setPen(QPen(QColor(MusicTheme.MUSIC_HEAD_BORDER), 1))
        p.setBrush(QBrush(QColor(MusicTheme.MUSIC_HEAD_BG)))
        head_path = QPainterPath()
        head_path.addRoundedRect(QRectF(head_x - vinyl_r * 0.07, head_y - vinyl_r * 0.09, vinyl_r * 0.14, vinyl_r * 0.2), 2, 2)
        p.save()
        p.translate(head_x, head_y)
        p.rotate(22)
        p.translate(-head_x, -head_y)
        p.drawPath(head_path)
        p.restore()

    def _draw_standard_layout(self, p: QPainter, w: int, h: int, bg_brush, border_pen, accent_color, text_main, text_sub, title: str, artist: str):
        card_x, card_y, card_w, card_h = self._draw_card_background(p, w, h, bg_brush, border_pen, 132, 20)
        scale = min(card_w / 440, card_h / 132)
        art_size = min(94 * scale, card_h - 20 * scale, card_w * 0.25)
        art_x = card_x + 12 * scale
        art_y = card_y + (card_h - art_size) / 2
        self._draw_album_art_placeholder(p, art_x, art_y, art_size, 14, with_third_stop=True)

        text_x = art_x + art_size + 16 * scale
        text_w = max(0, card_x + card_w - text_x - 16 * scale)

        self._draw_mockup_text(p, QRectF(text_x, card_y + 14 * scale, text_w, 16 * scale), artist, QFont("Google Sans", max(6, round(8 * scale)), QFont.Weight.Medium), text_sub)
        self._draw_mockup_text(p, QRectF(text_x, card_y + 34 * scale, text_w, 24 * scale), title, QFont("Google Sans", max(7, round(12 * scale)), QFont.Weight.Bold), text_main)
        prog_w = text_w
        prog_h = max(2, 4 * scale)
        prog_y = card_y + card_h * 0.58
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(get_qcolor_with_alpha(Palette.NEUTRAL_000, 45)))
        p.drawRoundedRect(QRectF(text_x, prog_y, prog_w, prog_h), prog_h / 2, prog_h / 2)
        p.setBrush(QBrush(accent_color))
        p.drawRoundedRect(QRectF(text_x, prog_y, prog_w * 0.42, prog_h), prog_h / 2, prog_h / 2)
        p.setFont(QFont("Google Sans", max(5, round(7 * scale)), QFont.Weight.Bold))
        p.setPen(text_sub)
        time_y = prog_y + 5 * scale
        p.drawText(QRectF(text_x, time_y, 40 * scale, 12 * scale), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "0:34")
        p.drawText(QRectF(text_x + prog_w - 40 * scale, time_y, 40 * scale, 12 * scale), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "3:43")

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
