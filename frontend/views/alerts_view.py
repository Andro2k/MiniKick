# frontend/views/alerts_view.py

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QApplication)
from PySide6.QtCore import QTimer, Qt, Signal, Slot

from frontend.components.controls import ModernButton
from frontend.utils import get_icon_colored
from frontend.components.dialogs import AlertConfigWizard

class AlertsView(QWidget):
    alerts_mapping_changed = Signal(dict)
    preview_requested = Signal(str, dict)
    refresh_rewards_requested = Signal()

    def __init__(self):
        super().__init__()
        self.mappings = {} 
        self.current_rewards_list = []
        self.active_dialog = None
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)

        title_layout = QHBoxLayout()
        title = QLabel("Triggers & Alertas")
        title.setProperty("role", "title")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self.btn_new_alert = ModernButton("+ Nueva Alerta", role="action_accent")
        self.btn_new_alert.clicked.connect(self._open_new_alert_dialog)
        title_layout.addWidget(self.btn_new_alert)
        
        self.main_layout.addLayout(title_layout)

        self._build_obs_card()
        self._build_table_card()

    def _build_obs_card(self):
        obs_card = QFrame()
        obs_card.setObjectName("Card")
        obs_layout = QHBoxLayout(obs_card)
        obs_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_obs_url = QLabel("URL Browser Source OBS:")
        lbl_obs_url.setProperty("role", "monospace")
        
        self.btn_copy_url = ModernButton("http://localhost:8090/overlay", role="action_outlined")
        self.btn_copy_url.clicked.connect(self._copy_obs_url)
        
        obs_layout.addWidget(lbl_obs_url)
        obs_layout.addStretch()
        obs_layout.addWidget(self.btn_copy_url)
        self.main_layout.addWidget(obs_card)

    def _build_table_card(self):
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
        btn = ModernButton("", role=role)
        btn.setFixedSize(28, 28)
        btn.setIcon(get_icon_colored(icon_name, color, size=16))
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        return btn

    @Slot()
    def _copy_obs_url(self):
        QApplication.clipboard().setText("http://localhost:8090/overlay")
        original_text = self.btn_copy_url.text()
        self.btn_copy_url.setText("¡Enlace Copiado!")
        self.btn_copy_url.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_copy_btn(original_text))

    def _reset_copy_btn(self, original_text: str):
        self.btn_copy_url.setText(original_text)
        self.btn_copy_url.setEnabled(True)

    @Slot()
    def _open_new_alert_dialog(self):
        self.active_dialog = AlertConfigWizard(self, rewards_list=self.current_rewards_list)
        
        # Validación limpia de ejecución
        if self.active_dialog.exec():
            reward, config = self.active_dialog.get_config_data()
            if reward and reward not in ["Cargando recompensas...", "No hay recompensas"] and config["filepath"]:
                self.mappings[reward] = config
                self._refresh_table()
                self.alerts_mapping_changed.emit(self.mappings)
        self.active_dialog = None

    @Slot(str)
    def _edit_mapping(self, reward_name: str):
        if reward_name not in self.mappings:
            return
            
        config = self.mappings[reward_name]
        self.active_dialog = AlertConfigWizard(
            self, 
            rewards_list=self.current_rewards_list, 
            existing_config=config, 
            existing_reward=reward_name
        )
        
        # Validación limpia de ejecución
        if self.active_dialog.exec():
            _, updated_config = self.active_dialog.get_config_data()
            if updated_config["filepath"]:
                self.mappings[reward_name] = updated_config
                self._refresh_table()
                self.alerts_mapping_changed.emit(self.mappings)
        self.active_dialog = None

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
            
            filepath = config if isinstance(config, str) else config.get("filepath", "Desconocido")
            item_file = QTableWidgetItem(os.path.basename(filepath))
            item_file.setToolTip(filepath)
            item_file.setFlags(item_file.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_alerts.setItem(row, 1, item_file)
            
            actions_widget = QFrame()
            actions_widget.setObjectName("TableActions")
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
        self.current_rewards_list = rewards_list if rewards_list else ["No hay recompensas"]
        # Si el diálogo está abierto mientras los datos llegan, lo actualizamos en caliente.
        if self.active_dialog:
            self.active_dialog.update_rewards(self.current_rewards_list)