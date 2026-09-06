# frontend\components\alerts\alert_mockup.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QFont, QFontMetrics
)

class AlertOverlayMockupWidget(QWidget):
    _EVENT_GLYPHS = {
        "follow": ("\uf004", "#38BDF8", "heart"),
        "subscription": ("\uf005", "#F59E0B", "star"),
        "resub": ("\uf130", "#818CF8", "crown"),
        "sub_gift": ("\udb80\udc1a", "#EC4899", "gift"),
        "raid": ("\uf101", "#10B981", "raid"),
        "cheer": ("\udb81\udcc6", "#6366F1", "diamond")
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
        self.setFixedHeight(180)
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
        p.setPen(QPen(QColor("#1F242F"), 1, Qt.PenStyle.SolidLine))
        p.setBrush(QBrush(QColor("#0B0D13")))
        p.drawRoundedRect(canvas_rect.adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)

        glyph, event_color_hex, _ = self._EVENT_GLYPHS.get(self.alert_type.lower(), ("\uf004", "#38BDF8", "heart"))
        platform_color = QColor("#2ECD70" if self.platform == "kick" else "#9146FF")
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
        card_w = min(420.0, w - 28.0)
        card_h = 60.0
        card_x = (w - card_w) / 2.0
        card_y = (h - card_h) / 2.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        self._draw_card_container(p, card_rect, accent, radius=12.0)

        badge_d = 36.0
        badge_x = card_x + 12.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        p.setBrush(QBrush(QColor(18, 22, 30)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 180), 1.2))
        p.drawEllipse(badge_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 11))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = badge_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = badge_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        text_x = badge_x + badge_d + 14.0
        text_w = card_w - (badge_d + 32.0)

        p.setFont(QFont("Outfit", 10.0, QFont.Weight.DemiBold))
        p.setPen(QColor("#F8FAFC"))
        u_rect = QRectF(text_x, card_y + 11.0, text_w, 18.0)
        p.drawText(u_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._elide(user, p.font(), text_w))

        p.setFont(QFont("Inter", 8.5, QFont.Weight.Normal))
        p.setPen(QColor("#94A3B8"))
        msg_rect = QRectF(text_x, card_y + 30.0, text_w, 18.0)
        p.drawText(msg_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._elide(full_text, p.font(), text_w))

    def _draw_above_layout(self, p: QPainter, w: int, h: int, glyph: str, accent: QColor, user: str, full_text: str):
        card_w = min(360.0, w - 28.0)
        card_h = 52.0
        card_x = (w - card_w) / 2.0
        card_y = (h - card_h) / 2.0 + 10.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        icon_size = 32.0
        icon_x = (w - icon_size) / 2.0
        icon_y = card_y - 15.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        self._draw_card_container(p, card_rect, accent, radius=12.0)

        p.setBrush(QBrush(QColor(18, 22, 30)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 180), 1.2))
        p.drawEllipse(icon_rect)

        p.setFont(QFont("GoogleSansCode Nerd Font", 10))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = icon_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = icon_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        p.setFont(QFont("Outfit", 9.5, QFont.Weight.DemiBold))
        p.setPen(QColor("#F8FAFC"))
        msg_rect = QRectF(card_x + 12, card_y + 20, card_w - 24, 22)
        p.drawText(msg_rect, Qt.AlignmentFlag.AlignCenter, self._elide(full_text, p.font(), card_w - 24))

    def _draw_overlay_layout(self, p: QPainter, w: int, h: int, glyph: str, accent: QColor, user: str, full_text: str):
        card_w = min(390.0, w - 28.0)
        card_h = 58.0
        card_x = (w - card_w) / 2.0
        card_y = (h - card_h) / 2.0
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        grad = QLinearGradient(card_x, card_y, card_x + card_w, card_y + card_h)
        grad.setColorAt(0.0, QColor(22, 27, 36, 240))
        grad.setColorAt(1.0, QColor(14, 17, 24, 250))

        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1.0))
        p.drawRoundedRect(card_rect, 12, 12)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(accent.red(), accent.green(), accent.blue(), 180)))
        p.drawRoundedRect(QRectF(card_x + 12, card_y + 1, card_w - 24, 2.0), 1, 1)

        p.setFont(QFont("Outfit", 10.0, QFont.Weight.Bold))
        p.setPen(QColor("#F8FAFC"))
        t_rect = QRectF(card_x + 16, card_y + 10, card_w - 32, 18)
        p.drawText(t_rect, Qt.AlignmentFlag.AlignCenter, self._elide(user, p.font(), card_w - 32))

        p.setFont(QFont("Inter", 8.5, QFont.Weight.Normal))
        p.setPen(QColor("#94A3B8"))
        sub_rect = QRectF(card_x + 16, card_y + 30, card_w - 32, 18)
        p.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, self._elide(full_text, p.font(), card_w - 32))

    def _draw_card_container(self, p: QPainter, rect: QRectF, accent: QColor, radius: float):
        if self.style_mode == "compact":
            p.setPen(QPen(QColor("#2E384D"), 1.2))
            p.setBrush(QBrush(QColor(15, 18, 25, 245)))
            p.drawRoundedRect(rect, radius, radius)

        elif self.style_mode == "glass":
            p.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
            p.setBrush(QBrush(QColor(24, 28, 38, 190)))
            p.drawRoundedRect(rect, radius, radius)

        else:
            p.setPen(QPen(QColor(255, 255, 255, 20), 1.0))
            p.setBrush(QBrush(QColor(13, 16, 22, 230)))
            p.drawRoundedRect(rect, radius, radius)

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
