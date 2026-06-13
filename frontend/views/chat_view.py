# frontend/views/chat_view.py

from PySide6.QtWidgets import (QBoxLayout, QComboBox, QLineEdit, QListView, 
                               QListWidget, QListWidgetItem, QPushButton, QScrollArea, QWidget, 
                               QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QSlider, 
                               QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot

from frontend.components.controls import ModernButton, ModernSwitch
from frontend.components.blocks import ViewHeader, SettingRow, SettingSliderRow
from frontend.theme import COLOR_ACCENT
from frontend.utils import get_icon_colored 

class ChatView(QWidget):
    volume_changed = Signal(int)
    voice_changed = Signal(str)
    provider_toggled = Signal(bool)
    settings_modified = Signal(dict)
    bot_add_requested = Signal(str)
    bot_remove_requested = Signal(str)
    language_filter_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_internal_signals()

    # ─── CONSTRUCCIÓN DE LA INTERFAZ (Alta Cohesión y Responsividad) ───
    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text="Chat en Vivo",
            subtitle_text="Gestiona la moderación, lectura de voz interactiva (TTS) y eventos del canal en tiempo real.",
            icon_name="bubble-text.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        self.body_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.body_layout.setSpacing(16)

        config_card = QFrame()
        config_card.setObjectName("Card")
        config_card.setMinimumWidth(380) 
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(10, 10, 10, 10)
        config_layout.setSpacing(10)

        self.chk_tts = ModernSwitch()
        self.chk_name = ModernSwitch() 
        self.chk_provider = ModernSwitch()
        self.chk_command = ModernSwitch()
        
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setProperty("role", "monospace")

        row_tts = SettingRow("volume.svg", "Servicio de Voz (TTS)", "Habilita la lectura automatizada de mensajes.", self.chk_tts)
        row_read_name = SettingRow("user.svg", "Leer Nombres", "Pronuncia el nombre del emisor antes del mensaje.", self.chk_name)
        row_provider = SettingRow("globe.svg", "Motor de Voz Premium", "Alterna entre voces web de Edge o locales.", self.chk_provider)
        row_cmd = SettingRow("code.svg", "Requerir Comando", "Solo leer mensajes que inicien con un prefijo.", self.chk_command)
        row_volume = SettingSliderRow("adjustments-alt.svg", "Volumen General", "Ajusta la intensidad del sintetizador de voz.", self.slider_vol, self.lbl_vol_perc)
        
        lang_voice_layout = QHBoxLayout()
        self.combo_lang = QComboBox()
        self.combo_lang.setFixedWidth(120)
        self.combo_voice = QComboBox()
        self.combo_voice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lang_voice_layout.addWidget(self.combo_lang)
        lang_voice_layout.addWidget(self.combo_voice)

        self.txt_command = QLineEdit()
        self.txt_command.setPlaceholderText("Ej. !tts")
        self.txt_command.setFixedWidth(80)

        row_prefix = SettingRow(
            icon_name="hash.svg", 
            title_text="Prefijo del Comando", 
            desc_text="Define el texto exacto que activará la lectura del bot.", 
            right_widget=self.txt_command
        )

        config_layout.addWidget(row_tts)
        config_layout.addWidget(row_read_name)
        config_layout.addWidget(row_provider)
        config_layout.addLayout(lang_voice_layout)
        config_layout.addWidget(row_volume)
        config_layout.addWidget(row_cmd)
        config_layout.addWidget(row_prefix)
        config_layout.addSpacing(10)
        config_layout.addWidget(self._build_bots_panel(), stretch=1) 
        
        chat_card = QFrame()
        chat_card.setObjectName("Card")
        chat_card.setMinimumHeight(400) 
        
        chat_layout = QVBoxLayout(chat_card)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(10)

        lbl_chat_title = QLabel("Historial de la Sala")
        lbl_chat_title.setProperty("role", "section")
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("ConsoleDisplay")

        chat_layout.addWidget(lbl_chat_title)
        chat_layout.addWidget(self.chat_display)

        self.body_layout.addWidget(config_card)
        self.body_layout.addWidget(chat_card, stretch=1)
        self.main_layout.addLayout(self.body_layout)

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def _build_bots_panel(self) -> QWidget:
        """Panel integrado para silenciar bots."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Usuarios Silenciados")
        title.setProperty("role", "section_small")
        layout.addWidget(title)

        input_row = QHBoxLayout()
        self.txt_bot_input = QLineEdit()
        self.txt_bot_input.setPlaceholderText("ej. botrix")
        
        self.btn_add_bot = ModernButton("Agregar", role="action_accent")
        self.btn_add_bot.setIcon(get_icon_colored("add.svg", "#000000", size=16))
            
        input_row.addWidget(self.txt_bot_input)
        input_row.addWidget(self.btn_add_bot)
        layout.addLayout(input_row)

        self.list_bots = QListWidget()
        self.list_bots.setFlow(QListView.Flow.LeftToRight) 
        self.list_bots.setWrapping(True) 
        self.list_bots.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_bots.setObjectName("BotsList")

        layout.addWidget(self.list_bots)
        return panel

    def resizeEvent(self, event):
        """Intercepta cambios de tamaño en la ventana para simular CSS Flexbox (wrap)."""
        super().resizeEvent(event)
        if self.width() < 800:
            self.body_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        else:
            self.body_layout.setDirection(QBoxLayout.Direction.LeftToRight)

    def _connect_internal_signals(self):
        """Mapea eventos visuales nativos a nuestras señales abstractas (Decoupling)."""
        self.chk_provider.toggled.connect(self.provider_toggled.emit)
        self.slider_vol.valueChanged.connect(self._on_slider_vol_changed)
        
        self.combo_lang.currentTextChanged.connect(self.language_filter_changed.emit)
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        
        self.txt_command.textChanged.connect(self._enforce_prefix_mask)
        self.btn_add_bot.clicked.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))
        self.txt_bot_input.returnPressed.connect(lambda: self.bot_add_requested.emit(self.txt_bot_input.text()))

        controls = [self.chk_tts, self.chk_name, self.chk_command, self.txt_command]
        for control in controls:
            if isinstance(control, ModernSwitch):
                control.toggled.connect(self._emit_current_settings)
            elif isinstance(control, QLineEdit):
                control.textChanged.connect(self._emit_current_settings)

    # ─── MÉTODOS PÚBLICOS PARA EL CONTROLADOR ───
    def set_initial_states(self, settings: dict):
        """Aplica estados sin disparar señales accidentales."""
        self.blockSignals(True)
        self.chk_tts.setChecked(settings.get("enabled", True))
        self.chk_name.setChecked(settings.get("read_name", True))
        self.chk_command.setChecked(settings.get("use_command", False))
        self.txt_command.setText(settings.get("command", "!tts"))
        self.chk_provider.setChecked(settings.get("provider") == "web")
        self.slider_vol.setValue(settings.get("volume", 100))
        self.blockSignals(False)

    def clear_bot_input(self):
        self.txt_bot_input.clear()

    def add_bot_tag(self, bot_name: str):
        item = QListWidgetItem(bot_name)
        self.list_bots.addItem(item)
        
        tag_widget = QFrame()
        tag_widget.setObjectName("BotTag")
        layout = QHBoxLayout(tag_widget)
        layout.setContentsMargins(4, 4, 8, 4) 
        layout.setSpacing(4)
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        
        lbl_name = QLabel(bot_name)
        btn_delete = QPushButton()
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setIcon(get_icon_colored("trash.svg", "#ef4444", size=14))
        btn_delete.setFixedSize(22, 22)
        btn_delete.clicked.connect(lambda checked=False, i=item: self._on_bot_remove_click(i))
        
        layout.addWidget(btn_delete)
        layout.addWidget(lbl_name)
        
        item.setSizeHint(tag_widget.sizeHint())
        self.list_bots.setItemWidget(item, tag_widget)

    def clear_bots_list(self):
        self.list_bots.clear()

    def update_languages(self, langs: list[str], select_prefix: str = None):
        self.combo_lang.blockSignals(True)
        self.combo_lang.clear()
        self.combo_lang.addItems(langs)
        if select_prefix:
            idx = self.combo_lang.findText(select_prefix)
            if idx >= 0:
                self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.blockSignals(False)

    def update_voices(self, voices: list[tuple[str, str]], select_id: str = None):
        """Recibe una lista de tuplas (id, name) para rellenar la caja."""
        self.combo_voice.blockSignals(True)
        self.combo_voice.clear()
        index_to_select = 0
        for i, (v_id, v_name) in enumerate(voices):
            self.combo_voice.addItem(v_name, userData=v_id)
            if v_id == select_id:
                index_to_select = i
                
        if self.combo_voice.count() > 0:
            self.combo_voice.setCurrentIndex(index_to_select)
        self.combo_voice.blockSignals(False)

    def append_message(self, user: str, message: str):
        html_msg = f'<b style="color: #53FC18;">{user}:</b> <span style="color: #f0f0f0;">{message}</span>'
        self.chat_display.append(html_msg)

    # ─── LÓGICA PURAMENTE VISUAL (Privada) ───
    @Slot(int)
    def _on_slider_vol_changed(self, value: int):
        self.lbl_vol_perc.setText(f"{value}%")
        self.volume_changed.emit(value)

    def _enforce_prefix_mask(self, text):
        """Máscara visual (UX): Fuerza que siempre inicie con '!'"""
        if not text.startswith("!"):
            self.txt_command.setText("!" + text.replace("!", ""))

    def _emit_current_settings(self):
        self.settings_modified.emit({
            "enabled": self.chk_tts.isChecked(),
            "read_name": self.chk_name.isChecked(),
            "use_command": self.chk_command.isChecked(),
            "command": self.txt_command.text().strip().lower(),
            "provider": "web" if self.chk_provider.isChecked() else "local"
        })

    def _on_voice_selected(self, index: int):
        if index >= 0:
            voice_id = self.combo_voice.itemData(index)
            self.voice_changed.emit(voice_id)

    def _on_bot_remove_click(self, item: QListWidgetItem):
        bot_name = item.text()
        row = self.list_bots.row(item)
        self.list_bots.takeItem(row)
        self.bot_remove_requested.emit(bot_name)