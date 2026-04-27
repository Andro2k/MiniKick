# frontend/views/dashboard_view.py
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QCheckBox, QFrame, QPushButton
)

from frontend.theme import SPACING, COLOR_ACCENT
from frontend.widgets.components import StatCard, ChatMessage
from frontend.widgets.sidebar import Sidebar # <--- NUEVA IMPORTACIÓN

class DashboardView(QWidget):
    
    new_chat_message = Signal(str, str)
    request_login = Signal()

    def __init__(self, tts_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("TransparentWidget") 
        
        self.username = None
        self.chatroom_id = None
        self.tts = tts_manager
        self.msg_count = 0
        self.tts_enabled = True

        self._build_ui()
        self.new_chat_message.connect(self._add_message_to_ui)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── SIDEBAR ───
        # ¡Mira lo limpio que queda esto ahora!
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        # ─── MAIN CONTENT ───
        main_content = QWidget()
        main_content.setObjectName("TransparentWidget")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(SPACING, SPACING, SPACING, SPACING)
        main_layout.setSpacing(SPACING)

        # ─── HEADER ───
        header_layout = QHBoxLayout()
        self.title_lbl = QLabel("Panel de Control - Desconectado")
        self.title_lbl.setProperty("role", "title")
        
        self.cb_tts = QCheckBox("Activar TTS")
        self.cb_tts.setChecked(True)
        self.cb_tts.stateChanged.connect(self._toggle_tts)
        
        self.btn_connect = QPushButton("Conectar con Kick")
        self.btn_connect.setProperty("accent", True)
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.cb_tts)
        header_layout.addSpacing(SPACING * 2)
        header_layout.addWidget(self.btn_connect)
        main_layout.addLayout(header_layout)

        # ─── STATS ROW ───
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(SPACING * 2)
        
        self.stat_viewers = StatCard("Espectadores", "—", "eye.svg")
        self.stat_followers = StatCard("Seguidores", "—", "heart.svg")
        self.stat_messages = StatCard("Mensajes Hoy", "0", "mail.svg")
        
        stats_layout.addWidget(self.stat_viewers)
        stats_layout.addWidget(self.stat_followers)
        stats_layout.addWidget(self.stat_messages)
        main_layout.addLayout(stats_layout)

        # ─── CHAT AREA ───
        chat_container = QFrame()
        chat_container.setObjectName("ChatContainer")
        chat_layout = QVBoxLayout(chat_container)
        
        chat_title = QLabel("Chat en Vivo")
        chat_title.setProperty("role", "title")
        chat_title.setStyleSheet("font-size: 16px;") 
        chat_layout.addWidget(chat_title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.chat_content = QWidget()
        self.chat_content.setObjectName("TransparentWidget")
        self.chat_content_layout = QVBoxLayout(self.chat_content)
        self.chat_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_content_layout.setSpacing(2)
        self.chat_content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.chat_content)
        chat_layout.addWidget(self.scroll_area)
        
        main_layout.addWidget(chat_container, stretch=1)
        root.addWidget(main_content, stretch=1)

    # ─── LÓGICA DE LA UI ───
    def _on_connect_clicked(self):
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Autenticando...")
        self.request_login.emit() # Llama a main.py

    def set_connected_state(self, username: str, chatroom_id: int):
        """Actualiza la interfaz cuando el login es exitoso"""
        self.username = username
        self.chatroom_id = chatroom_id
        
        self.title_lbl.setText(f"Panel de Control - {self.username}")
        
        self.btn_connect.setText("Conectado")
        self.btn_connect.setStyleSheet(f"background: {COLOR_ACCENT}; color: #0b0e11;")
        self.btn_connect.setEnabled(False)

    def set_error_state(self, error_msg: str):
        """Si falla el login, restauramos el botón"""
        self.btn_connect.setText("Reintentar")
        self.btn_connect.setEnabled(True)
        print(f"[-] Error UI: {error_msg}")

    def _toggle_tts(self, state):
        self.tts_enabled = bool(state)

    def trigger_new_message(self, username: str, text: str):
        self.new_chat_message.emit(username, text)

    def _add_message_to_ui(self, username: str, text: str):
        # Evita error si llega un mensaje antes de que la API nos devuelva el nombre
        if not self.username: return 
        
        is_streamer = (username.lower() == self.username.lower())
        msg_widget = ChatMessage(username, text, is_highlighted=is_streamer)
        self.chat_content_layout.addWidget(msg_widget)
        
        self.msg_count += 1
        self.stat_messages.set_value(str(self.msg_count))
        
        if self.tts_enabled:
            self.tts.say(f"{username} dice: {text}")

        QTimer.singleShot(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())