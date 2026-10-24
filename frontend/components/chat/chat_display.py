# frontend\components\chat\chat_display.py

import html
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QTextEdit, QSizePolicy, QPushButton, QHBoxLayout
from frontend.widgets import ModernCard
from frontend.common import Palette, BrandColors, BadgeTheme, Size

class ChatConsoleEdit(QTextEdit):
    def createMimeDataFromSelection(self):
        mime = super().createMimeDataFromSelection()
        if mime and mime.hasText():
            clean_text = mime.text().replace("\ue0b6", "").replace("\ue0b4", "")
            mime.setText(clean_text)
        return mime

class ChatDisplayPanel(ModernCard):
    detach_requested = Signal()
    reattach_requested = Signal()
    _MAX_CHAT_BLOCKS = 400
    _PILL_BG = BadgeTheme.BADGE_BCG
    _CAP_LEFT = "\ue0b6"
    _CAP_RIGHT = "\ue0b4"
    _FONT_FMT = "font-family: 'GoogleSansCode Nerd Font', 'GoogleSansCode NF', 'Google Sans Code Nerd Font', 'Hack Nerd Font', monospace;"

    _ROLE_SYMBOLS = {
        "Streamer": ("\uf130", BadgeTheme.BADGE_STR),
        "Broadcaster": ("\uf130", BadgeTheme.BADGE_STR),
        "Moderador": ("\ued25", BadgeTheme.BADGE_MOD),
        "Moderator": ("\ued25", BadgeTheme.BADGE_MOD),
        "VIP": ("\uedeb", BadgeTheme.BADGE_VIP),
        "Suscriptor": ("\udb83\ude44", BadgeTheme.BADGE_SUB),
        "Subscriber": ("\udb83\ude44", BadgeTheme.BADGE_SUB),
        "Miembro": ("\udb83\ude44", BadgeTheme.BADGE_SUB),
        "Member": ("\udb83\ude44", BadgeTheme.BADGE_SUB),
        "Verified": ("\uf00c", Palette.NEUTRAL_400),
        "Bot": ("\uee0d", BrandColors.BLUE),
        "Sistema": ("\uf113", BadgeTheme.BADGE_MOD),
        "System": ("\uf113", BadgeTheme.BADGE_MOD),
        "Usuario": ("\ued35", Palette.NEUTRAL_400),
        "User": ("\ued35", Palette.NEUTRAL_400)
    }

    _PLATFORM_ICONS = {
        "twitch": ("\uf1e8", BrandColors.TWITCH, "Twitch"),
        "kick": ("\uf2f3", BrandColors.KICK, "Kick"),
        "youtube": ("\uf16a", BrandColors.YOUTUBE, "YouTube"),
        "tiktok": ("\udb80\udf8c", BrandColors.TIKTOK, "TikTok")
    }

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=Size.Margin.MRG_XSM, spacing=Size.SPACING_SM, orientation="vertical")
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumWidth(280)
        self.setMinimumHeight(400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        header_layout = QHBoxLayout()
        lbl_chat_title = QLabel(self.i18n.get("chat.display.title"))
        lbl_chat_title.setProperty("role", "h3")

        self.btn_detach = QPushButton(self.i18n.get("chat.display.detach"))
        self.btn_detach.setProperty("role", "action_outlined")
        self.btn_detach.clicked.connect(self.detach_requested.emit)

        self.btn_reattach = QPushButton(self.i18n.get("chat.display.reattach"))
        self.btn_reattach.setProperty("role", "action_outlined")
        self.btn_reattach.hide()
        self.btn_reattach.clicked.connect(self.reattach_requested.emit)

        header_layout.addWidget(lbl_chat_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.btn_detach)
        header_layout.addWidget(self.btn_reattach)

        self.chat_display = ChatConsoleEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setProperty("role", "ConsoleDisplay")
        chat_font = QFont("GoogleSansCode Nerd Font", 10)
        chat_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.chat_display.setFont(chat_font)
        self.chat_display.document().setDocumentMargin(2)

        self.addLayout(header_layout)
        self.addWidget(self.chat_display)

    def set_detached(self, detached: bool) -> None:
        self.btn_detach.setVisible(not detached)
        self.btn_reattach.setVisible(detached)

    @classmethod
    def _create_pill(cls, content_html: str, text_color: str = Palette.NEUTRAL_400, pill_bg: str = _PILL_BG) -> str:
        return (
            f'<span style="{cls._FONT_FMT}">'
            f'<span style="color: {pill_bg};">{cls._CAP_LEFT}</span>'
            f'<span style="background-color: {pill_bg}; color: {text_color};">{content_html}</span>'
            f'<span style="color: {pill_bg};">{cls._CAP_RIGHT}</span>'
            f'</span>'
        )

    def append_message(self, user: str, message: str, color: str, timestamp: str = "", is_html: bool = False, role: str = "", platform: str = "kick"):
        safe_user = html.escape(user)
        safe_message = message if is_html else html.escape(message)
        safe_color = color if (color and color.startswith("#") and len(color) <= 7) else Palette.NEUTRAL_200

        pills = []
        plat_icon, plat_color, _ = self._PLATFORM_ICONS.get(
            platform.lower() if platform else "kick", ("\uf2f3", BrandColors.KICK, "Kick")
        )
        plat_span = f'<span style="color: {plat_color};">{plat_icon}</span>'

        if timestamp:
            time_plat_content = f"{plat_span} {timestamp}"
        else:
            time_plat_content = plat_span

        pills.append(self._create_pill(time_plat_content, text_color=Palette.NEUTRAL_400))

        if role:
            symbol, role_color = self._ROLE_SYMBOLS.get(role, ("\ued35", Palette.NEUTRAL_400))
            role_content = f'<span style="color: {role_color};">{symbol}</span> {role}'
            pills.append(self._create_pill(role_content, text_color=Palette.NEUTRAL_200))

        pills.append(self._create_pill(safe_user, text_color=safe_color))

        header_html = " ".join(pills)
        html_msg = f'<div style="margin: 2px 0px;">{header_html}  <span style="color: {Palette.NEUTRAL_200};">{safe_message}</span></div>'
        self.chat_display.append(html_msg)
        self._trim_chat_history()

    def _trim_chat_history(self):
        doc = self.chat_display.document()
        excess = doc.blockCount() - self._MAX_CHAT_BLOCKS
        if excess <= 20:
            return
        cursor = self.chat_display.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(excess):
            cursor.movePosition(cursor.MoveOperation.NextBlock, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deleteChar()
        cursor.endEditBlock()
