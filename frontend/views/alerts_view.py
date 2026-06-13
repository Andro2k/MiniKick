# frontend/views/alerts_view.py

import os
from PySide6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QApplication)
from PySide6.QtCore import QTimer, Qt, Signal, Slot

from frontend.components.controls import ModernButton
from frontend.components.blocks import ViewHeader, SettingRow
from frontend.theme import COLOR_ACCENT
from frontend.utils import get_icon_colored

class AlertsView(QWidget):
    # ─── CONTRATOS DE SALIDA (Hacia el Controlador) ───
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    preview_requested = Signal(str)
    refresh_rewards_requested = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

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
            title_text="Triggers & Alertas",
            subtitle_text="Vincula las recompensas de tu canal con elementos multimedia en pantalla.",
            icon_name="layout-dashboard.svg", 
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        self._build_obs_card()
        self._build_table_card()

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def _build_obs_card(self):
        obs_card = QFrame()
        obs_card.setObjectName("Card")
        obs_layout = QVBoxLayout(obs_card)
        obs_layout.setContentsMargins(10, 10, 10, 10)
        
        self.btn_copy_url = ModernButton("http://localhost:8090/overlay", role="action_outlined")
        self.btn_copy_url.clicked.connect(self._copy_obs_url)
        
        obs_row = SettingRow(
            icon_name="link.svg",
            title_text="Fuente de Navegador OBS",
            desc_text="Copia este enlace y pégalo en tu software de transmisión (Resolución recomendada: 1920x1080).",
            right_widget=self.btn_copy_url
        )
        
        obs_layout.addWidget(obs_row)
        self.main_layout.addWidget(obs_card)

    def _build_table_card(self):
        table_card = QFrame()
        table_card.setObjectName("Card")
        table_card.setMinimumHeight(300)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(10)

        table_header_layout = QHBoxLayout()
        lbl_table_title = QLabel("Recompensas Vinculadas")
        lbl_table_title.setProperty("role", "section")

        self.btn_new_alert = ModernButton("+ Nueva Alerta", role="action_accent")
        self.btn_new_alert.clicked.connect(self.add_requested.emit)

        table_header_layout.addWidget(lbl_table_title)
        table_header_layout.addStretch()
        table_header_layout.addWidget(self.btn_new_alert)

        table_layout.addLayout(table_header_layout)

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
        
        table_layout.addWidget(self.table_alerts)
        self.main_layout.addWidget(table_card, stretch=1) 

    def populate_table(self, mappings: dict):
        """Pinta la tabla desde cero recibiendo el estado dictado por el controlador."""
        self.table_alerts.setRowCount(0)
        for reward, config in mappings.items():
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
            
            btn_play = self._create_table_action_btn("play.svg", "#53FC18", "action_success", "Probar en OBS", lambda checked=False, r=reward: self.preview_requested.emit(r))
            btn_edit = self._create_table_action_btn("edit.svg", "#000000", "action_accent", "Modificar ajustes", lambda checked=False, r=reward: self.edit_requested.emit(r))
            btn_del = self._create_table_action_btn("trash.svg", "#ef4444", "action_danger", "Eliminar alerta", lambda checked=False, r=reward: self.delete_requested.emit(r))
            
            actions_layout.addWidget(btn_play)
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            
            self.table_alerts.setCellWidget(row, 2, actions_widget)

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