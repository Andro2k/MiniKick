# frontend\components\chat\chat_display.py

import html
from PySide6.QtWidgets import QLabel, QTextEdit, QSizePolicy
from frontend.widgets import ModernCard
from frontend.common.theme import COLOR_NEUTRAL_200, COLOR_NEUTRAL_500

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

        self.addWidget(lbl_chat_title)
        self.addWidget(self.chat_display)

    _ROLE_SYMBOLS = {
        "Streamer": ("\uf130", "#ef4444"),
        "Broadcaster": ("\uf130", "#ef4444"),
        "Moderador": ("\udb82\udc8f", "#22c55e"),
        "Moderator": ("\udb82\udc8f", "#22c55e"),
        "VIP": ("\udb80\uddc8", "#eab308"),
        "Suscriptor": ("\uedeb", "#a855f7"),
        "Subscriber": ("\uedeb", "#a855f7"),
        "Bot": ("\udb81\udea9", "#3b82f6"),
        "Sistema": ("\ue615", "#00e701"),
        "System": ("\ue615", "#00e701"),
        "Usuario": ("\ued35", "#9ca3af"),
        "User": ("\ued35", "#9ca3af")
    }

    _PLATFORM_ICONS = {
        "twitch": ("\uf1e8", "#9146FF", "Twitch"),
        "kick": ("\uf2f3", "#53FC18", "Kick")
    }

    def append_message(self, user: str, message: str, color: str, timestamp: str = "", is_html: bool = False, role: str = "", platform: str = "kick"):
        safe_user = html.escape(user)
        safe_message = message if is_html else html.escape(message)        
        safe_color = color if (color and color.startswith("#") and len(color) <= 7) else COLOR_NEUTRAL_200
        
        ts_span = f'<span style="color: {COLOR_NEUTRAL_500}; font-size: 0.85em;">[{timestamp}]</span>&nbsp;&nbsp;' if timestamp else ""
        
        plat_icon, plat_color, plat_name = self._PLATFORM_ICONS.get(platform.lower() if platform else "kick", ("\uf2f3", "#53FC18", "Kick"))
        plat_span = f'<span style="color: {plat_color};" title="{plat_name}">{plat_icon}</span>&nbsp;&nbsp;'
        
        symbol, role_color = self._ROLE_SYMBOLS.get(role, ("\ued35", "#9ca3af"))
        role_span = f'<span style="color: {role_color};" title="{role}">{symbol}</span>&nbsp;&nbsp;' if role else ""

        html_msg = f'{ts_span}{plat_span}{role_span}<b style="color: {safe_color};">{safe_user}:</b> <span style="color: {COLOR_NEUTRAL_200};">{safe_message}</span>'
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
