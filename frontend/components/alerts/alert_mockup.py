# frontend\components\alerts\alert_mockup.py

import os
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QFontMetrics, QPainterPath,
    QPixmap, QLinearGradient
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
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def sizeHint(self) -> QSize:
        return QSize(340, 340)

    def minimumSizeHint(self) -> QSize:
        return QSize(180, 180)

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

        side = min(w, h) - 6
        if side < 140:
            side = 140
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
        avail_space = side - 16.0
        if self.card_height > 0:
            target_w = max(100.0, float(self.card_width))
            target_h = max(40.0, float(self.card_height))
            scale = min(avail_space / target_w, avail_space / target_h)
            card_w = max(60.0, min(avail_space, target_w * scale))
            card_h = max(40.0, min(avail_space, target_h * scale))
        else:
            scale = min(1.0, avail_space / 560.0)
            card_w = min(avail_space, max(120.0, float(self.card_width) * scale))
            card_h = min(avail_space, max(50.0, default_h * (avail_space / 240.0)))

        card_x = cx + (side - card_w) / 2.0
        card_y = cy + (side - card_h) / 2.0
        return card_x, card_y, card_w, card_h, QRectF(card_x, card_y, card_w, card_h)

    def _draw_media_box(self, p: QPainter, rect: QRectF, glyph: str, accent: QColor):
        p.save()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, 8.0, 8.0)
        p.setClipPath(clip_path)

        drawn_media = False
        if self.media_path and os.path.isfile(self.media_path):
            ext = os.path.splitext(self.media_path)[1].lower()
            if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp'):
                pix = QPixmap(self.media_path)
                if not pix.isNull():
                    scaled_pix = pix.scaled(
                        int(rect.width()), int(rect.height()),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    sx = int(rect.x() + (rect.width() - scaled_pix.width()) / 2)
                    sy = int(rect.y() + (rect.height() - scaled_pix.height()) / 2)
                    p.drawPixmap(sx, sy, scaled_pix)
                    drawn_media = True

        if not drawn_media:
            p.setBrush(QBrush(QColor(18, 22, 30, 240)))
            p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 1.5))
            p.drawRoundedRect(rect, 8.0, 8.0)

            p.setFont(QFont("GoogleSansCode Nerd Font", int(min(rect.width(), rect.height()) * 0.4)))
            p.setPen(accent)
            fm = QFontMetrics(p.font())
            tb = fm.tightBoundingRect(glyph)
            gx = rect.center().x() - tb.x() - tb.width() / 2.0
            gy = rect.center().y() - tb.y() - tb.height() / 2.0
            p.drawText(QPointF(gx, gy), glyph)

        p.restore()

    def _draw_above_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 96.0)
        self._draw_card_container(p, card_rect, accent)

        badge_w = 54.0
        badge_h = 14.0
        badge_rect = QRectF(card_x + (card_w - badge_w) / 2.0, card_y + 8.0, badge_w, badge_h)
        badge_bg = QColor("#9146FF") if self.platform == "twitch" else QColor("#53FC18")
        badge_fg = QColor("#FFFFFF") if self.platform == "twitch" else QColor("#000000")
        p.setBrush(QBrush(badge_bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(badge_rect, 7.0, 7.0)
        p.setFont(QFont("Inter", 6, QFont.Weight.Bold))
        p.setPen(badge_fg)
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, self.platform.upper())

        icon_size = max(26.0, min(54.0, card_h * 0.36))
        icon_x = card_x + (card_w - icon_size) / 2.0
        icon_y = card_y + badge_h + 12.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        self._draw_media_box(p, icon_rect, glyph, accent)

        scale_factor = card_w / 560.0
        font_size = max(8.5, min(14.0, self.font_size * scale_factor * 1.2))
        title_font = QFont(self.font_family, int(font_size), self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        text_y = icon_y + icon_size + 6.0
        text_h = max(18.0, card_h - (text_y - card_y) - 6.0)
        msg_rect = QRectF(card_x + 8, text_y, card_w - 16, text_h)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, title_font, card_w - 16))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, title_font, card_w - 16))

    def _draw_below_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 96.0)
        self._draw_card_container(p, card_rect, accent)

        badge_w = 54.0
        badge_h = 14.0
        badge_rect = QRectF(card_x + (card_w - badge_w) / 2.0, card_y + 8.0, badge_w, badge_h)
        badge_bg = QColor("#9146FF") if self.platform == "twitch" else QColor("#53FC18")
        badge_fg = QColor("#FFFFFF") if self.platform == "twitch" else QColor("#000000")
        p.setBrush(QBrush(badge_bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(badge_rect, 7.0, 7.0)
        p.setFont(QFont("Inter", 6, QFont.Weight.Bold))
        p.setPen(badge_fg)
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, self.platform.upper())

        scale_factor = card_w / 560.0
        font_size = max(8.5, min(14.0, self.font_size * scale_factor * 1.2))
        title_font = QFont(self.font_family, int(font_size), self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        text_y = card_y + badge_h + 10.0
        msg_rect = QRectF(card_x + 8, text_y, card_w - 16, 22.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, title_font, card_w - 16))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, title_font, card_w - 16))

        icon_size = max(26.0, min(54.0, card_h * 0.36))
        icon_x = card_x + (card_w - icon_size) / 2.0
        icon_y = card_y + card_h - icon_size - 10.0
        icon_rect = QRectF(icon_x, icon_y, icon_size, icon_size)

        self._draw_media_box(p, icon_rect, glyph, accent)

    def _draw_side_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 72.0)
        self._draw_card_container(p, card_rect, accent)

        badge_d = min(56.0, max(36.0, card_h - 16.0))
        badge_x = card_x + 10.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        self._draw_media_box(p, badge_rect, glyph, accent)

        text_x = card_x + badge_d + 16.0
        text_w = max(40.0, card_w - (badge_d + 24.0))

        scale_factor = card_w / 560.0
        font_size = max(8.5, min(14.0, self.font_size * scale_factor * 1.2))
        title_font = QFont(self.font_family, int(font_size), self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(text_x, card_y + 10.0, text_w, 20.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(user, title_font, text_w))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, text_w))

        sub_font = QFont("Inter", 8.0, QFont.Weight.Normal)
        p.setFont(sub_font)
        msg_rect = QRectF(text_x, card_y + 32.0, text_w, 18.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, sub_font, text_w))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, sub_font, text_w))

    def _draw_side_right_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 72.0)
        self._draw_card_container(p, card_rect, accent)

        badge_d = min(56.0, max(36.0, card_h - 16.0))
        badge_x = card_x + card_w - badge_d - 10.0
        badge_y = card_y + (card_h - badge_d) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_d, badge_d)

        self._draw_media_box(p, badge_rect, glyph, accent)

        text_x = card_x + 10.0
        text_w = max(40.0, card_w - (badge_d + 20.0))

        scale_factor = card_w / 560.0
        font_size = max(8.5, min(14.0, self.font_size * scale_factor * 1.2))
        title_font = QFont(self.font_family, int(font_size), self._get_font_weight())
        p.setFont(title_font)

        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter
        t_rect = QRectF(text_x, card_y + 10.0, text_w, 20.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(user, title_font, text_w))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(user, title_font, text_w))

        sub_font = QFont("Inter", 8.0, QFont.Weight.Normal)
        p.setFont(sub_font)
        msg_rect = QRectF(text_x, card_y + 32.0, text_w, 18.0)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, sub_font, text_w))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(full_text, sub_font, text_w))

    def _draw_overlay_layout(self, p: QPainter, cx: float, cy: float, side: float, glyph: str, accent: QColor, text_color: QColor, user: str, full_text: str):
        card_x, card_y, card_w, card_h, card_rect = self._get_card_geometry(cx, cy, side, 120.0)

        r = max(0.0, float(self.border_radius) * (card_w / max(1.0, float(self.card_width))))
        p.save()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(card_rect, r, r)
        p.setClipPath(clip_path)

        drawn_media = False
        if self.media_path and os.path.isfile(self.media_path):
            ext = os.path.splitext(self.media_path)[1].lower()
            if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp'):
                pix = QPixmap(self.media_path)
                if not pix.isNull():
                    scaled_pix = pix.scaled(
                        int(card_rect.width()), int(card_rect.height()),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    sx = int(card_rect.x() + (card_rect.width() - scaled_pix.width()) / 2)
                    sy = int(card_rect.y() + (card_rect.height() - scaled_pix.height()) / 2)
                    p.drawPixmap(sx, sy, scaled_pix)
                    drawn_media = True

        if not drawn_media:
            grad = QLinearGradient(card_rect.topLeft(), card_rect.bottomRight())
            grad.setColorAt(0, QColor(34, 38, 50))
            grad.setColorAt(1, QColor(18, 22, 30))
            p.fillRect(card_rect, grad)
            if not self.media_path:
                p.setFont(QFont("GoogleSansCode Nerd Font", int(min(card_w, card_h) * 0.3)))
                p.setPen(QColor(255, 255, 255, 35))
                p.drawText(card_rect, Qt.AlignmentFlag.AlignCenter, glyph)

        p.restore()

        self._draw_card_container(p, card_rect, accent)

        badge_text = self.platform.upper()
        badge_bg = QColor("#9146FF") if self.platform == "twitch" else QColor("#53FC18")
        badge_fg = QColor("#FFFFFF") if self.platform == "twitch" else QColor("#000000")
        badge_w = 64.0
        badge_h = 18.0

        scale_factor = card_w / 560.0
        title_pt = max(9.5, min(22.0, self.font_size * scale_factor * 1.3))
        title_font = QFont(self.font_family, int(title_pt), self._get_font_weight())
        sub_pt = max(7.5, min(14.0, title_pt * 0.65))
        sub_font = QFont(self.font_family, int(sub_pt), QFont.Weight.Normal)

        fm_title = QFontMetrics(title_font)
        fm_sub = QFontMetrics(sub_font)
        title_h = fm_title.height() * 1.25
        sub_h = fm_sub.height()

        gap = 6.0
        total_content_h = badge_h + gap + title_h + (gap + sub_h)
        start_y = card_y + (card_h - total_content_h) / 2.0

        badge_rect = QRectF(card_x + (card_w - badge_w) / 2.0, start_y, badge_w, badge_h)
        p.setBrush(QBrush(badge_bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(badge_rect, 9.0, 9.0)

        badge_font = QFont("Inter", 7, QFont.Weight.Bold)
        p.setFont(badge_font)
        p.setPen(badge_fg)
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

        t_y = start_y + badge_h + gap
        t_rect = QRectF(card_x + 10.0, t_y, card_w - 20.0, title_h)
        align_flag = self._get_alignment_flag(Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter
        p.setFont(title_font)

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(t_rect.adjusted(1.2, 1.2, 1.2, 1.2), align_flag, self._elide(full_text, title_font, card_w - 20.0))

        p.setPen(accent)
        p.drawText(t_rect, align_flag, self._elide(full_text, title_font, card_w - 20.0))

        msg_y = t_y + title_h + 3.0
        msg_rect = QRectF(card_x + 10.0, msg_y, card_w - 20.0, sub_h)
        sub_font.setItalic(True)
        p.setFont(sub_font)
        sample_msg = '"¡Hola a todos!"'

        if self.text_shadow:
            p.setPen(QColor(0, 0, 0, 220))
            p.drawText(msg_rect.adjusted(1.0, 1.0, 1.0, 1.0), align_flag, self._elide(sample_msg, sub_font, card_w - 20.0))

        p.setPen(text_color)
        p.drawText(msg_rect, align_flag, self._elide(sample_msg, sub_font, card_w - 20.0))

    def _draw_card_container(self, p: QPainter, rect: QRectF, accent: QColor):
        opacity_alpha = int(max(0, min(100, self.bg_opacity)) * 2.55)
        r = max(0.0, float(self.border_radius) * (rect.width() / max(1.0, float(self.card_width))))

        if self.box_shadow:
            p.save()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, 100)))
            p.drawRoundedRect(rect.translated(0, 4), r, r)
            p.restore()

        if opacity_alpha <= 3:
            return

        bg_c = QColor(self.bg_color)
        bg_c.setAlpha(opacity_alpha)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg_c))
        p.drawRoundedRect(rect, r, r)

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
