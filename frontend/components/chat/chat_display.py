# frontend\components\chat\chat_display.py

import html
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QTextEdit, QSizePolicy
from frontend.widgets import ModernCard
from frontend.common.theme import COLOR_NEUTRAL_200

class ChatDisplayPanel(ModernCard):
    _MAX_CHAT_BLOCKS = 400

    def __init__(self, i18n, parent=None):
        super().__init__(parent, margin=8, spacing=6, orientation="vertical")
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumWidth(380)
        self.setMinimumHeight(400) 
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        lbl_chat_title = QLabel(self.i18n.get("chat.display.title"))
        lbl_chat_title.setProperty("role", "h3")
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setProperty("role", "ConsoleDisplay")
        chat_font = QFont("Google Sans Code Nerd Font", 10)
        chat_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.chat_display.setFont(chat_font)

        self.addWidget(lbl_chat_title)
        self.addWidget(self.chat_display)

    _ROLE_SYMBOLS = {
        "Streamer": ("\uf130", "#dc2626", "#ffffff"),
        "Broadcaster": ("\uf130", "#dc2626", "#ffffff"),
        "Moderador": ("\udb82\udc8f", "#16a34a", "#ffffff"),
        "Moderator": ("\udb82\udc8f", "#16a34a", "#ffffff"),
        "VIP": ("\udb80\uddc8", "#ca8a04", "#ffffff"),
        "Suscriptor": ("\uedeb", "#9333ea", "#ffffff"),
        "Subscriber": ("\uedeb", "#9333ea", "#ffffff"),
        "Bot": ("\udb81\udea9", "#2563eb", "#ffffff"),
        "Sistema": ("\ue615", "#059669", "#ffffff"),
        "System": ("\ue615", "#059669", "#ffffff"),
        "Usuario": ("\ued35", "#374151", "#e2e8f0"),
        "User": ("\ued35", "#374151", "#e2e8f0")
    }

    _PLATFORM_ICONS = {
        "twitch": ("\uf1e8", "#9146FF", "#ffffff", "Twitch"),
        "kick": ("\uf2f3", "#53FC18", "#000000", "Kick")
    }

    def append_message(self, user: str, message: str, color: str, timestamp: str = "", is_html: bool = False, role: str = "", platform: str = "kick"):
        safe_user = html.escape(user)
        safe_message = message if is_html else html.escape(message)        
        safe_color = color if (color and color.startswith("#") and len(color) <= 7) else COLOR_NEUTRAL_200
        
        segments = []
        
        if timestamp:
            segments.append(("#1e293b", "#94a3b8", f"&nbsp;{timestamp}&nbsp;"))
            
        plat_icon, plat_bg, plat_fg, plat_name = self._PLATFORM_ICONS.get(
            platform.lower() if platform else "kick", ("\uf2f3", "#53FC18", "#000000", "Kick")
        )
        segments.append((plat_bg, plat_fg, f"&nbsp;{plat_icon}&nbsp;"))
        
        if role:
            symbol, role_bg, role_fg = self._ROLE_SYMBOLS.get(role, ("\ued35", "#374151", "#e2e8f0"))
            segments.append((role_bg, role_fg, f"&nbsp;{symbol}&nbsp;&nbsp;{role}&nbsp;"))
            
        segments.append(("#262626", safe_color, f"&nbsp;{safe_user}&nbsp;"))

        font_fmt = "font-family: 'Google Sans Code Nerd Font', 'Hack Nerd Font', monospace;"
        html_parts = []
        for i, (bg, fg, text) in enumerate(segments):
            if i == 0:
                html_parts.append(f'<span style="{font_fmt} color: {bg};">\ue0b2</span>')
            else:
                prev_bg = segments[i-1][0]
                html_parts.append(f'<span style="{font_fmt} color: {prev_bg}; background-color: {bg};">\ue0b0</span>')
            
            html_parts.append(f'<span style="{font_fmt} background-color: {bg}; color: {fg};">{text}</span>')
        
        last_bg = segments[-1][0]
        html_parts.append(f'<span style="{font_fmt} color: {last_bg};">\ue0b0</span>')

        header_html = "".join(html_parts)
        html_msg = f'{header_html} <span style="color: {COLOR_NEUTRAL_200};">{safe_message}</span>'
        self.chat_display.append(html_msg)
        self._trim_chat_history()

    def _trim_chat_history(self):
        doc = self.chat_display.document()
        excess = doc.blockCount() - self._MAX_CHAT_BLOCKS
        if excess <= 0:
            return
        cursor = self.chat_display.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(excess):
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        cursor.endEditBlock()
