# frontend/gui.py
import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import cargar_sesion, actualizar_configuracion, guardar_sesion
from backend.chat import iniciar_chat, detener_chat, actualizar_config_en_vivo
from backend.connection.auth import autenticar_usuario
from backend.connection.kick_api import obtener_mi_perfil, obtener_chatroom_id

# Importamos tu nuevo y genial sistema de diseño
from frontend.theme import get_sheet, STYLES, Palette
from frontend.utils import get_icon_colored

class ChatThread(QThread):
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
        self.setFixedSize(460, 680)
        # Aplicamos el QSS global desde tu theme.py
        self.setStyleSheet(get_sheet())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # ==========================================
        # TARJETA: INFO DE USUARIO
        # ==========================================
        self.user_card = QFrame()
        self.user_card.setStyleSheet(STYLES["card"])
        u_lay = QVBoxLayout(self.user_card)
        
        # Título con icono
        title_layout = QHBoxLayout()
        icon_user = QLabel()
        icon_user.setPixmap(get_icon_colored("user.svg", Palette.NeonGreen_Main, 20).pixmap(20, 20))
        self.user_lbl = QLabel(f"Canal: {self.sesion['username'] if self.sesion else 'Desconectado'}")
        self.user_lbl.setObjectName("h2")
        title_layout.addWidget(icon_user)
        title_layout.addWidget(self.user_lbl)
        title_layout.addStretch()
        
        self.status_lbl = QLabel("Estado: Esperando...")
        self.status_lbl.setObjectName("subtitle")
        
        u_lay.addLayout(title_layout)
        u_lay.addWidget(self.status_lbl)
        layout.addWidget(self.user_card)

        # ==========================================
        # TARJETA: CONFIGURACIÓN
        # ==========================================
        config_card = QFrame()
        config_card.setStyleSheet(STYLES["card"])
        c_lay = QVBoxLayout(config_card)
        
        # Cabecera Configuración
        cfg_title_layout = QHBoxLayout()
        icon_cfg = QLabel()
        icon_cfg.setPixmap(get_icon_colored("settings.svg", Palette.White_N1, 16).pixmap(16, 16))
        cfg_title = QLabel("Configuración TTS")
        cfg_title.setObjectName("h3")
        cfg_title_layout.addWidget(icon_cfg)
        cfg_title_layout.addWidget(cfg_title)
        cfg_title_layout.addStretch()
        c_lay.addLayout(cfg_title_layout)
        
        # Controles
        c_lay.addWidget(QLabel("Voz TTS:", objectName="h5"))
        self.voice_cb = QComboBox()
        self.voice_cb.setStyleSheet(STYLES["combobox_modern"])
        self.voice_cb.addItems(["es-MX-JorgeNeural", "es-MX-DaliaNeural", "es-ES-AlvaroNeural"])
        c_lay.addWidget(self.voice_cb)

        c_lay.addWidget(QLabel("Modo de lectura:", objectName="h5"))
        self.mode_cb = QComboBox()
        self.mode_cb.setStyleSheet(STYLES["combobox_modern"])
        self.mode_cb.addItems(["Automático", "Por Comando"])
        self.mode_cb.currentIndexChanged.connect(self.toggle_cmd)
        c_lay.addWidget(self.mode_cb)

        self.cmd_lbl = QLabel("Comando (ej: !s):", objectName="h5")
        self.cmd_in = QLineEdit()
        self.cmd_in.setStyleSheet(STYLES["input_cmd"])
        c_lay.addWidget(self.cmd_lbl)
        c_lay.addWidget(self.cmd_in)
        layout.addWidget(config_card)

        # ==========================================
        # CONSOLA / LOG DE MENSAJES
        # ==========================================
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(STYLES["text_edit_console"])
        self.log_view.setPlaceholderText("> Esperando mensajes del chat...")
        layout.addWidget(self.log_view)

        # ==========================================
        # BOTONES DE ACCIÓN
        # ==========================================
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton(" Guardar")
        self.btn_save.setIcon(get_icon_colored("save.svg", Palette.White_N1, 16))
        self.btn_save.setStyleSheet(STYLES["btn_outlined"])
        self.btn_save.clicked.connect(self.save_settings)
        
        self.btn_toggle = QPushButton(" CONECTAR KICK")
        self.btn_toggle.setIcon(get_icon_colored("kick.svg", Palette.NeonGreen_Main, 24))
        self.btn_toggle.setStyleSheet(STYLES["btn_primary"])
        self.btn_toggle.clicked.connect(self.toggle_connection)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_toggle)
        layout.addLayout(btn_layout)

    def toggle_cmd(self):
        visible = self.mode_cb.currentIndex() == 1
        self.cmd_lbl.setVisible(visible)
        self.cmd_in.setVisible(visible)

    def load_settings(self):
        if self.sesion:
            self.voice_cb.setCurrentText(self.sesion.get('voz_tts', 'es-MX-JorgeNeural'))
            self.mode_cb.setCurrentIndex(0 if self.sesion.get('modo_lectura', 'auto') == "auto" else 1)
            self.cmd_in.setText(self.sesion.get('comando_tts', '!s'))
        self.toggle_cmd()

    def save_settings(self):
        voz = self.voice_cb.currentText()
        modo = "auto" if self.mode_cb.currentIndex() == 0 else "comando"
        cmd = self.cmd_in.text().strip()
        
        actualizar_configuracion(voz, modo, cmd)
        if self.bot_activo:
            actualizar_config_en_vivo({"voz": voz, "modo": modo, "comando": cmd})
        
        self.status_lbl.setText("Estado: ¡Configuración guardada!")
        self.status_lbl.setStyleSheet(f"color: {Palette.NeonGreen_Main};")

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
        self.btn_toggle.setText(" DESCONECTAR")
        self.btn_toggle.setIcon(get_icon_colored("power.svg", Palette.White_N1, 24))
        self.btn_toggle.setStyleSheet(STYLES["btn_danger_outlined"])
        self.status_lbl.setText("Estado: BOT ONLINE")
        self.status_lbl.setStyleSheet(f"color: {Palette.NeonGreen_Main};")

    def stop_bot(self):
        detener_chat()
        self.bot_activo = False
        self.btn_toggle.setText(" CONECTAR KICK")
        self.btn_toggle.setIcon(get_icon_colored("kick.svg", Palette.NeonGreen_Main, 24))
        self.btn_toggle.setStyleSheet(STYLES["btn_primary"])
        self.status_lbl.setText("Estado: Desconectado")
        self.status_lbl.setStyleSheet(f"color: {Palette.Gray_N1};")

    def append_log(self, user, msg):
        self.log_view.append(f"<span style='color:{Palette.NeonGreen_Main}; font-weight:bold;'>{user}</span><span style='color:{Palette.White_N1};'>: {msg}</span>")