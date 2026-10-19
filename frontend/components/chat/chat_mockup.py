# frontend\components\chat\chat_mockup.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath, QLinearGradient, QFont, QFontMetrics
)
from frontend.common import (
    CHAT_PREVIEW_AVATAR_GRADIENTS, COLOR_TWITCH, COLOR_TWITCH_DARK,
    COLOR_KICK, COLOR_YOUTUBE, COLOR_RED_DARK,
    COLOR_TIKTOK, COLOR_TIKTOK_ACCENT,
    COLOR_RED, COLOR_GREEN, COLOR_GREEN_SOLID, COLOR_AMBER,
    COLOR_AMBER_DARK, COLOR_PURPLE, COLOR_PURPLE_DARK,
    COLOR_BLUE, COLOR_BLUE_DARK, COLOR_WHITE, COLOR_PURE_WHITE,
    COLOR_BLACK, COLOR_LIGHT_TEXT_PRIMARY, COLOR_LIGHT_TEXT_MUTED,
    COLOR_CHAT_PREVIEW_SURFACE, COLOR_CHAT_PREVIEW_BADGE,
    COLOR_CALLOUT_WARNING_LIGHT, COLOR_CODE_LINK, get_qcolor_with_alpha,
)
from frontend.components.mockup_helpers import init_mockup_painter, draw_mockup_canvas

VALID_CHAT_THEMES = frozenset({"dark", "light", "minimal"})
DEFAULT_CHAT_THEME = "dark"

