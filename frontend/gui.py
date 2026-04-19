# frontend/gui.py
import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import cargar_sesion, actualizar_configuracion, guardar_sesion
from backend.chat import iniciar_chat, detener_chat, actualizar_config_en_vivo
from backend.connection.auth import autenticar_usuario
from backend.connection.kick_api import obtener_mi_perfil, obtener_chatroom_id

class ChatThread(QThread):
    # Señal para enviar el mensaje a la ventana principal
    new_msg_sig = pyqtSignal(str, str)

    def __init__(self, chatroom_id, config):
        super().__init__()
        self.chatroom_id = chatroom_id
        self.config = config

    def run(self):
        iniciar_chat(
            self.chatroom_id, 
            self.config, 
            callback_gui=lambda u, m: self.new_msg_sig.emit(u, m)
        )

class MiniKickGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.sesion = cargar_sesion()
        self.bot_activo = False
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("MiniKick Dashboard")
        self.setFixedSize(450, 650)
        layout = QVBoxLayout(self)

        # Info de Usuario
        self.user_card = QFrame()
        self.user_card.setObjectName("card")
        u_lay = QVBoxLayout(self.user_card)
        self.user_lbl = QLabel(f"Canal: {self.sesion['username'] if self.sesion else 'Desconectado'}")
        self.user_lbl.setObjectName("title")
        self.status_lbl = QLabel("Estado: Esperando...")
        u_lay.addWidget(self.user_lbl)
        u_lay.addWidget(self.status_lbl)
        layout.addWidget(self.user_card)

        # Configuración
        config_card = QFrame()
        config_card.setObjectName("card")
        c_lay = QVBoxLayout(config_card)
        
        self.voice_cb = QComboBox()
        self.voice_cb.addItems(["es-MX-JorgeNeural", "es-MX-DaliaNeural", "es-ES-AlvaroNeural"])
        c_lay.addWidget(QLabel("Voz TTS:"))
        c_lay.addWidget(self.voice_cb)

        self.mode_cb = QComboBox()
        self.mode_cb.addItems(["Automático", "Por Comando"])
        # Conectamos el cambio de opción para ocultar/mostrar el input del comando
        self.mode_cb.currentIndexChanged.connect(self.toggle_command_field)
        c_lay.addWidget(QLabel("Modo de lectura:"))
        c_lay.addWidget(self.mode_cb)

        self.cmd_lbl = QLabel("Comando (ej: !s):")
        self.cmd_in = QLineEdit()
        c_lay.addWidget(self.cmd_lbl)
        c_lay.addWidget(self.cmd_in)
        layout.addWidget(config_card)

        # Log de Mensajes
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        # BOTONES
        self.btn_save = QPushButton("GUARDAR CONFIGURACIÓN")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_settings)
        
        self.btn_toggle = QPushButton("CONECTAR CON KICK")
        self.btn_toggle.setObjectName("primary")
        self.btn_toggle.clicked.connect(self.toggle_connection)
        
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_toggle)

    def toggle_command_field(self):
        """Oculta o muestra el campo de comando dependiendo del modo elegido."""
        is_cmd = self.mode_cb.currentIndex() == 1
        self.cmd_lbl.setVisible(is_cmd)
        self.cmd_in.setVisible(is_cmd)

    def load_settings(self):
        if self.sesion:
            self.voice_cb.setCurrentText(self.sesion.get('voz_tts', 'es-MX-JorgeNeural'))
            self.mode_cb.setCurrentIndex(0 if self.sesion.get('modo_lectura', 'auto') == "auto" else 1)
            self.cmd_in.setText(self.sesion.get('comando_tts', '!s'))
        self.toggle_command_field() # Asegurar que inicie oculto si está en automático

    def save_settings(self):
        """Guarda en DB y actualiza el bot si está corriendo."""
        voz = self.voice_cb.currentText()
        # Línea corregida:
        modo = "auto" if self.mode_cb.currentIndex() == 0 else "comando"
        cmd = self.cmd_in.text().strip()
        
        actualizar_configuracion(voz, modo, cmd)
        
        if self.bot_activo:
            actualizar_config_en_vivo({"voz": voz, "modo": modo, "comando": cmd})
        
        self.status_lbl.setText("Estado: ¡Configuración guardada!")

    def toggle_connection(self):
        if not self.bot_activo:
            if not self.sesion:
                if not self.login_flow(): return
            self.start_bot()
        else:
            self.stop_bot()

    def login_flow(self):
        tokens = autenticar_usuario()
        if tokens:
            user = obtener_mi_perfil(tokens['access_token'])
            cid = obtener_chatroom_id(user)
            guardar_sesion(tokens['access_token'], tokens['refresh_token'], user, cid)
            self.sesion = cargar_sesion()
            self.user_lbl.setText(f"Canal: {user}")
            return True
        return False

    def start_bot(self):
        config = {
            "voz": self.voice_cb.currentText(),
            "modo": "auto" if self.mode_cb.currentIndex() == 0 else "comando",
            "comando": self.cmd_in.text()
        }
        self.thread = ChatThread(self.sesion['chatroom_id'], config)
        self.thread.new_msg_sig.connect(self.append_log)
        self.thread.start()
        
        self.bot_activo = True
        self.btn_toggle.setText("DESCONECTAR")
        self.btn_toggle.setStyleSheet("background-color: #ff4d4d; color: white;")
        self.status_lbl.setText("Estado: BOT ONLINE")

    def stop_bot(self):
        detener_chat()
        self.bot_activo = False
        self.btn_toggle.setText("CONECTAR CON KICK")
        self.btn_toggle.setStyleSheet("")
        self.status_lbl.setText("Estado: Desconectado")

    def append_log(self, user, msg):
        self.log_view.append(f"<b>{user}:</b> {msg}")