# frontend/views/chat_view.py

from PySide6.QtWidgets import (QComboBox, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QLabel, QSlider, QFrame)
from PySide6.QtCore import Qt, Signal, Slot

from frontend.components.switch import ModernSwitch

class ChatView(QWidget):
    # ─── CONTRATOS DE SALIDA (Para el Controlador) ───
    volume_changed = Signal(int)
    voice_changed = Signal(str)
    provider_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Chat en Vivo")
        title.setProperty("role", "title")
        layout.addWidget(title)
        
        controls_frame = QFrame()
        controls_frame.setObjectName("Card")
        controls_layout = QVBoxLayout(controls_frame) 
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setSpacing(12)
        
        # --- Fila 1: Configuración de Lectura y Motor ---
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        
        row1.addWidget(QLabel("Activar TTS:"))
        self.chk_tts = ModernSwitch()
        self.chk_tts.setChecked(True)
        row1.addWidget(self.chk_tts)
        
        row1.addSpacing(20)
        
        row1.addWidget(QLabel("Leer Nombre:"))
        self.chk_name = ModernSwitch() 
        self.chk_name.setChecked(True)
        row1.addWidget(self.chk_name)

        row1.addSpacing(20)

        self.lbl_provider_state = QLabel("Motor: Local")
        self.lbl_provider_state.setStyleSheet("font-weight: bold;")
        row1.addWidget(self.lbl_provider_state)
        
        self.chk_provider = ModernSwitch()
        self.chk_provider.setChecked(False)
        self.chk_provider.toggled.connect(self._on_provider_toggled)
        row1.addWidget(self.chk_provider)
        
        row1.addStretch() 
        
        # --- Selector de Voz ---
        row1.addWidget(QLabel("Voz:"))
        self.combo_voice = QComboBox()
        self.combo_voice.setFixedWidth(300)
        self.combo_voice.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        row1.addWidget(self.combo_voice)
        
        # --- Fila 2: Filtros y Volumen ---
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        
        # Usar Comando
        row2.addWidget(QLabel("Usar Comando:"))
        self.chk_command = ModernSwitch() 
        self.chk_command.setChecked(False)
        row2.addWidget(self.chk_command)
        
        # El QLineEdit se queda pegado al switch del comando
        self.txt_command = QLineEdit("!tts")
        self.txt_command.setFixedWidth(70)
        self.txt_command.textChanged.connect(self._validate_command)
        row2.addWidget(self.txt_command)
        
        row2.addStretch() 
        
        # Volumen
        row2.addWidget(QLabel("Volumen:"))
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.slider_vol.setFixedWidth(300)
        self.slider_vol.valueChanged.connect(self.volume_changed.emit)
        row2.addWidget(self.slider_vol)
        
        # Ensamblaje del Card
        controls_layout.addLayout(row1)
        controls_layout.addLayout(row2)
        layout.addWidget(controls_frame)

        # --- Display del Chat ---
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("ChatContainer")
        layout.addWidget(self.chat_display)

    def _validate_command(self, text):
        """Asegura que el comando siempre empiece con !"""
        if not text.startswith("!"):
            self.txt_command.setText("!" + text.replace("!", ""))

    def _on_provider_toggled(self, is_web: bool):
        """Maneja el cambio visual y emite la señal al controlador"""
        provider = "web" if is_web else "local"
        self.lbl_provider_state.setText("Motor: Web IA" if is_web else "Motor: Local")
        
        # Damos un feedback visual inmediato mientras el controlador trae las nuevas voces
        self.combo_voice.blockSignals(True)
        self.combo_voice.clear()
        self.combo_voice.addItem("Cargando voces...", userData=None)
        self.combo_voice.blockSignals(False)
        
        # Delegamos la carga real de voces al controlador
        self.provider_changed.emit(provider)

    # ─── CONTRATOS DE ESTADO (Para el Controlador) ───
    def get_tts_settings(self) -> dict:
        """Única fuente de verdad para la configuración actual (Alta Cohesión)"""
        return {
            "enabled": self.chk_tts.isChecked(),
            "read_name": self.chk_name.isChecked(),
            "use_command": self.chk_command.isChecked(),
            "command": self.txt_command.text().strip().lower(),
            "provider": "web" if self.chk_provider.isChecked() else "local" # Añadido
        }

    @Slot(str, str)
    def append_message(self, user: str, message: str):
        """Agrega un nuevo mensaje con el nombre en verde en la UI"""
        html_msg = f'<b style="color: #0ca678;">{user}:</b> <span style="color: #f0f0f0;">{message}</span>'
        self.chat_display.append(html_msg)

    def populate_voices(self, voices: list[dict], selected_id: str = None):
        """Carga las voces sin romper la capa de presentación (SoR)"""
        self.combo_voice.blockSignals(True) 
        self.combo_voice.clear()
        
        for index, voice in enumerate(voices):
            self.combo_voice.addItem(voice["name"], userData=voice["id"])
            if voice["id"] == selected_id:
                self.combo_voice.setCurrentIndex(index)
                
        self.combo_voice.blockSignals(False)
        if not selected_id and self.combo_voice.count() > 0:
            self._on_voice_selected(0)

    def _on_voice_selected(self, index: int):
        voice_id = self.combo_voice.itemData(index)
        if voice_id:
            self.voice_changed.emit(voice_id)