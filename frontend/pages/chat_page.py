# frontend/pages/chat_page.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
                             QTextEdit, QFrame, QLabel, QComboBox, 
                             QDoubleSpinBox, QSpinBox, QFormLayout)
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt

# Importamos los estilos y utilidades del tema
from frontend.theme import STYLES, get_switch_style

class ChatPage(QWidget):
    def __init__(self, tts_worker, db_manager):
        super().__init__()
        self.tts = tts_worker
        self.db = db_manager  # Recibimos la base de datos para guardar ajustes
        
        # Variables de estado
        self.tts_enabled = True
        self.command_mode = False
        self.trigger_command = "!tts" # Comando por defecto
        
        self.init_ui()
        self.cargar_configuraciones()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # ==========================================
        # PANEL SUPERIOR: CONFIGURACIÓN DE VOZ
        # ==========================================
        config_frame = QFrame()
        config_frame.setStyleSheet(STYLES["card"]) # Estilo de tarjeta del theme.py
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(15, 15, 15, 15)

        lbl_titulo = QLabel("Ajustes de Texto a Voz (TTS)")
        lbl_titulo.setStyleSheet(STYLES["label_title"])
        config_layout.addWidget(lbl_titulo)

        # --- FILA 1: Switches (Interruptores) ---
        switches_layout = QHBoxLayout()
        
        self.chk_tts = QCheckBox(" Habilitar Voz IA")
        self.chk_tts.setStyleSheet(get_switch_style())
        self.chk_tts.toggled.connect(self.on_tts_toggled)

        self.chk_cmd = QCheckBox(" Solo con Comando (!tts)")
        self.chk_cmd.setStyleSheet(get_switch_style())
        self.chk_cmd.toggled.connect(self.on_cmd_toggled)

        switches_layout.addWidget(self.chk_tts)
        switches_layout.addWidget(self.chk_cmd)
        switches_layout.addStretch()
        config_layout.addLayout(switches_layout)

        # --- FILA 2: Controles de Audio ---
        controls_layout = QHBoxLayout()
        
        # Selector de Voz
        voice_layout = QFormLayout()
        self.combo_voice = QComboBox()
        self.combo_voice.setStyleSheet(STYLES["combobox_modern"])
        self.combo_voice.addItems([
            "es-MX-JorgeNeural", "es-MX-DaliaNeural", 
            "es-ES-AlvaroNeural", "es-ES-ElviraNeural", 
            "es-US-AlonsoNeural", "es-AR-TomasNeural"
        ])
        self.combo_voice.currentTextChanged.connect(self.on_voice_changed)
        
        lbl_v = QLabel("Voz:")
        lbl_v.setStyleSheet(STYLES["label_text"])
        voice_layout.addRow(lbl_v, self.combo_voice)

        # Control de Volumen
        vol_layout = QFormLayout()
        self.spin_vol = QDoubleSpinBox()
        self.spin_vol.setStyleSheet(STYLES["spinbox_modern"])
        self.spin_vol.setRange(0.1, 2.0)
        self.spin_vol.setSingleStep(0.1)
        self.spin_vol.valueChanged.connect(self.on_volume_changed)
        
        lbl_vol = QLabel("Volumen:")
        lbl_vol.setStyleSheet(STYLES["label_text"])
        vol_layout.addRow(lbl_vol, self.spin_vol)

        # Control de Velocidad
        rate_layout = QFormLayout()
        self.spin_rate = QSpinBox()
        self.spin_rate.setStyleSheet(STYLES["spinbox_modern"])
        self.spin_rate.setRange(50, 300)
        self.spin_rate.setSingleStep(5)
        self.spin_rate.valueChanged.connect(self.on_rate_changed)
        
        lbl_r = QLabel("Velocidad:")
        lbl_r.setStyleSheet(STYLES["label_text"])
        rate_layout.addRow(lbl_r, self.spin_rate)

        controls_layout.addLayout(voice_layout)
        controls_layout.addLayout(vol_layout)
        controls_layout.addLayout(rate_layout)
        controls_layout.addStretch()
        
        config_layout.addLayout(controls_layout)
        main_layout.addWidget(config_frame)

        # ==========================================
        # PANEL INFERIOR: CONSOLA DE CHAT
        # ==========================================
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet(STYLES["text_edit_console"]) # Estilo de consola
        
        main_layout.addWidget(self.consola)
        self.setLayout(main_layout)

    # --- CARGA Y GUARDADO DE DATOS (SQLite) ---

    def cargar_configuraciones(self):
        """Carga los ajustes desde SQLite e inicializa la UI y el motor TTS."""
        self.chk_tts.blockSignals(True)
        self.chk_cmd.blockSignals(True)
        self.combo_voice.blockSignals(True)
        self.spin_vol.blockSignals(True)
        self.spin_rate.blockSignals(True)

        # Leer de base de datos o usar valores por defecto
        self.tts_enabled = self.db.get_config("tts_enabled", "True") == "True"
        self.command_mode = self.db.get_config("tts_cmd_mode", "False") == "True"
        voz = self.db.get_config("tts_voice", "es-MX-JorgeNeural")
        vol = float(self.db.get_config("tts_volume", 1.0))
        rate = int(self.db.get_config("tts_rate", 175))

        # Actualizar UI
        self.chk_tts.setChecked(self.tts_enabled)
        self.chk_cmd.setChecked(self.command_mode)
        self.combo_voice.setCurrentText(voz)
        self.spin_vol.setValue(vol)
        self.spin_rate.setValue(rate)

        # Aplicar al motor TTS
        self.tts.edge_voice = voz
        self.tts.volume = vol
        self.tts.rate = rate

        self.chk_tts.blockSignals(False)
        self.chk_cmd.blockSignals(False)
        self.combo_voice.blockSignals(False)
        self.spin_vol.blockSignals(False)
        self.spin_rate.blockSignals(False)

    def on_tts_toggled(self, checked):
        self.tts_enabled = checked
        self.db.set_config("tts_enabled", str(checked))
        if not checked: self.tts.immediate_stop()
        self.log(f"🎙️ [SISTEMA] TTS {'Activado' if checked else 'Desactivado'}.")

    def on_cmd_toggled(self, checked):
        self.command_mode = checked
        self.db.set_config("tts_cmd_mode", str(checked))
        self.log(f"⚙️ [SISTEMA] Modo Comando {'Activado (!tts)' if checked else 'Desactivado (Lee todo)'}.")

    def on_voice_changed(self, voice):
        self.tts.edge_voice = voice
        self.db.set_config("tts_voice", voice)

    def on_volume_changed(self, vol):
        self.tts.volume = vol
        self.db.set_config("tts_volume", str(vol))

    def on_rate_changed(self, rate):
        self.tts.rate = rate
        self.db.set_config("tts_rate", str(rate))

    # --- LÓGICA DE PROCESAMIENTO ---

    def log(self, mensaje):
        """Escribe en la consola visual de esta pestaña."""
        self.consola.append(mensaje)
        self.consola.moveCursor(QTextCursor.MoveOperation.End)

    def procesar_mensaje_tts(self, usuario, mensaje_limpio):
        """Filtra y envía el mensaje al motor de voz dependiendo de la configuración."""
        if not self.tts_enabled or not mensaje_limpio:
            return

        texto_a_leer = mensaje_limpio

        # Si el modo comando está activo, verificamos si el mensaje empieza por !tts
        if self.command_mode:
            if not texto_a_leer.lower().startswith(self.trigger_command):
                return # Ignoramos el mensaje si no tiene el comando
            
            # Removemos el "!tts " del inicio para que no lo lea en voz alta
            texto_a_leer = texto_a_leer[len(self.trigger_command):].strip()
            
            if not texto_a_leer:
                return # Si solo mandaron "!tts" sin texto, ignoramos

        self.tts.add_message(f"{usuario} dice: {texto_a_leer}")