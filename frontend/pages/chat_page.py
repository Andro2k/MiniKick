# frontend/pages/chat_page.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QTextEdit
from PyQt6.QtGui import QTextCursor

class ChatPage(QWidget):
    def __init__(self, tts_worker):
        super().__init__()
        self.tts = tts_worker  # Recibe el motor de voz desde el main
        self.tts_enabled = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Checkbox para el TTS
        self.chk_tts = QCheckBox("Habilitar Lectura de Chat (Voz IA)")
        self.chk_tts.setChecked(True)
        self.chk_tts.setStyleSheet("color: #53fc18; font-weight: bold; margin-bottom: 5px;")
        self.chk_tts.toggled.connect(self.toggle_tts)

        # Consola de Chat
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("background-color: #121516; color: #ffffff; font-family: Consolas; font-size: 13px; border: none;")
        
        layout.addWidget(self.chk_tts)
        layout.addWidget(self.consola)
        self.setLayout(layout)

    def toggle_tts(self, checked):
        self.tts_enabled = checked
        if not checked and self.tts:
            self.tts.immediate_stop()
        self.log(f"🎙️ [SISTEMA] TTS {'Activado' if checked else 'Desactivado'}.")

    def log(self, mensaje):
        """Escribe en la consola visual de esta pestaña."""
        self.consola.append(mensaje)
        self.consola.moveCursor(QTextCursor.MoveOperation.End)

    def procesar_mensaje_tts(self, usuario, mensaje_limpio):
        """Envía el mensaje al motor de voz si está habilitado."""
        if self.tts_enabled and mensaje_limpio:
            self.tts.add_message(f"{usuario} dice: {mensaje_limpio}")

            