# frontend\components\alerts\alert_mockup.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QFont, QFontMetrics
)

class AlertOverlayMockupWidget(QWidget):
    _EVENT_GLYPHS = {
        "follow": ("\uf004", "#FB923C", "heart"),
        "subscription": ("\uf005", "#38BDF8", "star"),
        "resub": ("\uf130", "#A855F7", "crown"),
        "sub_gift": ("\udb80\udc1a", "#EC4899", "gift"),
        "raid": ("\uf101", "#4ADE80", "raid"),
        "cheer": ("\udb81\udcc6", "#F43F5E", "diamond")
    }

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.platform = "kick"
        self.alert_type = "follow"
        self.layout_mode = "above"
        self.style_mode = "compact"
        self.template_text = "{user} te acaba de seguir!"
        self.media_path = ""
        self.setFixedHeight(135)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_configuration(
        self,
        platform: str,
        alert_type: str,
        layout: str,
        style: str,
        template: str = "",
        media_path: str = "",
        text_template: str = ""
    ):
        new_platform = platform or "kick"
        new_type = alert_type or "follow"
        new_layout = layout or "above"
        new_style = style or "compact"
        new_template = text_template or template or "{user}"

        changed = (
            self.platform != new_platform
            or self.alert_type != new_type
            or self.layout_mode != new_layout
            or self.style_mode != new_style
            or self.template_text != new_template
            or self.media_path != media_path
        )
        if changed:
            self.platform = new_platform
            self.alert_type = new_type
            self.layout_mode = new_layout
            self.style_mode = new_style
            self.template_text = new_template
            self.media_path = media_path
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()

        canvas_rect = QRectF(0, 0, w, h)
        p.setPen(QPen(QColor("#27272A"), 1, Qt.PenStyle.SolidLine))
        p.setBrush(QBrush(QColor("#09090B")))
        p.drawRoundedRect(canvas_rect.adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)
        glyph, event_color_hex, _ = self._EVENT_GLYPHS.get(self.alert_type.lower(), ("\uf004", "#53FC18", "heart"))
        platform_color = QColor("#53FC18" if self.platform == "kick" else "#9146FF")
        accent_color = QColor(event_color_hex if self.style_mode == "compact" else platform_color)

        sample_user = self.i18n.get("alerts.preview.sample_user") if self.i18n else "TheAndro2K"
        sample_amount = self.i18n.get("alerts.preview.sample_amount") if self.i18n else "500"
        sample_tier = self.i18n.get("alerts.preview.sample_tier") if self.i18n else "1"

        resolved_text = self.template_text.replace("{user}", sample_user)\
            .replace("{amount}", sample_amount)\
            .replace("{tier}", sample_tier)\
            .replace("{platform}", self.platform.capitalize())

        if self.layout_mode == "side":
            self._draw_side_layout(p, w, h, glyph, accent_color, sample_user, resolved_text)
        elif self.layout_mode == "overlay":
            self._draw_overlay_layout(p, w, h, glyph, accent_color, sample_user, resolved_text)
        else:
            self._draw_above_layout(p, w, h, glyph, accent_color, sample_user, resolved_text)

    def _draw_side_layout(self, p: QPainter, w: int, h: int, glyph: str, accent: QColor, user: str, full_text: str):
        card_w = min(420.0, w - 32.0)
        card_h = 68.0
        card_x = (w - card_w) / 2.0
        card_y = (h - card_h) / 2.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        self._draw_card_container(p, card_rect, accent, radius=18.0)

        badge_d = 42.0
        badge_x = card_x + 14.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        p.setBrush(QBrush(QColor(12, 14, 18, 220)))
        p.setPen(QPen(accent, 1.8))
        p.drawEllipse(badge_rect)

        inner_rect = badge_rect.adjusted(3.5, 3.5, -3.5, -3.5)
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 100), 1.0))
        p.drawEllipse(inner_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 12))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = badge_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = badge_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        text_x = badge_x + badge_d + 16.0
        text_w = card_w - (badge_d + 38.0)

        p.setFont(QFont("Outfit", 10.5, QFont.Weight.Bold))
        p.setPen(accent)
        u_rect = QRectF(text_x, card_y + 13.0, text_w, 18.0)
        p.drawText(u_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._elide(user, p.font(), text_w))

        p.setFont(QFont("Inter", 8.5, QFont.Weight.Medium))
        p.setPen(QColor("#E2E8F0" if self.style_mode != "minimal" else "#CBD5E1"))
        msg_rect = QRectF(text_x, card_y + 33.0, text_w, 18.0)
        p.drawText(msg_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._elide(full_text, p.font(), text_w))

    def _draw_above_layout(self, p: QPainter, w: int, h: int, glyph: str, accent: QColor, user: str, full_text: str):
        card_w = min(360.0, w - 32.0)
        card_h = 56.0
        card_x = (w - card_w) / 2.0
        card_y = (h - card_h) / 2.0 + 12.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        icon_size = 38.0
        icon_x = (w - icon_size) / 2.0
        icon_y = card_y - 18.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        self._draw_card_container(p, card_rect, accent, radius=14.0)

        p.setBrush(QBrush(QColor(15, 17, 22)))
        p.setPen(QPen(accent, 2.0))
        p.drawEllipse(icon_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 11))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = icon_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = icon_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        p.setFont(QFont("Outfit", 9.5, QFont.Weight.Bold))
        p.setPen(QColor("#FFFFFF"))
        msg_rect = QRectF(card_x + 12, card_y + 24, card_w - 24, 22)
        p.drawText(msg_rect, Qt.AlignmentFlag.AlignCenter, self._elide(full_text, p.font(), card_w - 24))

    def _draw_overlay_layout(self, p: QPainter, w: int, h: int, glyph: str, accent: QColor, user: str, full_text: str):
        card_w = min(400.0, w - 32.0)
        card_h = 64.0
        card_x = (w - card_w) / 2.0
        card_y = (h - card_h) / 2.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        grad = QLinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
        grad.setColorAt(0.0, QColor(accent.red() // 4, accent.green() // 4, accent.blue() // 4, 230))
        grad.setColorAt(1.0, QColor(10, 12, 16, 245))

        p.setBrush(QBrush(grad))
        p.setPen(QPen(accent if self.style_mode != "glass" else QColor(255, 255, 255, 70), 1.5))
        p.drawRoundedRect(card_rect, 14, 14)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(accent))
        p.drawRoundedRect(QRectF(card_x + 10, card_y + 2, card_w - 20, 2.5), 1, 1)
        p.save()
        p.setFont(QFont("GoogleSansCode Nerd Font", 24))
        p.setPen(QColor(accent.red(), accent.green(), accent.blue(), 35))
        p.drawText(QRectF(card_x + 16, card_y + 10, 48, 48), Qt.AlignmentFlag.AlignCenter, glyph)
        p.restore()

        p.setFont(QFont("Outfit", 10.5, QFont.Weight.ExtraBold))
        p.setPen(QColor("#FFFFFF"))
        t_rect = QRectF(card_x + 16, card_y + 12, card_w - 32, 20)
        p.drawText(t_rect, Qt.AlignmentFlag.AlignCenter, self._elide(user, p.font(), card_w - 32))

        p.setFont(QFont("Inter", 8.5, QFont.Weight.Medium))
        p.setPen(QColor("#CBD5E1"))
        sub_rect = QRectF(card_x + 16, card_y + 34, card_w - 32, 18)
        p.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, self._elide(full_text, p.font(), card_w - 32))

    def _draw_card_container(self, p: QPainter, rect: QRectF, accent: QColor, radius: float):
        if self.style_mode == "compact":
            p.setPen(QPen(accent, 1.8))
            p.setBrush(QBrush(QColor(10, 12, 16, 240)))
            p.drawRoundedRect(rect, radius, radius)

            glow_pen = QPen(QColor(accent.red(), accent.green(), accent.blue(), 55), 3.5)
            p.setPen(glow_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius - 1, radius - 1)

        elif self.style_mode == "glass":
            p.setPen(QPen(QColor(255, 255, 255, 55), 1.25))
            p.setBrush(QBrush(QColor(18, 20, 26, 180)))
            p.drawRoundedRect(rect, radius, radius)

        else:
            p.setPen(QPen(QColor(255, 255, 255, 25), 1.0))
            p.setBrush(QBrush(QColor(14, 16, 22, 210)))
            p.drawRoundedRect(rect, radius, radius)

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
