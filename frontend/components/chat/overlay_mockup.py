# frontend\components\chat\overlay_mockup.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath, QLinearGradient, QFont, QFontMetrics
)

class ChatOverlayMockupWidget(QWidget):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.theme_mode = "glass"
        self.orientation = "vertical"
        self.show_time = False
        self.show_bots = False
        self.setFixedHeight(180)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_configuration(self, theme: str, orientation: str, show_time: bool = False, show_bots: bool = False):
        new_theme = theme or "glass"
        new_orientation = orientation or "vertical"
        changed = (
            self.theme_mode != new_theme
            or self.orientation != new_orientation
            or self.show_time != show_time
            or self.show_bots != show_bots
        )
        if changed:
            self.theme_mode = new_theme
            self.orientation = new_orientation
            self.show_time = show_time
            self.show_bots = show_bots
            self.setFixedHeight(105 if self.orientation == "horizontal" else 155)
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
        sample_user = self.i18n.get("chat.overlay.preview_sample_user") if self.i18n else "TheAndro2K"
        sample_msg_1 = self.i18n.get("chat.overlay.preview_sample_msg_1") if self.i18n else "hola xd"
        sample_bot_user = self.i18n.get("chat.overlay.preview_sample_bot_user") if self.i18n else "theandro2k"
        sample_bot_msg = self.i18n.get("chat.overlay.preview_sample_bot_msg") if self.i18n else "¡Qué onda @TheAndro2K! Bienvenido al stream 👾"

        if self.orientation == "horizontal":
            self._draw_horizontal(p, w, h, sample_user, sample_msg_1, sample_bot_user, sample_bot_msg)
        else:
            self._draw_vertical(p, w, h, sample_user, sample_msg_1, sample_bot_user, sample_bot_msg)

    def _draw_horizontal(self, p: QPainter, w: int, h: int, user: str, msg1: str, bot_user: str, bot_msg: str):
        p.save()
        p.setClipRect(QRectF(8, 8, w - 16, h - 16))

        pill_h = 32.0
        pill_y = (h - pill_h) / 2.0
        start_x = 14.0

        m1_w = self._calculate_horizontal_width(p, user, msg1, is_bot=False)
        self._draw_horizontal_pill(p, start_x, pill_y, m1_w, pill_h, "10:49:05", user, msg1, "#FACC15", is_bot=False)

        if self.show_bots or (start_x + m1_w + 12 < w):
            start_x2 = start_x + m1_w + 12
            m2_w = self._calculate_horizontal_width(p, bot_user, bot_msg, is_bot=True)
            self._draw_horizontal_pill(p, start_x2, pill_y, m2_w, pill_h, "10:49:15", bot_user, bot_msg, "#A855F7", is_bot=True)

        p.restore()

    def _calculate_horizontal_width(self, p: QPainter, user: str, msg: str, is_bot: bool) -> float:
        font_main = QFont("Google Sans", 8, QFont.Weight.Bold)
        fm = QFontMetrics(font_main)
        user_w = fm.horizontalAdvance(user + ": ")
        msg_w = fm.horizontalAdvance(msg)

        base = 10 + 40 + 10
        if self.show_time:
            base += fm.horizontalAdvance("[10:49:05] ") + 4
        return base + user_w + msg_w

    def _draw_horizontal_pill(self, p: QPainter, x: float, y: float, width: float, height: float,
                              time_str: str, user: str, msg: str, color_hex: str, is_bot: bool):
        rect = QRectF(x, y, width, height)
        color = QColor(color_hex)

        self._apply_pill_theme(p, rect, color)

        curr_x = x + 10.0
        if self.show_time:
            p.setFont(QFont("Google Sans", 7, QFont.Weight.Medium))
            p.setPen(QColor(255, 255, 255, 140))
            time_rect = QRectF(curr_x, y, 54, height)
            p.drawText(time_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"[{time_str}]")
            curr_x += 54.0

        platform = "twitch" if not is_bot else "kick"
        self._draw_badge(p, curr_x, y + (height - 16) / 2, platform)
        curr_x += 19.0
        role = "broadcaster" if not is_bot else "bot"
        self._draw_badge(p, curr_x, y + (height - 16) / 2, role)
        curr_x += 21.0

        p.setFont(QFont("Google Sans", 8, QFont.Weight.Bold if self.theme_mode != "cyber" else QFont.Weight.ExtraBold))
        display_user = (user.upper() if self.theme_mode == "cyber" else user) + ":"
        fm_user = QFontMetrics(p.font())
        user_w = fm_user.horizontalAdvance(display_user)
        p.setPen(color)

        user_rect = QRectF(curr_x, y, user_w, height)
        p.drawText(user_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_user)
        curr_x += user_w + 6.0

        p.setFont(QFont("Google Sans", 8, QFont.Weight.Medium))
        p.setPen(QColor("#FFFFFF") if self.theme_mode != "card" else QColor("#F1F1F5"))
        msg_rect = QRectF(curr_x, y, width - (curr_x - x) - 8, height)
        p.drawText(msg_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, msg)

    def _apply_pill_theme(self, p: QPainter, rect: QRectF, accent_color: QColor):
        if self.theme_mode == "neon":
            p.setPen(QPen(accent_color, 1.75))
            p.setBrush(QBrush(QColor(6, 6, 12, 235)))
            p.drawRoundedRect(rect, 15, 15)
            glow_pen = QPen(QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 60), 3.5)
            p.setPen(glow_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)

        elif self.theme_mode == "glass":
            p.setPen(QPen(QColor(255, 255, 255, 55), 1.25))
            p.setBrush(QBrush(QColor(18, 18, 26, 175)))
            p.drawRoundedRect(rect, 16, 16)

        elif self.theme_mode == "card":
            p.setPen(QPen(QColor("#282A36"), 1.25))
            p.setBrush(QBrush(QColor("#181920")))
            p.drawRoundedRect(rect, 12, 12)

        elif self.theme_mode == "cyber":
            p.setPen(QPen(QColor(0, 240, 255, 120), 1.0))
            p.setBrush(QBrush(QColor(8, 14, 20, 240)))
            path = self._create_chamfered_path(rect, 8.0)
            p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(accent_color))
            p.drawRect(QRectF(rect.x(), rect.y() + 6, 3, rect.height() - 12))

        elif self.theme_mode == "minimal":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_vertical(self, p: QPainter, w: int, h: int, user: str, msg1: str, bot_user: str, bot_msg: str):
        card_w = min(360.0, w - 28.0)
        card_h = 58.0
        card_x = (w - card_w) / 2.0
        gap = 8.0

        y1 = 12.0
        rect1 = QRectF(card_x, y1, card_w, card_h)
        self._draw_vertical_card(p, rect1, "10:49:05", user, msg1, "#FACC15", is_bot=False)
        y2 = y1 + card_h + gap
        if y2 + card_h <= h - 4:
            rect2 = QRectF(card_x, y2, card_w, card_h)
            self._draw_vertical_card(p, rect2, "10:49:15", bot_user, bot_msg, "#A855F7", is_bot=True)

    def _draw_vertical_card(self, p: QPainter, rect: QRectF, time_str: str, user: str, msg: str, color_hex: str, is_bot: bool):
        color = QColor(color_hex)
        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()

        if self.theme_mode == "neon":
            p.setPen(QPen(color, 1.75))
            p.setBrush(QBrush(QColor(6, 6, 12, 235)))
            p.drawRoundedRect(rect, 12, 12)
            glow_pen = QPen(QColor(color.red(), color.green(), color.blue(), 50), 3)
            p.setPen(glow_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 11, 11)

        elif self.theme_mode == "glass":
            p.setPen(QPen(QColor(255, 255, 255, 45), 1.25))
            p.setBrush(QBrush(QColor(18, 18, 26, 175)))
            p.drawRoundedRect(rect, 14, 14)

        elif self.theme_mode == "card":
            p.setPen(QPen(QColor("#282A36"), 1.25))
            p.setBrush(QBrush(QColor("#181920")))
            p.drawRoundedRect(rect, 12, 12)

        elif self.theme_mode == "cyber":
            p.setPen(QPen(QColor(0, 240, 255, 110), 1.0))
            p.setBrush(QBrush(QColor(8, 14, 20, 240)))
            path = self._create_chamfered_path(rect, 10.0)
            p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawRect(QRectF(x, y + 8, 3.5, h - 16))

        elif self.theme_mode == "minimal":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Qt.BrushStyle.NoBrush)

        curr_x = x + 12.0
        header_y = y + 10.0

        if self.show_time:
            p.setFont(QFont("Google Sans", 7, QFont.Weight.Medium))
            p.setPen(QColor(255, 255, 255, 130))
            p.drawText(QRectF(curr_x, header_y - 2, 54, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"[{time_str}]")
            curr_x += 54.0

        platform = "twitch" if not is_bot else "kick"
        self._draw_badge(p, curr_x, header_y, platform)
        curr_x += 19.0

        role = "broadcaster" if not is_bot else "bot"
        self._draw_badge(p, curr_x, header_y, role)
        curr_x += 21.0

        p.setFont(QFont("Google Sans", 8.5, QFont.Weight.Bold if self.theme_mode != "cyber" else QFont.Weight.ExtraBold))
        display_user = user.upper() if self.theme_mode == "cyber" else user
        fm_user = QFontMetrics(p.font())
        u_w = fm_user.horizontalAdvance(display_user)

        if self.theme_mode == "card":
            pill_rect = QRectF(curr_x, header_y - 2, u_w + 12, 18)
            p.setPen(QPen(QColor(255, 255, 255, 20), 1))
            p.setBrush(QBrush(QColor(255, 255, 255, 22)))
            p.drawRoundedRect(pill_rect, 5, 5)
            p.setPen(color)
            p.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, display_user)
        else:
            p.setPen(color)
            p.drawText(QRectF(curr_x, header_y - 2, u_w + 4, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_user)

        msg_y = y + 32.0
        msg_x = x + 12.0
        msg_w = w - 24.0

        p.setFont(QFont("Google Sans", 8, QFont.Weight.Medium))
        p.setPen(QColor("#FFFFFF") if self.theme_mode != "card" else QColor("#F1F1F5"))
        elided_msg = self._elide(msg, p.font(), msg_w)
        p.drawText(QRectF(msg_x, msg_y, msg_w, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_msg)

    def _create_chamfered_path(self, rect: QRectF, cut: float) -> QPainterPath:
        path = QPainterPath()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        path.moveTo(x + cut, y)
        path.lineTo(x + w, y)
        path.lineTo(x + w, y + h - cut)
        path.lineTo(x + w - cut, y + h)
        path.lineTo(x, y + h)
        path.lineTo(x, y + cut)
        path.closeSubpath()
        return path

    _BADGE_CONFIG = {
        "twitch": ("\uf1e8", "#9146FF", "#772CE8", "#ffffff"),
        "kick": ("\uf2f3", "#53FC18", "#3DB510", "#000000"),
        "youtube": ("\uf16a", "#FF0000", "#DC2626", "#ffffff"),
        "tiktok": ("\udb80\udf8c", "#00F2FE", "#FF0050", "#ffffff"),
        "broadcaster": ("\uf130", "#EF4444", "#DC2626", "#ffffff"),
        "streamer": ("\uf130", "#EF4444", "#DC2626", "#ffffff"),
        "moderator": ("\ued25", "#2ECD70", "#16A34A", "#ffffff"),
        "vip": ("\uedeb", "#EAB308", "#CA8A04", "#ffffff"),
        "subscriber": ("\udb83\ude44", "#A855F7", "#9333EA", "#ffffff"),
        "bot": ("\uee0d", "#3B82F6", "#2563EB", "#ffffff"),
    }

    def _draw_badge(self, p: QPainter, x: float, y: float, badge_type: str):
        size = 15.5
        rect = QRectF(x, y, size, size)
        p.save()
        p.setPen(Qt.PenStyle.NoPen)

        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, 4, 4)
        p.setClipPath(clip_path)

        config = self._BADGE_CONFIG.get(badge_type.lower())
        if config:
            glyph, col1, col2, fg_col = config
            grad = QLinearGradient(x, y, x + size, y + size)
            grad.setColorAt(0.0, QColor(col1))
            grad.setColorAt(1.0, QColor(col2))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(rect, 4, 4)

            font = QFont("GoogleSansCode Nerd Font", 7.5)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            p.setFont(font)
            p.setPen(QColor(fg_col))

            fm = QFontMetrics(font)
            tb = fm.tightBoundingRect(glyph)
            glyph_x = rect.center().x() - tb.x() - tb.width() / 2.0
            glyph_y = rect.center().y() - tb.y() - tb.height() / 2.0
            p.drawText(QPointF(glyph_x, glyph_y), glyph)
        else:
            p.setBrush(QBrush(QColor("#4B5563")))
            p.drawRoundedRect(rect, 4, 4)

        p.restore()

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
