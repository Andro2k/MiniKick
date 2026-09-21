# frontend\components\chat\chat_display.py

import html
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QTextEdit, QSizePolicy
from frontend.widgets import ModernCard
from frontend.common import COLOR_NEUTRAL_200, MARGIN_SM, SPACING_SM

class ChatConsoleEdit(QTextEdit):
    def createMimeDataFromSelection(self):
        mime = super().createMimeDataFromSelection()
        if mime and mime.hasText():
            clean_text = mime.text().replace("\ue0b6", "").replace("\ue0b4", "")
            mime.setText(clean_text)
        return mime

class ChatDisplayPanel(ModernCard):
    _MAX_CHAT_BLOCKS = 400
    _PILL_BG = "#29315A"
    _CAP_LEFT = "\ue0b6"
    _CAP_RIGHT = "\ue0b4"
    _FONT_FMT = "font-family: 'GoogleSansCode Nerd Font', 'GoogleSansCode NF', 'Google Sans Code Nerd Font', 'Hack Nerd Font', monospace;"

    _ROLE_SYMBOLS = {
        "Streamer": ("\uf130", "#E64747"),
        "Broadcaster": ("\uf130", "#E64747"),
        "Moderador": ("\ued25", "#3EC669"),
        "Moderator": ("\ued25", "#3EC669"),
        "VIP": ("\uedeb", "#E4F34A"),
        "Suscriptor": ("\udb83\ude44", "#9B6BDF"),
        "Subscriber": ("\udb83\ude44", "#9B6BDF"),
        "Miembro": ("\udb83\ude44", "#43CCEA"),
        "Member": ("\udb83\ude44", "#43CCEA"),
        "Verified": ("\uf00c", "#AEA4BF"),
        "Bot": ("\uee0d", "#43CCEA"),
        "Sistema": ("\uf113", "#3EC669"),
        "System": ("\uf113", "#3EC669"),
        "Usuario": ("\ued35", "#AEA4BF"),
        "User": ("\ued35", "#AEA4BF")
    }

    _PLATFORM_ICONS = {
        "twitch": ("\uf1e8", "#9146FF", "Twitch"),
        "kick": ("\uf2f3", "#53FC18", "Kick"),
        "youtube": ("\uf16a", "#FF0000", "YouTube"),
        "tiktok": ("\udb80\udf8c", "#00F2FE", "TikTok")
    }

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=MARGIN_SM, spacing=SPACING_SM, orientation="vertical")
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumWidth(380)
        self.setMinimumHeight(400) 
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        lbl_chat_title = QLabel(self.i18n.get("chat.display.title"))
        lbl_chat_title.setProperty("role", "h3")
        
        self.chat_display = ChatConsoleEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setProperty("role", "ConsoleDisplay")
        chat_font = QFont("GoogleSansCode Nerd Font", 10)
        chat_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.chat_display.setFont(chat_font)
        self.chat_display.document().setDocumentMargin(2)

        self.addWidget(lbl_chat_title)
        self.addWidget(self.chat_display)

    @classmethod
    def _create_pill(cls, content_html: str, text_color: str = "#AEA4BF", pill_bg: str = _PILL_BG) -> str:
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
        safe_color = color if (color and color.startswith("#") and len(color) <= 7) else COLOR_NEUTRAL_200
        
        pills = []
        plat_icon, plat_color, _ = self._PLATFORM_ICONS.get(
            platform.lower() if platform else "kick", ("\uf2f3", "#53FC18", "Kick")
        )
        plat_span = f'<span style="color: {plat_color};">{plat_icon}</span>'

        if timestamp:
            time_plat_content = f"{plat_span} {timestamp}"
        else:
            time_plat_content = plat_span

        pills.append(self._create_pill(time_plat_content, text_color="#AEA4BF"))

        if role:
            symbol, role_color = self._ROLE_SYMBOLS.get(role, ("\ued35", "#AEA4BF"))
            role_content = f'<span style="color: {role_color};">{symbol}</span> {role}'
            pills.append(self._create_pill(role_content, text_color="#E4E5E9"))

        pills.append(self._create_pill(safe_user, text_color=safe_color))

        header_html = " ".join(pills)
        html_msg = f'<div style="margin: 2px 0px;">{header_html}  <span style="color: {COLOR_NEUTRAL_200};">{safe_message}</span></div>'
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
