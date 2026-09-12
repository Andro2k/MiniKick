# frontend\components\alerts\alert_mockup.py

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QFontMetrics, QPainterPath
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
        self.bg_color = "#121317"
        self.bg_opacity = 88
        self.border_radius = 20
        self.padding_px = 24
        self.spacing_px = 16
        self.box_shadow = True
        self.font_weight = "bold"
        self.text_shadow = True
        self.card_width = 560
        self.card_height = 0
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
        style: str = "compact",
        template: str = "",
        media_path: str = "",
        text_template: str = "",
        text_color: str = "#FFFFFF",
        highlight_color: str = "",
        font_family: str = "Outfit",
        font_size: int = 24,
        text_align: str = "center",
        bg_color: str = "#121317",
        bg_opacity: int = 88,
        border_radius: int = 20,
        padding_px: int = 24,
        spacing_px: int = 16,
        box_shadow: bool = True,
        font_weight: str = "bold",
        text_shadow: bool = True,
        card_width: int = 560,
        card_height: int = 0
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
        new_bg = bg_color or "#121317"
        new_opacity = bg_opacity if bg_opacity is not None else 88
        new_radius = border_radius if border_radius is not None else 20
        new_padding = padding_px if padding_px is not None else 24
        new_spacing = spacing_px if spacing_px is not None else 16
        new_weight = font_weight or "bold"
        new_card_w = card_width if card_width is not None else 560
        new_card_h = card_height if card_height is not None else 0

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
            or self.bg_color != new_bg
            or self.bg_opacity != new_opacity
            or self.border_radius != new_radius
            or self.padding_px != new_padding
            or self.spacing_px != new_spacing
            or self.box_shadow != box_shadow
            or self.font_weight != new_weight
            or self.text_shadow != text_shadow
            or self.card_width != new_card_w
            or self.card_height != new_card_h
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
            self.bg_color = new_bg
            self.bg_opacity = new_opacity
            self.border_radius = new_radius
            self.padding_px = new_padding
            self.spacing_px = new_spacing
            self.box_shadow = box_shadow
            self.font_weight = new_weight
            self.text_shadow = text_shadow
            self.card_width = new_card_w
            self.card_height = new_card_h
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
        elif self.text_align in ("center", "justify"):
            return Qt.AlignmentFlag.AlignCenter
        return default_align

    def _get_font_weight(self) -> QFont.Weight:
        w = str(self.font_weight).lower()
        if w in ("normal", "400"):
            return QFont.Weight.Normal
        if w in ("semi_bold", "600"):
            return QFont.Weight.DemiBold
        if w in ("extra_bold", "800"):
            return QFont.Weight.ExtraBold
        return QFont.Weight.Bold

    def _get_card_geometry(self, cx: float, cy: float, side: float, default_h: float) -> tuple[float, float, float, float, QRectF]:
        base_w = side - 20.0
        ratio_w = max(0.45, min(1.25, self.card_width / 560.0))
        card_w = max(110.0, min(side - 12.0, base_w * ratio_w))

        if self.card_height > 0:
            ratio_h = max(0.5, min(1.5, self.card_height / 200.0))
            card_h = max(44.0, min(side - 16.0, default_h * ratio_h))
        else:
            card_h = default_h

        card_x = cx + (side - card_w) / 2.0
        card_y = cy + (side - card_h) / 2.0
        return card_x, card_y, card_w, card_h, QRectF(card_x, card_y, card_w, card_h)

    def _draw_above_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 86.0)
        self._draw_card_container(p, card_rect, accent)

        icon_size = 32.0
        icon_x = card_x + (card_w - icon_size) / 2.0
        icon_y = card_y + 10.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        p.setBrush(QBrush(QColor(18, 22, 30, 240)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawRoundedRect(icon_rect, 8.0, 8.0)

        p.setFont(QFont("GoogleSansCode Nerd Font", 12))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = icon_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = icon_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        font_size = max(8.5, min(13.0, self.font_size * 0.42))
        title_font = QFont(self.font_family, font_size, self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        text_y = icon_y + icon_size + 6.0
        text_h = max(20.0, card_h - (text_y - card_y) - 6.0)
        msg_rect = QRectF(card_x + 8, text_y, card_w - 16, text_h)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, title_font, card_w - 16))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, title_font, card_w - 16))

    def _draw_below_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 86.0)
        self._draw_card_container(p, card_rect, accent)

        font_size = max(8.5, min(13.0, self.font_size * 0.42))
        title_font = QFont(self.font_family, font_size, self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        msg_rect = QRectF(card_x + 8, card_y + 10.0, card_w - 16, 24.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, title_font, card_w - 16))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, title_font, card_w - 16))

        icon_size = 32.0
        icon_x = card_x + (card_w - icon_size) / 2.0
        icon_y = card_y + card_h - icon_size - 10.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        p.setBrush(QBrush(QColor(18, 22, 30, 240)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawRoundedRect(icon_rect, 8.0, 8.0)

        p.setFont(QFont("GoogleSansCode Nerd Font", 12))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = icon_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = icon_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

    def _draw_side_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 68.0)
        self._draw_card_container(p, card_rect, accent)

        badge_d = 38.0
        badge_x = card_x + 10.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        p.setBrush(QBrush(QColor(18, 22, 30, 240)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawRoundedRect(badge_rect, 10.0, 10.0)

        p.setFont(QFont("GoogleSansCode Nerd Font", 12))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = badge_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = badge_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        text_x = card_x + badge_d + 18.0
        text_w = max(40.0, card_w - (badge_d + 26.0))

        font_size = max(8.5, min(13.0, self.font_size * 0.42))
        title_font = QFont(self.font_family, font_size, self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(text_x, card_y + 12.0, text_w, 20.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(user, title_font, text_w))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, text_w))

        sub_font = QFont("Inter", 8.0, QFont.Weight.Normal)
        p.setFont(sub_font)
        msg_rect = QRectF(text_x, card_y + 34.0, text_w, 18.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, sub_font, text_w))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, sub_font, text_w))

    def _draw_side_right_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 68.0)
        self._draw_card_container(p, card_rect, accent)

        badge_d = 38.0
        badge_x = card_x + card_w - badge_d - 10.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        p.setBrush(QBrush(QColor(18, 22, 30, 240)))
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
        p.drawRoundedRect(badge_rect, 10.0, 10.0)

        p.setFont(QFont("GoogleSansCode Nerd Font", 12))
        p.setPen(accent)
        fm = QFontMetrics(p.font())
        tb = fm.tightBoundingRect(glyph)
        gx = badge_rect.center().x() - tb.x() - tb.width() / 2.0
        gy = badge_rect.center().y() - tb.y() - tb.height() / 2.0
        p.drawText(QPointF(gx, gy), glyph)

        text_x = card_x + 10.0
        text_w = max(40.0, card_w - (badge_d + 20.0))

        font_size = max(8.5, min(13.0, self.font_size * 0.42))
        title_font = QFont(self.font_family, font_size, self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(text_x, card_y + 12.0, text_w, 20.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(user, title_font, text_w))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, text_w))

        sub_font = QFont("Inter", 8.0, QFont.Weight.Normal)
        p.setFont(sub_font)
        msg_rect = QRectF(text_x, card_y + 34.0, text_w, 18.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, sub_font, text_w))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, sub_font, text_w))

    def _draw_overlay_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 72.0)
        self._draw_card_container(p, card_rect, accent)

        font_size = max(8.5, min(13.0, self.font_size * 0.42))
        title_font = QFont(self.font_family, font_size, self._get_font_weight())
        p.setFont(title_font)
        p.setPen(accent)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(card_x + 14, card_y + 12, card_w - 28, 20)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(user, title_font, card_w - 28))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, card_w - 28))

        sub_font = QFont("Inter", 8.0, QFont.Weight.Normal)
        p.setFont(sub_font)
        sub_rect = QRectF(card_x + 14, card_y + 36, card_w - 28, 18)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(sub_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, sub_font, card_w - 28))

        p.setPen(text_color)
        p.drawText(sub_rect, align_flag, self._elide(full_text, sub_font, card_w - 28))

    def _draw_card_container(self, p: QPainter, rect: QRectF, accent: QColor):
        opacity_alpha = int(max(0, min(100, self.bg_opacity)) * 2.55)
        if opacity_alpha <= 3:
            return

        bg_c = QColor(self.bg_color)
        bg_c.setAlpha(opacity_alpha)

        r = max(0.0, float(self.border_radius) * 0.5)

        if self.box_shadow:
            p.save()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, min(110, opacity_alpha))))
            p.drawRoundedRect(rect.translated(0, 3), r, r)
            p.restore()

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg_c))
        p.drawRoundedRect(rect, r, r)

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
