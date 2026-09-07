# frontend\components\alerts\alert_mockup.py

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QFont, QFontMetrics, QPainterPath
)

class AlertOverlayMockupWidget(QWidget):
    _EVENT_GLYPHS = {
        "follow": ("\uf004", "#38BDF8", "heart"),
        "subscription": ("\uedeb", "#F59E0B", "star"),
        "resub": ("\uf005", "#818CF8", "crown"),
        "sub_gift": ("\uf06b", "#EC4899", "gift"),
        "raid": ("\uf0c0", "#10B981", "raid"),
        "cheer": ("\ue86e", "#6366F1", "diamond")
    }

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.platform = "kick"
        self.alert_type = "follow"
        self.layout_mode = "above"
        self.style_mode = "compact"
        self.template_text = self.i18n.get("alerts.preview.sample_template")
        self.media_path = ""
        self.text_color = "#FFFFFF"
        self.highlight_color = ""
        self.font_family = "Outfit"
        self.font_size = 24
        self.text_align = "center"
        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def sizeHint(self) -> QSize:
        return QSize(320, 320)

    def minimumSizeHint(self) -> QSize:
        return QSize(160, 160)

    def set_configuration(
        self,
        platform: str,
        alert_type: str,
        layout: str,
        style: str,
        template: str = "",
        media_path: str = "",
        text_template: str = "",
        text_color: str = "#FFFFFF",
        highlight_color: str = "",
        font_family: str = "Outfit",
        font_size: int = 24,
        text_align: str = "center"
    ):
        new_platform = platform or "kick"
        new_type = alert_type or "follow"
        new_layout = layout or "above"
        new_style = style or "compact"
        new_template = text_template or template or "{user}"
        new_text_color = text_color or "#FFFFFF"
        new_highlight = highlight_color or ""
        new_font = font_family or "Outfit"
        new_font_size = font_size or 24
        new_align = text_align or "center"

        changed = (
            self.platform != new_platform
            or self.alert_type != new_type
            or self.layout_mode != new_layout
            or self.style_mode != new_style
            or self.template_text != new_template
            or self.media_path != media_path
            or self.text_color != new_text_color
            or self.highlight_color != new_highlight
            or self.font_family != new_font
            or self.font_size != new_font_size
            or self.text_align != new_align
        )
        if changed:
            self.platform = new_platform
            self.alert_type = new_type
            self.layout_mode = new_layout
            self.style_mode = new_style
            self.template_text = new_template
            self.media_path = media_path
            self.text_color = new_text_color
            self.highlight_color = new_highlight
            self.font_family = new_font
            self.font_size = new_font_size
            self.text_align = new_align
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()

        side = min(w, h) - 4
        if side < 100:
            side = 100
        cx = (w - side) / 2.0
        cy = (h - side) / 2.0
        canvas_rect = QRectF(cx, cy, side, side)

        canvas_path = QPainterPath()
        canvas_path.addRoundedRect(canvas_rect, 10, 10)
        p.save()
        p.setClipPath(canvas_path)

        tile_size = 16
        c1 = QColor("#11141C")
        c2 = QColor("#0B0D13")
        start_x = int(cx)
        start_y = int(cy)
        for x in range(start_x, start_x + int(side) + tile_size, tile_size):
            for y in range(start_y, start_y + int(side) + tile_size, tile_size):
                p.fillRect(x, y, tile_size, tile_size, c1 if (((x - start_x) // tile_size + (y - start_y) // tile_size) % 2 == 0) else c2)

        p.restore()

        p.setPen(QPen(QColor("#1F242F"), 1, Qt.PenStyle.SolidLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(canvas_rect, 10, 10)

        glyph, _, _ = self._EVENT_GLYPHS.get(self.alert_type.lower(), ("\uf004", "#38BDF8", "heart"))
        default_platform_color = "#53FC18" if self.platform == "kick" else "#9146FF"
        accent_hex = self.highlight_color if self.highlight_color else default_platform_color
        accent_color = QColor(accent_hex)
        text_main_color = QColor(self.text_color if self.text_color else "#FFFFFF")

        sample_user = self.i18n.get("alerts.preview.sample_user") if self.i18n else "TheAndro2K"
        sample_amount = self.i18n.get("alerts.preview.sample_amount") if self.i18n else "500"
        sample_tier = self.i18n.get("alerts.preview.sample_tier") if self.i18n else "1"

        resolved_text = self.template_text.replace("{user}", sample_user)\
            .replace("{amount}", sample_amount)\
            .replace("{tier}", sample_tier)\
            .replace("{platform}", self.platform.capitalize())

        if self.layout_mode == "side":
            self._draw_side_layout(p, cx, cy, side, glyph, accent_color, text_main_color, sample_user, resolved_text)
        elif self.layout_mode == "side_right":
            self._draw_side_right_layout(p, cx, cy, side, glyph, accent_color, text_main_color, sample_user, resolved_text)
        elif self.layout_mode == "below":
            self._draw_below_layout(p, cx, cy, side, glyph, accent_color, text_main_color, sample_user, resolved_text)
        elif self.layout_mode == "overlay":
            self._draw_overlay_layout(p, cx, cy, side, glyph, accent_color, text_main_color, sample_user, resolved_text)
        else:
            self._draw_above_layout(p, cx, cy, side, glyph, accent_color, text_main_color, sample_user, resolved_text)

    def _get_alignment_flag(self, default_align=Qt.AlignmentFlag.AlignCenter):
        if self.text_align == "left":
            return Qt.AlignmentFlag.AlignLeft
        elif self.text_align == "right":
            return Qt.AlignmentFlag.AlignRight
        elif self.text_align == "center":
            return Qt.AlignmentFlag.AlignCenter
        return default_align

    def _draw_above_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        is_sticker = (self.style_mode == "sticker")
        card_w = min(290.0, side - 24.0)
        card_h = 56.0
        card_x = cx + (side - card_w) / 2.0
        card_y = cy + (side - card_h) / 2.0 + 22.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        icon_size = 42.0
        icon_x = cx + (side - icon_size) / 2.0
        icon_y = card_y - 24.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        if not is_sticker:
            self._draw_card_container(p, card_rect, accent, radius=14.0)

        p.setBrush(QBrush(QColor(18, 22, 30, 240 if not is_sticker else 210)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawEllipse(icon_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 13))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = icon_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = icon_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        font_size = max(9.0, min(14.0, self.font_size * 0.45))
        title_font = QFont(self.font_family, font_size, QFont.Weight.DemiBold)
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        msg_rect = QRectF(card_x + 10, card_y + 16, card_w - 20, 30)

        if is_sticker:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.5, 1.5, 1.5, 1.5), align_flag, self._elide(full_text, title_font, card_w - 20))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, title_font, card_w - 20))

    def _draw_below_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        is_sticker = (self.style_mode == "sticker")
        card_w = min(290.0, side - 24.0)
        card_h = 56.0
        card_x = cx + (side - card_w) / 2.0
        card_y = cy + (side - card_h) / 2.0 - 22.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        icon_size = 42.0
        icon_x = cx + (side - icon_size) / 2.0
        icon_y = card_y + card_h - 18.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        if not is_sticker:
            self._draw_card_container(p, card_rect, accent, radius=14.0)

        font_size = max(9.0, min(14.0, self.font_size * 0.45))
        title_font = QFont(self.font_family, font_size, QFont.Weight.DemiBold)
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        msg_rect = QRectF(card_x + 10, card_y + 10, card_w - 20, 30)

        if is_sticker:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.5, 1.5, 1.5, 1.5), align_flag, self._elide(full_text, title_font, card_w - 20))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, title_font, card_w - 20))

        p.setBrush(QBrush(QColor(18, 22, 30, 240 if not is_sticker else 210)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawEllipse(icon_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 13))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = icon_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = icon_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

    def _draw_side_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        is_sticker = (self.style_mode == "sticker")
        card_w = min(320.0, side - 16.0)
        card_h = 68.0
        card_x = cx + (side - card_w) / 2.0
        card_y = cy + (side - card_h) / 2.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        if not is_sticker:
            self._draw_card_container(p, card_rect, accent, radius=12.0)

        badge_d = 42.0
        badge_x = card_x + 12.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        p.setBrush(QBrush(QColor(18, 22, 30, 240 if not is_sticker else 210)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawEllipse(badge_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 13))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = badge_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = badge_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        text_x = badge_x + badge_d + 12.0
        text_w = card_w - (badge_d + 24.0)

        font_size = max(9.0, min(14.0, self.font_size * 0.45))
        title_font = QFont(self.font_family, font_size, QFont.Weight.DemiBold)
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(text_x, card_y + 12.0, text_w, 20.0)

        if is_sticker:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.5, 1.5, 1.5, 1.5), align_flag, self._elide(user, title_font, text_w))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, text_w))

        sub_font = QFont("Inter", 8.5, QFont.Weight.Normal)
        p.setFont(sub_font)
        msg_rect = QRectF(text_x, card_y + 34.0, text_w, 18.0)

        if is_sticker:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, sub_font, text_w))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, sub_font, text_w))

    def _draw_side_right_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        is_sticker = (self.style_mode == "sticker")
        card_w = min(320.0, side - 16.0)
        card_h = 68.0
        card_x = cx + (side - card_w) / 2.0
        card_y = cy + (side - card_h) / 2.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        if not is_sticker:
            self._draw_card_container(p, card_rect, accent, radius=12.0)

        badge_d = 42.0
        badge_x = card_x + card_w - badge_d - 12.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        p.setBrush(QBrush(QColor(18, 22, 30, 240 if not is_sticker else 210)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawEllipse(badge_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 13))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = badge_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = badge_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        text_x = card_x + 12.0
        text_w = card_w - (badge_d + 24.0)

        font_size = max(9.0, min(14.0, self.font_size * 0.45))
        title_font = QFont(self.font_family, font_size, QFont.Weight.DemiBold)
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(text_x, card_y + 12.0, text_w, 20.0)

        if is_sticker:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.5, 1.5, 1.5, 1.5), align_flag, self._elide(user, title_font, text_w))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, text_w))

        sub_font = QFont("Inter", 8.5, QFont.Weight.Normal)
        p.setFont(sub_font)
        msg_rect = QRectF(text_x, card_y + 34.0, text_w, 18.0)

        if is_sticker:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, sub_font, text_w))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, sub_font, text_w))

    def _draw_overlay_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_w = min(300.0, side - 20.0)
        card_h = 70.0
        card_x = cx + (side - card_w) / 2.0
        card_y = cy + (side - card_h) / 2.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        grad = QLinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
        grad.setColorAt(0.0, QColor(22, 27, 36, 240))
        grad.setColorAt(1.0, QColor(14, 17, 24, 250))

        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1.0))
        p.drawRoundedRect(card_rect, 12, 12)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(accent.red(), accent.green(), accent.blue(), 180)))
        p.drawRoundedRect(QRectF(card_x + 12, card_y + 1, card_w - 24, 2.5), 1, 1)

        font_size = max(9.0, min(14.0, self.font_size * 0.45))
        title_font = QFont(self.font_family, font_size, QFont.Weight.Bold)
        p.setFont(title_font)
        p.setPen(accent)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(card_x + 16, card_y + 12, card_w - 32, 20)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, card_w - 32))

        sub_font = QFont("Inter", 8.5, QFont.Weight.Normal)
        p.setFont(sub_font)
        p.setPen(text_color)
        sub_rect = QRectF(card_x + 16, card_y + 36, card_w - 32, 18)
        p.drawText(sub_rect, align_flag, self._elide(full_text, sub_font, card_w - 32))

    def _draw_card_container(self, p: QPainter, rect: QRectF, accent: QColor, radius: float):
        if self.style_mode == "compact":
            p.setPen(QPen(QColor("#2E384D"), 1.2))
            p.setBrush(QBrush(QColor(15, 18, 25, 245)))
            p.drawRoundedRect(rect, radius, radius)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(accent))
            p.drawRoundedRect(QRectF(rect.x() + 16, rect.y() + 1, rect.width() - 32, 2.0), 1, 1)

        elif self.style_mode == "glass":
            p.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
            p.setBrush(QBrush(QColor(24, 28, 38, 190)))
            p.drawRoundedRect(rect, radius, radius)
            p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 100), 1.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius - 1, radius - 1)

        else:
            p.setPen(QPen(QColor(255, 255, 255, 20), 1.0))
            p.setBrush(QBrush(QColor(13, 16, 22, 230)))
            p.drawRoundedRect(rect, radius, radius)

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
