# frontend/views/chat_view.py

import os
from PySide6.QtWidgets import (QComboBox, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QLabel, QSlider, QFrame, QSizePolicy, 
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon

from frontend.components.controls import SegmentedToggle, ModernButton, ModernSwitch
from frontend.utils import resource_path, get_icon_colored 

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

    # ─── CONSTRUCCIÓN DE LA INTERFAZ (Alta Cohesión) ───
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Título
        title = QLabel("Chat en Vivo")
        title.setProperty("role", "title")
        main_layout.addWidget(title)
        
        # Tarjeta de Controles Superiores
        controls_frame = QFrame()
        controls_frame.setObjectName("Card")
        controls_layout = QVBoxLayout(controls_frame) 
        controls_layout.setContentsMargins(16, 16, 16, 16)
        controls_layout.setSpacing(12)
        
        controls_layout.addLayout(self._build_toggles_row())
        controls_layout.addLayout(self._build_voice_and_volume_section()) # <-- CAMBIO AQUÍ
        controls_layout.addLayout(self._build_filters_row())
        
        main_layout.addWidget(controls_frame)

        # Área Inferior: Chat + Panel de Bots (Flex HBox)
        bottom_area = QHBoxLayout()
        bottom_area.setSpacing(12)
        
        # Display del Chat (Flex-grow: 1)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("ChatContainer")
        self.chat_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bottom_area.addWidget(self.chat_display)

        # Panel Lateral de Bots (Ancho fijo)
        bots_panel = self._build_bots_panel()
        bottom_area.addWidget(bots_panel)

        main_layout.addLayout(bottom_area)

    def _build_toggles_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(QLabel("Activar TTS:"))
        self.chk_tts = ModernSwitch()
        row.addWidget(self.chk_tts)
        row.addWidget(QLabel("Leer Nombre:"))
        self.chk_name = ModernSwitch() 
        row.addWidget(self.chk_name)
        row.addSpacing(20)
        row.addWidget(QLabel("Motor:"))
        self.chk_provider = SegmentedToggle("LOCAL", "WEB IA", default_right=False)
        row.addWidget(self.chk_provider)
        row.addStretch()
        return row

    def _build_voice_and_volume_section(self) -> QVBoxLayout:
        section = QVBoxLayout()
        section.setSpacing(12)
        
        # --- Fila 1: Selector de Idioma y Voz ---
        row_voice = QHBoxLayout()
        row_voice.setSpacing(12)
        row_voice.addWidget(QLabel("Voz:"))
        
        self.combo_lang = QComboBox()
        self.combo_lang.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_lang.setFixedWidth(100)
        row_voice.addWidget(self.combo_lang)

        self.combo_voice = QComboBox()
        self.combo_voice.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_voice.setStyleSheet("QAbstractItemView { font-size: 13px; }")
        self.combo_voice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_voice.addWidget(self.combo_voice)
        
        # --- Fila 2: Volumen con Indicador ---
        row_vol = QHBoxLayout()
        row_vol.addWidget(QLabel("Volumen:"))
        
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setFixedWidth(40)
        self.lbl_vol_perc.setStyleSheet("color: #0ca678; font-weight: bold;")
        
        row_vol.addWidget(self.slider_vol)
        row_vol.addWidget(self.lbl_vol_perc)
        
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol_perc.setText(f"{v}%"))
        
        # AQUÍ ESTABA EL ERROR: Cambiamos self._build_voice_row() por row_voice
        section.addLayout(row_voice) 
        section.addLayout(row_vol)
        
        return section

    def _build_filters_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(QLabel("Usar Comando:"))
        self.chk_command = ModernSwitch() 
        row.addWidget(self.chk_command)
        self.txt_command = QLineEdit("!tts")
        self.txt_command.setFixedWidth(70)
        row.addWidget(self.txt_command)
        row.addStretch()
        return row

    def _build_bots_panel(self) -> QFrame:
        """Construye el panel lateral derecho para gestionar bots (SoR)"""
        panel = QFrame()
        panel.setObjectName("Card") 
        panel.setFixedWidth(260)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("Silenciar Usuarios/Bots")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        # Fila de Input + Botón
        input_row = QHBoxLayout()
        self.txt_bot_input = QLineEdit()
        self.txt_bot_input.setPlaceholderText("ej. @botrix")
        
        self.btn_add_bot = ModernButton(" Agregar", role="action_accent")
        self.btn_add_bot.setIcon(get_icon_colored("add.svg", "#FFFFFF", size=16))
        icon_add_path = resource_path(os.path.join("assets", "icons", "add.svg"))
        if os.path.exists(icon_add_path):
            self.btn_add_bot.setIcon(QIcon(icon_add_path))
            
        input_row.addWidget(self.txt_bot_input)
        input_row.addWidget(self.btn_add_bot)
        layout.addLayout(input_row)

        # Tabla (Lista visual)
        self.table_bots = QTableWidget(0, 2)
        self.table_bots.horizontalHeader().setVisible(False)
        self.table_bots.verticalHeader().setVisible(False)
        self.table_bots.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_bots.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_bots.setColumnWidth(1, 45) # Ancho ajustado para acomodar el padding de theme.py
        self.table_bots.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table_bots.setShowGrid(False)
        self.table_bots.setStyleSheet("QTableWidget { border: none; background: transparent; }")
        layout.addWidget(self.table_bots)

        return panel

    # ─── GESTIÓN DE LA TABLA DE BOTS ───
    @Slot()
    def _handle_add_bot_request(self):
        bot_name = self.txt_bot_input.text()
        self._add_bot_to_table(bot_name, trigger_update=True)

    def _add_bot_to_table(self, bot_name: str, trigger_update: bool = True):
        # Limpieza del string: conservamos el @
        bot_name = bot_name.strip().lower()
        if not bot_name: 
            return

        # Evitar duplicados (DRY)
        for row in range(self.table_bots.rowCount()):
            item = self.table_bots.item(row, 0)
            if item and item.text() == bot_name:
                self.txt_bot_input.clear()
                return 

        row_idx = self.table_bots.rowCount()
        self.table_bots.insertRow(row_idx)
        
        # Nombre (Celda Izquierda)
        name_item = QTableWidgetItem(bot_name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable) 
        self.table_bots.setItem(row_idx, 0, name_item)
        
        # Botón Eliminar usando ModernButton con el rol action_danger (DRY)
        btn_delete = ModernButton("", role="action_danger")
        btn_delete.setIcon(get_icon_colored("trash.svg", "#FFFFFF", size=16))
        btn_delete.setToolTip("Eliminar de la lista")
        
        btn_delete.clicked.connect(lambda checked=False, b=bot_name: self._remove_bot(b))
        self.table_bots.setCellWidget(row_idx, 1, btn_delete)
        
        self.txt_bot_input.clear()
        
        if trigger_update:
            self._on_settings_modified()

    def _remove_bot(self, bot_name: str):
        """Busca el bot por nombre y elimina la fila."""
        for row in range(self.table_bots.rowCount()):
            item = self.table_bots.item(row, 0)
            if item and item.text() == bot_name:
                self.table_bots.removeRow(row)
                self._on_settings_modified()
                break

    def _get_bots_as_string(self) -> str:
        """Recorre la tabla y devuelve un string separado por comas para guardar."""
        bots = []
        for row in range(self.table_bots.rowCount()):
            item = self.table_bots.item(row, 0)
            if item:
                bots.append(item.text())
        return ", ".join(bots)

    # ─── GESTIÓN DE EVENTOS INTERNOS ───
    def _connect_internal_signals(self):
        # Combos y Sliders
        self.chk_provider.toggled.connect(self._on_provider_toggled)
        self.combo_lang.currentIndexChanged.connect(self._filter_voices_by_lang) # <-- NUEVO
        self.combo_voice.currentIndexChanged.connect(self._on_voice_selected)
        self.slider_vol.valueChanged.connect(self.volume_changed.emit)
        self.txt_command.textChanged.connect(self._validate_command)
        
        # Eventos del panel de bots
        self.btn_add_bot.clicked.connect(self._handle_add_bot_request)
        self.txt_bot_input.returnPressed.connect(self._handle_add_bot_request)

        # Emisión global de cambios para guardado
        controls = [self.chk_tts, self.chk_name, self.chk_command, self.txt_command]
        for control in controls:
            if isinstance(control, ModernSwitch):
                control.toggled.connect(self._on_settings_modified)
            elif isinstance(control, QLineEdit):
                control.textChanged.connect(self._on_settings_modified)

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
        voice_id = self.combo_voice.itemData(index)
        if voice_id:
            self.voice_changed.emit(voice_id)

    # ─── CONTRATOS DE ESTADO Y DATOS (SoR) ───
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
        self.table_bots.setRowCount(0) 
        ignored_str = settings.get("ignored_users", "")
        if ignored_str:
            for bot in ignored_str.split(","):
                self._add_bot_to_table(bot, trigger_update=False)

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

        # Llenamos el combo de idiomas sin disparar señales
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

        # Aplicamos el filtro de voces con el flag de silencio
        self._apply_voice_filter(selected_id, mute_signal)

    @Slot()
    def _filter_voices_by_lang(self):
        """Slot que se ejecuta cuando el USUARIO cambia el idioma manualmente."""
        # Al cambiar de idioma manualmente, no hay voz seleccionada previamente ni queremos mutearlo
        self._apply_voice_filter(selected_id=None, mute_signal=False)

    def _apply_voice_filter(self, selected_id=None, mute_signal=False):
        """Lógica centralizada para filtrar las voces según el idioma actual."""
        current_lang = self.combo_lang.currentText()
        
        # Bloqueamos el combo de voces si estamos en la carga inicial
        if mute_signal:
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
                
        # Seleccionamos la voz correspondiente
        if self.combo_voice.count() > 0:
            self.combo_voice.setCurrentIndex(index_to_select)
            
            # Si NO estamos en modo silencioso, emitimos la señal para que el bot hable
            if not mute_signal:
                self._on_voice_selected(index_to_select)
                
        # Desbloqueamos si lo habíamos bloqueado
        if mute_signal:
            self.combo_voice.blockSignals(False)