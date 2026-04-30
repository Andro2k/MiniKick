# frontend/views/chat_view.py

from PySide6.QtWidgets import (QComboBox, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QLabel, QSlider, QFrame)
from PySide6.QtCore import Qt, Signal, Slot

from frontend.components.switch import ModernSwitch

class ChatView(QWidget):
    # ─── CONTRATOS DE SALIDA ───
    volume_changed = Signal(int)
    voice_changed = Signal(str) # NUEVA SEÑAL para orquestar

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Chat en Vivo")
        title.setProperty("role", "title")
        layout.addWidget(title)
        
        controls_frame = QFrame()
        controls_frame.setObjectName("Card")
        controls_layout = QVBoxLayout(controls_frame) 
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setSpacing(12)
        
        # --- Fila 1: Configuración de Lectura ---
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        
        row1.addWidget(QLabel("Activar TTS:"))
        self.chk_tts = ModernSwitch()
        self.chk_tts.setChecked(True)
        row1.addWidget(self.chk_tts)
        
        row1.addSpacing(30)
        
        row1.addWidget(QLabel("Leer Nombre:"))
        self.chk_name = ModernSwitch() 
        self.chk_name.setChecked(True)
        row1.addWidget(self.chk_name)
        
        row1.addStretch() 
        
        # --- NUEVO: Selector de Voz (Anclado a la derecha en la fila 1) ---
        row1.addWidget(QLabel("Voz:"))
        self.combo_voice = QComboBox()
        self.combo_voice.setFixedWidth(200)
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
        
        # --- EL "ANCLA" CENTRAL ---
        # Este stretch separa el bloque de comando (izquierda) del bloque de volumen (derecha)
        row2.addStretch() 
        
        # Volumen (Anclado a la derecha)
        row2.addWidget(QLabel("Volumen:"))
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.slider_vol.setFixedWidth(200)
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

    # ─── CONTRATOS DE ESTADO (Para el Controlador) ───
    def get_tts_settings(self) -> dict:
        """Única fuente de verdad para la configuración actual (Alta Cohesión)"""
        return {
            "enabled": self.chk_tts.isChecked(),
            "read_name": self.chk_name.isChecked(),
            "use_command": self.chk_command.isChecked(),
            "command": self.txt_command.text().strip().lower()
        }

    @Slot(str, str)
    def append_message(self, user: str, message: str):
        """Agrega un nuevo mensaje con el nombre en verde en la UI"""
        html_msg = f'<b style="color: #0ca678;">{user}:</b> <span style="color: #f0f0f0;">{message}</span>'
        self.chat_display.append(html_msg)

    # --- Añadir al final de ChatView ---
    def populate_voices(self, voices: list[dict], selected_id: str):
        """Carga las voces sin romper la capa de presentación (SoR)"""
        self.combo_voice.blockSignals(True) # Evitamos bucles infinitos al cargar
        self.combo_voice.clear()
        
        for index, voice in enumerate(voices):
            # Guardamos el nombre para el usuario, y el ID interno como "UserData"
            self.combo_voice.addItem(voice["name"], userData=voice["id"])
            if voice["id"] == selected_id:
                self.combo_voice.setCurrentIndex(index)
                
        self.combo_voice.blockSignals(False)

    def _on_voice_selected(self, index: int):
        voice_id = self.combo_voice.itemData(index)
        if voice_id:
            self.voice_changed.emit(voice_id)