class ChatOverlayMockupWidget(QWidget):
    _AVATAR_GRADIENTS = CHAT_PREVIEW_AVATAR_GRADIENTS

    _BADGE_CONFIG = {
        "twitch": ("\uf1e8", COLOR_TWITCH, COLOR_TWITCH_DARK, COLOR_PURE_WHITE),
        "kick": ("\uf2f3", COLOR_KICK, COLOR_GREEN_SOLID, COLOR_BLACK),
        "youtube": ("\uf16a", COLOR_YOUTUBE, COLOR_RED_DARK, COLOR_PURE_WHITE),
        "tiktok": ("\udb80\udf8c", COLOR_TIKTOK, COLOR_TIKTOK_ACCENT, COLOR_PURE_WHITE),
        "broadcaster": ("\uf130", COLOR_RED, COLOR_RED_DARK, COLOR_PURE_WHITE),
        "streamer": ("\uf130", COLOR_RED, COLOR_RED_DARK, COLOR_PURE_WHITE),
        "moderator": ("\ued25", COLOR_GREEN, COLOR_GREEN_SOLID, COLOR_PURE_WHITE),
        "vip": ("\uedeb", COLOR_AMBER, COLOR_AMBER_DARK, COLOR_PURE_WHITE),
        "subscriber": ("\udb83\ude44", COLOR_PURPLE, COLOR_PURPLE_DARK, COLOR_PURE_WHITE),
        "bot": ("\uee0d", COLOR_BLUE, COLOR_BLUE_DARK, COLOR_PURE_WHITE),
    }

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.theme_mode = DEFAULT_CHAT_THEME
        self.orientation = "vertical"
        self.show_time = False
        self.show_bots = False
        self.show_badges = True
        self.show_platform = True
        self.hide_commands = False
        self.big_emotes = True
        self.show_gifs = True
        self.setFixedHeight(180)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_configuration(
        self,
        theme: str,
        orientation: str,
        show_time: bool = False,
        show_bots: bool = False,
        show_badges: bool = True,
        show_platform: bool = True,
        hide_commands: bool = False,
        big_emotes: bool = True,
        show_gifs: bool = True
    ):
        new_theme = theme if theme in VALID_CHAT_THEMES else DEFAULT_CHAT_THEME
        new_orientation = orientation or "vertical"
        changed = (
            self.theme_mode != new_theme
            or self.orientation != new_orientation
            or self.show_time != show_time
            or self.show_bots != show_bots
            or self.show_badges != show_badges
            or self.show_platform != show_platform
            or self.hide_commands != hide_commands
            or self.big_emotes != big_emotes
            or self.show_gifs != show_gifs
        )
        if changed:
            self.theme_mode = new_theme
            self.orientation = new_orientation
            self.show_time = show_time
            self.show_bots = show_bots
            self.show_badges = show_badges
            self.show_platform = show_platform
            self.hide_commands = hide_commands
            self.big_emotes = big_emotes
            self.show_gifs = show_gifs
            self.setFixedHeight(105 if self.orientation == "horizontal" else 180)
            self.update()

    def paintEvent(self, _event):
        p, w, h = init_mockup_painter(self)
        canvas_rect = draw_mockup_canvas(p, w, h)

        sample_user = self.i18n.get("chat.overlay.preview_sample_user") if self.i18n else "TheAndro2K"
        sample_msg_1 = self.i18n.get("chat.overlay.preview_sample_msg_1") if self.i18n else "hola xd"
        if self.big_emotes and "🔥" not in sample_msg_1:
            sample_msg_1 = f"{sample_msg_1} 🔥"

        sample_bot_user = self.i18n.get("chat.overlay.preview_sample_bot_user") if self.i18n else "theandro2k"
        sample_bot_msg = self.i18n.get("chat.overlay.preview_sample_bot_msg") if self.i18n else "¡Qué onda @TheAndro2K! Bienvenido al stream 👾"

        sample_cmd_user = self.i18n.get("chat.overlay.preview_sample_cmd_user") if self.i18n else "Viewer42"
        sample_cmd_msg = self.i18n.get("chat.overlay.preview_sample_cmd_msg") if self.i18n else "!redes"

        msg2_data = None
        if self.show_bots:
            msg2_data = ("10:49", sample_bot_user, sample_bot_msg, COLOR_PURPLE, True, "bot", "kick")
        elif not self.hide_commands:
            msg2_data = ("10:49", sample_cmd_user, sample_cmd_msg, COLOR_CODE_LINK, False, "subscriber", "kick")

        if self.orientation == "horizontal":
            self._draw_horizontal(p, w, h, sample_user, sample_msg_1, msg2_data)
        else:
            self._draw_vertical(p, w, h, sample_user, sample_msg_1, msg2_data)

    def _get_avatar_gradient(self, user: str) -> tuple[str, str]:
        if not user:
            return self._AVATAR_GRADIENTS[0]
        code = ord(user[0].upper())
        idx = code % len(self._AVATAR_GRADIENTS)
        return self._AVATAR_GRADIENTS[idx]

    def _draw_avatar(self, p: QPainter, x: float, y: float, size: float, user: str, platform: str = ""):
        p.save()
        rect = QRectF(x, y, size, size)
        c1_hex, c2_hex = self._get_avatar_gradient(user)
        grad = QLinearGradient(x, y, x + size, y + size)
        grad.setColorAt(0.0, QColor(c1_hex))
        grad.setColorAt(1.0, QColor(c2_hex))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(rect)

        letter = user[0].upper() if user else "?"
        font = QFont("Google Sans", int(size * 0.42), QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor(COLOR_PURE_WHITE))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, letter)

        if self.show_platform and platform:
            b_size = size * 0.44
            bx = x + size - b_size + 1.0
            by = y + size - b_size + 1.0
            self._draw_badge(p, bx, by, platform, size=b_size)

        p.restore()

    def _draw_horizontal(self, p: QPainter, w: int, h: int, user: str, msg1: str, msg2_data):
        p.save()
        p.setClipRect(QRectF(8, 8, w - 16, h - 16))

        pill_h = 34.0
        pill_y = (h - pill_h) / 2.0
        start_x = 14.0

        m1_w = self._calculate_horizontal_width(user, msg1)
        self._draw_horizontal_pill(p, start_x, pill_y, m1_w, pill_h, "10:49", user, msg1, COLOR_CALLOUT_WARNING_LIGHT, badge_type="broadcaster", platform="twitch")

        if msg2_data and (start_x + m1_w + 12 < w):
            start_x2 = start_x + m1_w + 12
            t2, u2, m2, c2, _ib2, r2, plat2 = msg2_data
            m2_w = self._calculate_horizontal_width(u2, m2)
            self._draw_horizontal_pill(p, start_x2, pill_y, m2_w, pill_h, t2, u2, m2, c2, badge_type=r2, platform=plat2)

        p.restore()

    def _calculate_horizontal_width(self, user: str, msg: str) -> float:
        font_main = QFont("Google Sans", 8, QFont.Weight.Bold)
        fm = QFontMetrics(font_main)
        display_user = user + ":"
        user_w = fm.horizontalAdvance(display_user)
        msg_font = QFont("Google Sans", 9 if self.big_emotes else 8, QFont.Weight.Medium)
        fm_msg = QFontMetrics(msg_font)
        msg_w = fm_msg.horizontalAdvance(msg)

        base = 22.0 + 30.0
        if self.show_time:
            base += 44.0
        if self.show_badges:
            base += 19.0
        return base + user_w + msg_w + 10.0

    def _draw_horizontal_pill(self, p: QPainter, x: float, y: float, width: float, height: float,
                              time_str: str, user: str, msg: str, color_hex: str,
                              badge_type: str = "broadcaster", platform: str = "twitch"):
        rect = QRectF(x, y, width, height)
        color = QColor(color_hex)

        self._apply_pill_theme(p, rect, color)

        av_size = 24.0
        av_y = y + (height - av_size) / 2.0
        self._draw_avatar(p, x + 6.0, av_y, av_size, user, platform=platform)

        curr_x = x + 36.0
        if self.show_time:
            p.setFont(QFont("Google Sans", 7, QFont.Weight.Medium))
            time_col = QColor(COLOR_LIGHT_TEXT_MUTED) if self.theme_mode == "light" else get_qcolor_with_alpha(COLOR_WHITE, 140)
            p.setPen(time_col)
            time_rect = QRectF(curr_x, y, 42, height)
            p.drawText(time_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"[{time_str}]")
            curr_x += 42.0

        if self.show_badges and badge_type:
            self._draw_badge(p, curr_x, y + (height - 16) / 2, badge_type)
            curr_x += 19.0

        p.setFont(QFont("Google Sans", 8, QFont.Weight.Bold))
        display_user = user + ":"
        fm_user = QFontMetrics(p.font())
        user_w = fm_user.horizontalAdvance(display_user)
        p.setPen(color)

        user_rect = QRectF(curr_x, y, user_w, height)
        p.drawText(user_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_user)
        curr_x += user_w + 6.0

        p.setFont(QFont("Google Sans", 9 if self.big_emotes else 8, QFont.Weight.Medium))
        msg_col = QColor(COLOR_LIGHT_TEXT_PRIMARY) if self.theme_mode == "light" else QColor(COLOR_PURE_WHITE)
        p.setPen(msg_col)
        msg_rect = QRectF(curr_x, y, width - (curr_x - x) - 8, height)
        p.drawText(msg_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, msg)

    def _apply_pill_theme(self, p: QPainter, rect: QRectF, _accent_color: QColor):
        if self.theme_mode == "light":
            p.setPen(QPen(get_qcolor_with_alpha(COLOR_PURE_WHITE, 120), 1.0))
            p.setBrush(QBrush(get_qcolor_with_alpha(COLOR_PURE_WHITE, 170)))
            p.drawRoundedRect(rect, 16, 16)
        elif self.theme_mode == "minimal":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Qt.BrushStyle.NoBrush)
        else:
            p.setPen(QPen(get_qcolor_with_alpha(COLOR_PURE_WHITE, 30), 1.0))
            p.setBrush(QBrush(get_qcolor_with_alpha(COLOR_CHAT_PREVIEW_SURFACE, 195)))
            p.drawRoundedRect(rect, 16, 16)

    def _draw_vertical(self, p: QPainter, w: int, h: int, user: str, msg1: str, msg2_data):
        card_w = min(360.0, w - 28.0)
        card_h = 56.0
        card_x = (w - card_w) / 2.0
        gap = 8.0

        y1 = 12.0
        rect1 = QRectF(card_x, y1, card_w, card_h)
        self._draw_vertical_card(p, rect1, "10:49", user, msg1, COLOR_CALLOUT_WARNING_LIGHT, badge_type="broadcaster", platform="twitch")

        if msg2_data:
            y2 = y1 + card_h + gap
            if y2 + card_h <= h - 4:
                rect2 = QRectF(card_x, y2, card_w, card_h)
                t2, u2, m2, c2, _ib2, r2, plat2 = msg2_data
                self._draw_vertical_card(p, rect2, t2, u2, m2, c2, badge_type=r2, platform=plat2)

    def _draw_vertical_card(self, p: QPainter, rect: QRectF, time_str: str, user: str, msg: str,
                           color_hex: str, badge_type: str = "broadcaster", platform: str = "twitch"):
        color = QColor(color_hex)
        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()

        if self.theme_mode == "light":
            p.setPen(QPen(get_qcolor_with_alpha(COLOR_PURE_WHITE, 120), 1.0))
            p.setBrush(QBrush(get_qcolor_with_alpha(COLOR_PURE_WHITE, 170)))
            p.drawRoundedRect(rect, 14, 14)
        elif self.theme_mode == "minimal":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Qt.BrushStyle.NoBrush)
        else:
            p.setPen(QPen(get_qcolor_with_alpha(COLOR_PURE_WHITE, 28), 1.0))
            p.setBrush(QBrush(get_qcolor_with_alpha(COLOR_CHAT_PREVIEW_SURFACE, 195)))
            p.drawRoundedRect(rect, 14, 14)
        av_size = 38.0
        av_x = x + 10.0
        av_y = y + (h - av_size) / 2.0
        self._draw_avatar(p, av_x, av_y, av_size, user, platform=platform)

        content_x = av_x + av_size + 10.0
        header_y = y + 10.0
        curr_x = content_x

        if self.show_badges and badge_type:
            self._draw_badge(p, curr_x, header_y, badge_type)
            curr_x += 19.0

        p.setFont(QFont("Google Sans", 8.5, QFont.Weight.Bold))
        display_user = user
        fm_user = QFontMetrics(p.font())
        u_w = fm_user.horizontalAdvance(display_user)
        p.setPen(color)
        p.drawText(QRectF(curr_x, header_y - 2, u_w + 4, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_user)
        curr_x += u_w + 6.0

        if self.show_time:
            p.setFont(QFont("Google Sans", 7, QFont.Weight.Medium))
            time_col = QColor(COLOR_LIGHT_TEXT_MUTED) if self.theme_mode == "light" else get_qcolor_with_alpha(COLOR_WHITE, 130)
            p.setPen(time_col)
            p.drawText(QRectF(curr_x, header_y - 2, 44, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"[{time_str}]")

        msg_y = y + 30.0
        msg_w = w - (content_x - x) - 12.0

        p.setFont(QFont("Google Sans", 8.5 if self.big_emotes else 8, QFont.Weight.Medium))
        msg_col = QColor(COLOR_LIGHT_TEXT_PRIMARY) if self.theme_mode == "light" else QColor(COLOR_PURE_WHITE)
        p.setPen(msg_col)
        elided_msg = self._elide(msg, p.font(), msg_w)
        p.drawText(QRectF(content_x, msg_y, msg_w, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_msg)

    def _draw_badge(self, p: QPainter, x: float, y: float, badge_type: str, size: float = 15.5):
        rect = QRectF(x, y, size, size)
        p.save()
        p.setPen(Qt.PenStyle.NoPen)

        radius = max(2.5, size * 0.25)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, radius, radius)
        p.setClipPath(clip_path)

        config = self._BADGE_CONFIG.get(badge_type.lower())
        if config:
            glyph, col1, col2, fg_col = config
            grad = QLinearGradient(x, y, x + size, y + size)
            grad.setColorAt(0.0, QColor(col1))
            grad.setColorAt(1.0, QColor(col2))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(rect, radius, radius)

            font = QFont("GoogleSansCode Nerd Font", max(5.0, size * 0.48))
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            p.setFont(font)
            p.setPen(QColor(fg_col))

            fm = QFontMetrics(font)
            tb = fm.tightBoundingRect(glyph)
            glyph_x = rect.center().x() - tb.x() - tb.width() / 2.0
            glyph_y = rect.center().y() - tb.y() - tb.height() / 2.0
            p.drawText(QPointF(glyph_x, glyph_y), glyph)
        else:
            p.setBrush(QBrush(QColor(COLOR_CHAT_PREVIEW_BADGE)))
            p.drawRoundedRect(rect, radius, radius)

        p.restore()

    def _elide(self, text: str, font: QFont, max_w: float) -> str:
        fm = QFontMetrics(font)
        return fm.elidedText(text, Qt.TextElideMode.ElideRight, int(max_w))
