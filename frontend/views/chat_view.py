# frontend/views/chat_view.py

from PySide6.QtWidgets import (QBoxLayout, QComboBox, QLineEdit, QListView, QListWidget, QListWidgetItem, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QLabel, QSlider, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot

from frontend.components.controls import ModernButton, ModernSwitch
from frontend.components.blocks import ViewHeader, SettingRow, SettingSliderRow
from frontend.theme import COLOR_ACCENT
from frontend.utils import get_icon_colored 

class ChatView(QWidget):
    # ─── CONTRATOS DE SALIDA (Para el Controlador) ───
    volume_changed = Signal(int)
    voice_changed = Signal(str)
    provider_changed = Signal(str)
    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_internal_signals()

    # =========================================================================
    # ─── CONSTRUCCIÓN DE LA INTERFAZ (Alta Cohesión y Responsividad) ───
    # =========================================================================
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        # ─── 1. ENCABEZADO DE LA VISTA ───
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

        # --- USO DE COMPONENTES REUTILIZABLES ---
        row_tts = SettingRow("volume.svg", "Servicio de Voz (TTS)", "Habilita la lectura automatizada de mensajes.", self.chk_tts)
        row_read_name = SettingRow("user.svg", "Leer Nombres", "Pronuncia el nombre del emisor antes del mensaje.", self.chk_name)
        row_provider = SettingRow("globe.svg", "Motor de Voz Premium", "Alterna entre voces web de Edge o locales.", self.chk_provider)
        row_cmd = SettingRow("terminal.svg", "Requerir Comando", "Solo leer mensajes que inicien con un prefijo.", self.chk_command)
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

        # Lo inyectamos en nuestro componente estandarizado
        row_prefix = SettingRow(
            icon_name="hash.svg", # Puedes cambiar este icono por 'keyboard.svg' o 'edit.svg' si prefieres
            title_text="Prefijo del Comando", 
            desc_text="Define el texto exacto que activará la lectura del bot.", 
            right_widget=self.txt_command
        )

        # Agregamos los componentes (notar el uso de addWidget en lugar de addLayout para los SettingRow)
        config_layout.addWidget(row_tts)
        config_layout.addWidget(row_read_name)
        config_layout.addWidget(row_provider)
        config_layout.addLayout(lang_voice_layout)
        config_layout.addWidget(row_volume)
        
        config_layout.addWidget(row_cmd)
        config_layout.addWidget(row_prefix)
        config_layout.addSpacing(10)
        
        config_layout.addWidget(self._build_bots_panel(), stretch=1) 
        
        # ─── 3. PANEL DE VISUALIZACIÓN DEL CHAT (DERECHO / INFERIOR) ───
        chat_card = QFrame()
        chat_card.setObjectName("Card")
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

    # ─── GESTIÓN DE LA TABLA DE BOTS ───
    @Slot()
    def _handle_add_bot_request(self):
        bot_name = self.txt_bot_input.text()
        self._add_bot_to_list(bot_name, trigger_update=True)

    def _add_bot_to_list(self, bot_name: str, trigger_update: bool = True):
        bot_name = bot_name.strip().lower()
        if not bot_name: 
            return
        if self.list_bots.findItems(bot_name, Qt.MatchFlag.MatchExactly):
            self.txt_bot_input.clear()
            return 

        item = QListWidgetItem(bot_name)
        self.list_bots.addItem(item)
        
        tag_widget = QFrame()
        tag_widget.setObjectName("BotTag")
        
        layout = QHBoxLayout(tag_widget)
        layout.setContentsMargins(4, 4, 8, 4) 
        layout.setSpacing(4)
        
        # CRÍTICO: Obliga al contenedor a envolver el texto y el botón con precisión
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)
        
        lbl_name = QLabel(bot_name)
        # (Se eliminó la línea de QSizePolicy que colapsaba el texto)
        
        btn_delete = QPushButton()
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setIcon(get_icon_colored("trash.svg", "#ef4444", size=14))
        btn_delete.setFixedSize(22, 22)
        btn_delete.setToolTip("Eliminar bot")
        btn_delete.clicked.connect(lambda checked=False, i=item: self._remove_bot_item(i))
        
        layout.addWidget(btn_delete)
        layout.addWidget(lbl_name)
        
        item.setSizeHint(tag_widget.sizeHint())
        self.list_bots.setItemWidget(item, tag_widget)
        self.txt_bot_input.clear()
        
        if trigger_update:
            self._on_settings_modified()

    @Slot(QListWidgetItem)
    def _remove_bot_item(self, item: QListWidgetItem):
        """Elimina el tag específico usando su referencia exacta."""
        row = self.list_bots.row(item)
        self.list_bots.takeItem(row)
        self._on_settings_modified()

    @Slot(QListWidgetItem)
    def _handle_bot_clicked(self, item):
        """Elimina el bot al hacer clic sobre su etiqueta (Alta Cohesión)."""
        row = self.list_bots.row(item)
        self.list_bots.takeItem(row)
        self._on_settings_modified()

    def _get_bots_as_string(self) -> str:
        """Recorre la lista y devuelve un string separado por comas para guardar."""
        bots = []
        for i in range(self.list_bots.count()):
            bots.append(self.list_bots.item(i).text())
        return ", ".join(bots)

    def _connect_internal_signals(self):
        self.chk_provider.toggled.connect(self._on_provider_toggled)
        self.combo_lang.currentIndexChanged.connect(self._filter_voices_by_lang)
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        self.slider_vol.valueChanged.connect(self._on_slider_vol_changed)
        self.txt_command.textChanged.connect(self._validate_command)
        self.btn_add_bot.clicked.connect(self._handle_add_bot_request)
        self.txt_bot_input.returnPressed.connect(self._handle_add_bot_request)

        controls = [self.chk_tts, self.chk_name, self.chk_command, self.txt_command]
        for control in controls:
            if isinstance(control, ModernSwitch):
                control.toggled.connect(self._on_settings_modified)
            elif isinstance(control, QLineEdit):
                control.textChanged.connect(self._on_settings_modified)

    @Slot(int)
    def _on_slider_vol_changed(self, value: int):
        """Actualiza la interfaz visual y luego emite la señal al controlador."""
        self.lbl_vol_perc.setText(f"{value}%")
        self.volume_changed.emit(value)

    def resizeEvent(self, event):
        """Intercepta cambios de tamaño en la ventana para simular CSS Flexbox (wrap)."""
        super().resizeEvent(event)
        if self.width() < 800:
            self.body_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        else:
            self.body_layout.setDirection(QBoxLayout.Direction.LeftToRight)

    def _validate_command(self, text):
        if not text.startswith("!"):
            self.txt_command.setText("!" + text.replace("!", ""))

    def _on_provider_toggled(self, is_web: bool):
        provider = "web" if is_web else "local"
        self.combo_voice.blockSignals(True)
        self.combo_voice.clear()
        self.combo_voice.addItem("Cargando voces...", userData=None)
        self.combo_voice.blockSignals(False)
        self._on_settings_modified()
        self.provider_changed.emit(provider)

    def _on_settings_modified(self, *args):
        self.settings_changed.emit(self.get_tts_settings())

    def _on_voice_selected(self, index: int):
        if index < 0:
            return       
        voice_id = self.combo_voice.itemData(index)
        if voice_id:
            self.voice_changed.emit(voice_id)

    def get_tts_settings(self) -> dict:
        return {
            "enabled": self.chk_tts.isChecked(),
            "read_name": self.chk_name.isChecked(),
            "use_command": self.chk_command.isChecked(),
            "command": self.txt_command.text().strip().lower(),
            "provider": "web" if self.chk_provider.isChecked() else "local",
            "ignored_users": self._get_bots_as_string() 
        }

    def set_initial_settings(self, settings: dict):
        self.chk_tts.blockSignals(True)
        self.chk_name.blockSignals(True)
        self.chk_command.blockSignals(True)
        self.txt_command.blockSignals(True)
        self.chk_provider.blockSignals(True)

        self.chk_tts.setChecked(settings.get("enabled", True))
        self.chk_name.setChecked(settings.get("read_name", True))
        self.chk_command.setChecked(settings.get("use_command", False))
        self.txt_command.setText(settings.get("command", "!tts"))
        self.chk_provider.setChecked(settings.get("provider") == "web")

        # Cargar los bots ignorados en la tabla
        self.list_bots.clear() 
        ignored_str = settings.get("ignored_users", "")
        if ignored_str:
            for bot in ignored_str.split(","):
                self._add_bot_to_list(bot, trigger_update=False)

        self.chk_tts.blockSignals(False)
        self.chk_name.blockSignals(False)
        self.chk_command.blockSignals(False)
        self.txt_command.blockSignals(False)
        self.chk_provider.blockSignals(False)

    @Slot(str, str)
    def append_message(self, user: str, message: str):
        html_msg = f'<b style="color: #0ca678;">{user}:</b> <span style="color: #f0f0f0;">{message}</span>'
        self.chat_display.append(html_msg)

    def populate_voices(self, voices: list[dict], selected_id: str = None, mute_signal: bool = False):
        """Carga las voces iniciales y extrae los idiomas disponibles."""
        self._all_voices = voices
        
        langs = []
        for v in voices:
            prefix = "-".join(v["id"].split("-")[:2]) if "-" in v["id"] else "Local"
            if prefix not in langs:
                langs.append(prefix)

        self.combo_lang.blockSignals(True)
        self.combo_lang.clear()
        self.combo_lang.addItems(langs)
        self.combo_lang.blockSignals(False)

        if selected_id:
            sel_prefix = "-".join(selected_id.split("-")[:2]) if "-" in selected_id else "Local"
            idx = self.combo_lang.findText(sel_prefix)
            if idx >= 0:
                self.combo_lang.blockSignals(True)
                self.combo_lang.setCurrentIndex(idx)
                self.combo_lang.blockSignals(False)

        self._apply_voice_filter(selected_id, mute_signal)

    @Slot()
    def _filter_voices_by_lang(self):
        self._apply_voice_filter(selected_id=None, mute_signal=False)

    def _apply_voice_filter(self, selected_id=None, mute_signal=False):
        """Lógica centralizada para filtrar las voces según el idioma actual."""
        current_lang = self.combo_lang.currentText()

        self.combo_voice.blockSignals(True) 
        self.combo_voice.clear()
        
        index_to_select = 0
        count = 0
        
        for voice in getattr(self, '_all_voices', []):
            prefix = "-".join(voice["id"].split("-")[:2]) if "-" in voice["id"] else "Local"
            
            if prefix == current_lang:
                self.combo_voice.addItem(voice["name"], userData=voice["id"])
                
                if voice["id"] == selected_id:
                    index_to_select = count
                count += 1

        if self.combo_voice.count() > 0:
            self.combo_voice.setCurrentIndex(index_to_select)
        self.combo_voice.blockSignals(False)
        if not mute_signal and self.combo_voice.count() > 0:
            self._on_voice_selected(index_to_select)