# frontend/views/alerts_view.py

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QFileDialog, QApplication, QComboBox,
                               QSlider, QDoubleSpinBox, QSpinBox)
from PySide6.QtCore import Qt, Signal, Slot

from frontend.components.controls import ModernButton, ModernSwitch
from frontend.utils import get_icon_colored

class AlertsView(QWidget):
    # ─── SEÑALES (Comunicación con el Controlador) ───
    alerts_mapping_changed = Signal(dict)
    preview_requested = Signal(str, dict)
    refresh_rewards_requested = Signal()

    def __init__(self):
        super().__init__()
        self.mappings = {} 
        self._setup_ui()

    # =========================================================================
    # ─── CAPA DE PRESENTACIÓN (SoR: Solo construcción visual) ───
    # =========================================================================
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        title = QLabel("Alertas OBS (TriggerFyre)")
        title.setProperty("role", "title")
        self.main_layout.addWidget(title)

        self._build_obs_card()
        self._build_form_card()
        self._build_table_card()

    def _build_obs_card(self):
        """Construye la tarjeta de conexión de OBS (Alta Cohesión)."""
        obs_card = QFrame()
        obs_card.setObjectName("Card")
        obs_layout = QHBoxLayout(obs_card)
        obs_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_obs_url = QLabel("URL Browser Source:  http://localhost:8090/overlay")
        lbl_obs_url.setStyleSheet("font-family: monospace; font-weight: bold;")
        
        self.btn_copy_url = ModernButton("Copiar", role="action_accent")
        self.btn_copy_url.clicked.connect(lambda: QApplication.clipboard().setText("http://localhost:8090/overlay"))
        
        obs_layout.addWidget(lbl_obs_url)
        obs_layout.addStretch()
        obs_layout.addWidget(self.btn_copy_url)
        self.main_layout.addWidget(obs_card)

    def _build_form_card(self):
        """Construye el formulario de configuración de alertas."""
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        
        # Paso 1: Recompensa
        lbl_step1 = QLabel("1. Seleccione la recompensa de KICK")
        lbl_step1.setProperty("role", "section")
        form_layout.addWidget(lbl_step1)
        
        row1 = QHBoxLayout()
        self.combo_rewards = QComboBox()
        self.combo_rewards.addItem("Cargando recompensas...")
        self.btn_refresh = ModernButton("Actualizar Lista")
        self.btn_refresh.clicked.connect(self.refresh_rewards_requested.emit)
        row1.addWidget(self.combo_rewards, stretch=1)
        row1.addWidget(self.btn_refresh)
        form_layout.addLayout(row1)

        form_layout.addSpacing(10)
        
        # Paso 2: Archivo y Ajustes
        lbl_step2 = QLabel("2. Archivo y Ajustes (Audio/Video)")
        lbl_step2.setProperty("role", "section")
        form_layout.addWidget(lbl_step2)

        row2 = QHBoxLayout()
        self.txt_file_path = QLineEdit()
        self.txt_file_path.setReadOnly(True)
        self.btn_browse = ModernButton("Explorar Archivo")
        self.btn_browse.clicked.connect(self._browse_file)
        row2.addWidget(self.txt_file_path, stretch=1)
        row2.addWidget(self.btn_browse)
        form_layout.addLayout(row2)

        # Fila de Posiciones y Escala
        row3 = QHBoxLayout()
        
        # NUEVO: Control de Posición Aleatoria
        row3.addWidget(QLabel("Pos Random:"))
        self.chk_random_pos = ModernSwitch()
        self.chk_random_pos.setEnabled(False) # Desactivado por defecto hasta cargar un video
        self.chk_random_pos.toggled.connect(self._on_random_pos_toggled)
        row3.addWidget(self.chk_random_pos)
        row3.addSpacing(8)

        row3.addWidget(QLabel("Pos X:"))
        self.spin_x = QSpinBox()
        self.spin_x.setRange(-5000, 5000)
        self.spin_x.setValue(0)
        row3.addWidget(self.spin_x)
        
        row3.addSpacing(8)
        row3.addWidget(QLabel("Pos Y:"))
        self.spin_y = QSpinBox()
        self.spin_y.setRange(-5000, 5000)
        self.spin_y.setValue(0)
        row3.addWidget(self.spin_y)
        
        row3.addSpacing(8)
        row3.addWidget(QLabel("Escala:"))
        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setRange(0.1, 5.0)
        self.spin_scale.setSingleStep(0.1)
        self.spin_scale.setValue(1.0)
        row3.addWidget(self.spin_scale)
        row3.addStretch()
        form_layout.addLayout(row3)

        # Nueva Fila Exclusiva para Volumen
        row_vol = QHBoxLayout()
        row_vol.addWidget(QLabel("Volumen:"))
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        row_vol.addWidget(self.slider_vol)
        form_layout.addLayout(row_vol)
        
        # Botón Guardar
        self.btn_add = ModernButton("Guardar Alerta", role="action_success")
        self.btn_add.clicked.connect(self._add_mapping)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.btn_add)

        self.main_layout.addWidget(form_card)

    def _build_table_card(self):
        """Construye y configura la tabla de gestión de alertas."""
        self.table_alerts = QTableWidget(0, 3)
        self.table_alerts.setHorizontalHeaderLabels(["Recompensa de Kick", "Archivo", "Acciones"])
        self.table_alerts.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_alerts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_alerts.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_alerts.setColumnWidth(2, 140) 
        
        self.table_alerts.verticalHeader().setVisible(False)
        self.table_alerts.verticalHeader().setDefaultSectionSize(45)
        self.table_alerts.setShowGrid(False)
        self.table_alerts.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table_alerts.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
        
        self.main_layout.addWidget(self.table_alerts)

    def _create_table_action_btn(self, icon_name: str, color: str, role: str, tooltip: str, callback) -> ModernButton:
        """Helper para generar botones de acción en la tabla (DRY Principle)."""
        btn = ModernButton("", role=role)
        btn.setFixedSize(28, 28)
        btn.setIcon(get_icon_colored(icon_name, color, size=16))
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        return btn

    # =========================================================================
    # ─── CAPA LOGICA (SoR: Solo gestión de datos y eventos) ───
    # =========================================================================
    
    @Slot(bool)
    def _on_random_pos_toggled(self, checked: bool):
        """Bloquea o desbloquea las coordenadas según el estado del switch."""
        self.spin_x.setEnabled(not checked)
        self.spin_y.setEnabled(not checked)

    def _evaluate_media_type(self, filepath: str):
        """Valida si es video para habilitar la opción aleatoria."""
        is_video = filepath.lower().endswith(('.mp4', '.webm'))
        self.chk_random_pos.setEnabled(is_video)
        
        if not is_video:
            self.chk_random_pos.setChecked(False)

    @Slot()
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Multimedia", "", "Media (*.mp4 *.webm *.mp3 *.wav *.ogg);;Todos (*.*)")
        if file_path:
            self.txt_file_path.setText(file_path)
            self._evaluate_media_type(file_path)

    @Slot()
    def _add_mapping(self):
        reward = self.combo_rewards.currentText()
        if reward in ["Cargando recompensas...", "No hay recompensas"]:
            return
            
        filepath = self.txt_file_path.text().strip()
        if not filepath:
            return

        self.mappings[reward] = {
            "filepath": filepath,
            "volume": self.slider_vol.value() / 100.0,
            "scale": self.spin_scale.value(),
            "pos_x": self.spin_x.value(),
            "pos_y": self.spin_y.value(),
            "is_random_pos": self.chk_random_pos.isChecked() # <-- CORRECCIÓN: is_random_pos
        }
        self._refresh_table()
        
        self.txt_file_path.clear()
        self.chk_random_pos.setChecked(False)
        self.chk_random_pos.setEnabled(False)
        self.btn_add.setText("Guardar Alerta")
        self.alerts_mapping_changed.emit(self.mappings)

    def _remove_mapping(self, reward_name: str):
        if reward_name in self.mappings:
            del self.mappings[reward_name]
            self._refresh_table()
            self.alerts_mapping_changed.emit(self.mappings)

    def _request_preview(self, reward_name: str):
        """Emite la señal al controlador principal para reproducir en OBS."""
        if reward_name in self.mappings:
            self.preview_requested.emit(reward_name, self.mappings[reward_name])

    @Slot(str)
    def _edit_mapping(self, reward_name: str):
        if reward_name not in self.mappings:
            return
            
        config = self.mappings[reward_name]
        
        index = self.combo_rewards.findText(reward_name)
        if index >= 0:
            self.combo_rewards.setCurrentIndex(index)
        else:
            self.combo_rewards.addItem(reward_name)
            self.combo_rewards.setCurrentText(reward_name)
            
        filepath = config if isinstance(config, str) else config.get("filepath", "")
        self.txt_file_path.setText(filepath)
        
        if isinstance(config, dict):
            self.spin_x.setValue(config.get("pos_x", 0))
            self.spin_y.setValue(config.get("pos_y", 0))
            self.spin_scale.setValue(config.get("scale", 1.0))
            self.slider_vol.setValue(int(config.get("volume", 1.0) * 100))
            
            self._evaluate_media_type(filepath)
            
            # <-- CORRECCIÓN: Carga correctamente la variable
            self.chk_random_pos.setChecked(config.get("is_random_pos", False)) 
            
        self.btn_add.setText("Actualizar Alerta")

    def _refresh_table(self):
        self.table_alerts.setRowCount(0)
        for reward, config in self.mappings.items():
            row = self.table_alerts.rowCount()
            self.table_alerts.insertRow(row)
            
            item_reward = QTableWidgetItem(reward)
            item_reward.setFlags(item_reward.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_alerts.setItem(row, 0, item_reward)
            
            filepath = config if isinstance(config, str) else config.get("filepath", "Desconocido")
            item_file = QTableWidgetItem(os.path.basename(filepath))
            item_file.setToolTip(filepath)
            item_file.setFlags(item_file.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_alerts.setItem(row, 1, item_file)
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0) 
            actions_layout.setSpacing(8)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_play = self._create_table_action_btn("play.svg", "#000000", "action_accent", "Probar en OBS", lambda checked=False, r=reward: self._request_preview(r))
            btn_edit = self._create_table_action_btn("edit.svg", "#000000", "action_accent", "Modificar ajustes", lambda checked=False, r=reward: self._edit_mapping(r))
            btn_del = self._create_table_action_btn("trash.svg", "#ef4444", "action_danger", "Eliminar alerta", lambda checked=False, r=reward: self._remove_mapping(r))
            
            actions_layout.addWidget(btn_play)
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            
            self.table_alerts.setCellWidget(row, 2, actions_widget)

    def set_initial_mappings(self, mappings: dict):
        self.mappings = mappings.copy() if mappings else {}
        self._refresh_table()
        
    @Slot(list)
    def update_rewards_combo(self, rewards_list: list):
        self.combo_rewards.clear()
        if not rewards_list:
            self.combo_rewards.addItem("No hay recompensas")
        else:
            self.combo_rewards.addItems(rewards_list)