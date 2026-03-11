# frontend/pages/rewards_page.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt

class RewardsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Información para OBS
        info_obs = QLabel("URL para OBS (Fuente de Navegador): <b style='color:#53fc18;'>http://127.0.0.1:8081</b> (Ancho 1920, Alto 1080)")
        info_obs.setTextFormat(Qt.TextFormat.RichText)
        info_obs.setStyleSheet("background-color: #121516; padding: 10px; border: 1px solid #333; border-radius: 4px; margin-bottom: 5px;")
        info_obs.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # Consola de Canjes
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("background-color: #121516; color: #00e5ff; font-family: Consolas; font-size: 13px; border: none;")

        layout.addWidget(info_obs)
        layout.addWidget(self.consola)
        self.setLayout(layout)

    def log(self, mensaje):
        """Escribe en la consola visual de esta pestaña."""
        self.consola.append(mensaje)
        self.consola.moveCursor(QTextCursor.MoveOperation.End)