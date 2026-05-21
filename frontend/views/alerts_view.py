# frontend/views/alerts_view.py

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QFileDialog, QApplication, QComboBox,
                               QSlider, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal, Slot

from frontend.components.controls import ModernButton
from frontend.utils import get_icon_colored

class AlertsView(QWidget):
    alerts_mapping_changed = Signal(dict)
    preview_requested = Signal(str, dict) # Nueva señal: Nombre, Configuración
    refresh_rewards_requested = Signal()  # Nueva señal para pedir lista a la API

    def __init__(self):
        super().__init__()
        self.mappings = {} 
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Alertas OBS (TriggerFyre)")
        title.setProperty("role", "title")
        main_layout.addWidget(title)

        # --- Tarjeta 1: Conexión OBS ---
        obs_card = QFrame()
        obs_card.setObjectName("Card")
        obs_layout = QHBoxLayout(obs_card)
        obs_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_obs_url = QLabel("URL Browser Source:  http://localhost:8080/overlay")
        lbl_obs_url.setStyleSheet("font-family: monospace; font-weight: bold;")
        
        self.btn_copy_url = ModernButton("Copiar", role="action_accent")
        self.btn_copy_url.clicked.connect(lambda: QApplication.clipboard().setText("http://localhost:8080/overlay"))
        
        obs_layout.addWidget(lbl_obs_url)
        obs_layout.addStretch()
        obs_layout.addWidget(self.btn_copy_url)
        main_layout.addWidget(obs_card)

        # --- Tarjeta 2: Formulario Avanzado ---
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        
        # SOLUCIÓN AQUÍ: Instanciar y asignar propiedad por separado
        lbl_step1 = QLabel("1. SELECCIONA LA RECOMPENSA DE KICK")
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
        
        # SOLUCIÓN AQUÍ: Instanciar y asignar propiedad por separado
        lbl_step2 = QLabel("2. ARCHIVO Y AJUSTES (Audio/Video)")
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

        # Ajustes de Visualización
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Posición (Video):"))
        self.combo_pos = QComboBox()
        self.combo_pos.addItems(["center", "top-left", "top-right", "bottom-left", "bottom-right"])
        row3.addWidget(self.combo_pos)
        
        row3.addSpacing(15)
        row3.addWidget(QLabel("Escala (Video):"))
        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setRange(0.1, 5.0)
        self.spin_scale.setSingleStep(0.1)
        self.spin_scale.setValue(1.0)
        row3.addWidget(self.spin_scale)

        row3.addSpacing(15)
        row3.addWidget(QLabel("Volumen:"))
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        row3.addWidget(self.slider_vol)

        form_layout.addLayout(row3)
        
        self.btn_add = ModernButton("Guardar Alerta", role="action_success")
        self.btn_add.clicked.connect(self._add_mapping)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.btn_add)

        main_layout.addWidget(form_card)

        # --- Tarjeta 3: Tabla de Alertas ---
        self.table_alerts = QTableWidget(0, 3)
        self.table_alerts.setHorizontalHeaderLabels(["Recompensa de Kick", "Archivo", "Acciones"])
        self.table_alerts.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_alerts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_alerts.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_alerts.setColumnWidth(2, 120) # Más espacio para 2 botones
        self.table_alerts.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        
        main_layout.addWidget(self.table_alerts)

    @Slot()
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Multimedia", "", "Media (*.mp4 *.webm *.mp3 *.wav *.ogg);;Todos (*.*)")
        if file_path:
            self.txt_file_path.setText(file_path)

    @Slot()
    def _add_mapping(self):
        reward = self.combo_rewards.currentText()
        if reward == "Cargando recompensas..." or reward == "No hay recompensas":
            return
            
        filepath = self.txt_file_path.text().strip()
        if not filepath:
            return

        # Alta Cohesión: Guardamos el objeto complejo
        self.mappings[reward] = {
            "filepath": filepath,
            "volume": self.slider_vol.value() / 100.0,
            "scale": self.spin_scale.value(),
            "position": self.combo_pos.currentText()
        }
        self._refresh_table()
        self.txt_file_path.clear()
        self.alerts_mapping_changed.emit(self.mappings)

    def _remove_mapping(self, reward_name: str):
        if reward_name in self.mappings:
            del self.mappings[reward_name]
            self._refresh_table()
            self.alerts_mapping_changed.emit(self.mappings)

    def _request_preview(self, reward_name: str):
        if reward_name in self.mappings:
            self.preview_requested.emit(reward_name, self.mappings[reward_name])

    def _refresh_table(self):
        self.table_alerts.setRowCount(0)
        for reward, config in self.mappings.items():
            row = self.table_alerts.rowCount()
            self.table_alerts.insertRow(row)
            
            item_reward = QTableWidgetItem(reward)
            item_reward.setFlags(item_reward.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_alerts.setItem(row, 0, item_reward)
            
            # Retrocompatibilidad defensiva
            filepath = config if isinstance(config, str) else config.get("filepath", "Desconocido")
            
            item_file = QTableWidgetItem(os.path.basename(filepath))
            item_file.setToolTip(filepath)
            item_file.setFlags(item_file.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_alerts.setItem(row, 1, item_file)
            
            # Celda de Acciones (Contiene 2 botones)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0,0,0,0)
            
            btn_play = ModernButton("▶", role="action_accent")
            btn_play.setToolTip("Probar en OBS")
            btn_play.clicked.connect(lambda checked=False, r=reward: self._request_preview(r))
            
            btn_del = ModernButton("", role="action_danger")
            btn_del.setIcon(get_icon_colored("trash.svg", "#FFFFFF", size=16))
            btn_del.clicked.connect(lambda checked=False, r=reward: self._remove_mapping(r))
            
            actions_layout.addWidget(btn_play)
            actions_layout.addWidget(btn_del)
            self.table_alerts.setCellWidget(row, 2, actions_widget)

    def set_initial_mappings(self, mappings: dict):
        self.mappings = mappings.copy() if mappings else {}
        self._refresh_table()
        
    @Slot(list)
    def update_rewards_combo(self, rewards_list: list):
        """Recibe la lista de la API y puebla el ComboBox"""
        self.combo_rewards.clear()
        if not rewards_list:
            self.combo_rewards.addItem("No hay recompensas")
        else:
            self.combo_rewards.addItems(rewards_list)