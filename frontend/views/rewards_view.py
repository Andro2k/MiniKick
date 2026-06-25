# frontend\views\rewards_view.py

import os
from PySide6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QApplication)
from PySide6.QtCore import QTimer, Qt, Signal, Slot

from frontend.widgets.controls_component import ModernButton
from frontend.widgets.blocks_component import ViewHeader, SettingRow
from frontend.common.theme import COLOR_ACCENT, COLOR_BLACK, COLOR_DANGER
from frontend.common.utils import get_icon_colored

class RewardsView(QWidget):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    preview_requested = Signal(str)
    refresh_rewards_requested = Signal()

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text=self.i18n.get("rewards.header.title"),
            subtitle_text=self.i18n.get("rewards.header.subtitle"),
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
        obs_card.setProperty("role", "card")
        obs_layout = QVBoxLayout(obs_card)
        obs_layout.setContentsMargins(8, 8, 8, 8)

        self.btn_copy_url = ModernButton("http://localhost:8090/overlay", role="action_outlined")
        self.btn_copy_url.clicked.connect(self._copy_obs_url)
        
        obs_row = SettingRow(
            icon_name="link.svg",
            title_text=self.i18n.get("rewards.obs.title"),
            desc_text=self.i18n.get("rewards.obs.desc"),
            right_widget=self.btn_copy_url
        )
        
        obs_layout.addWidget(obs_row)
        self.main_layout.addWidget(obs_card)

    def _build_table_card(self):
        table_card = QFrame()
        table_card.setProperty("role", "card")
        table_card.setMinimumHeight(300)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(8, 8, 8, 8)
        table_layout.setSpacing(6)

        table_header_layout = QHBoxLayout()
        lbl_table_title = QLabel(self.i18n.get("rewards.table.title"))
        lbl_table_title.setProperty("role", "h3")

        self.btn_new_rewards = ModernButton(self.i18n.get("rewards.table.btn_new"), role="action_accent")
        self.btn_new_rewards.setIcon(get_icon_colored("add.svg", COLOR_BLACK, 16))
        self.btn_new_rewards.clicked.connect(self.add_requested.emit)

        table_header_layout.addWidget(lbl_table_title)
        table_header_layout.addStretch()
        table_header_layout.addWidget(self.btn_new_rewards)

        table_layout.addLayout(table_header_layout)

        self.table_rewards = QTableWidget(0, 3)
        col_1 = self.i18n.get("rewards.table.col_reward")
        col_2 = self.i18n.get("rewards.table.col_file")
        col_3 = self.i18n.get("rewards.table.col_actions")
        self.table_rewards.setHorizontalHeaderLabels([col_1, col_2, col_3])
        
        self.table_rewards.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_rewards.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_rewards.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_rewards.setColumnWidth(2, 140) 
        
        self.table_rewards.verticalHeader().setVisible(False)
        self.table_rewards.verticalHeader().setDefaultSectionSize(45)
        self.table_rewards.setShowGrid(False)
        self.table_rewards.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table_rewards.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
        
        table_layout.addWidget(self.table_rewards)
        self.main_layout.addWidget(table_card, stretch=1) 

    def populate_table(self, mappings: dict):
        self.table_rewards.setRowCount(0)
        str_unknown = self.i18n.get("rewards.table.unknown_file")
        
        for reward, config in mappings.items():
            row = self.table_rewards.rowCount()
            self.table_rewards.insertRow(row)
            
            item_reward = QTableWidgetItem(reward)
            item_reward.setFlags(item_reward.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 0, item_reward)
            
            filepath = config if isinstance(config, str) else config.get("filepath", str_unknown)
            item_file = QTableWidgetItem(os.path.basename(filepath))
            item_file.setToolTip(filepath)
            item_file.setFlags(item_file.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 1, item_file)
            
            actions_widget = QFrame()
            actions_widget.setObjectName("TableActions")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0) 
            actions_layout.setSpacing(8)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn_play = self._create_table_action_btn("play.svg", COLOR_ACCENT, "action_outlined", self.i18n.get("rewards.table.tooltip_play"), lambda checked=False, r=reward: self.preview_requested.emit(r))
            btn_edit = self._create_table_action_btn("edit.svg", COLOR_BLACK, "action_accent", self.i18n.get("rewards.table.tooltip_edit"), lambda checked=False, r=reward: self.edit_requested.emit(r))
            btn_del = self._create_table_action_btn("trash.svg", COLOR_DANGER, "action_danger", self.i18n.get("rewards.table.tooltip_delete"), lambda checked=False, r=reward: self.delete_requested.emit(r))
            
            actions_layout.addWidget(btn_play)
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            
            self.table_rewards.setCellWidget(row, 2, actions_widget)

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
        self.btn_copy_url.setText(self.i18n.get("rewards.obs.copied"))
        self.btn_copy_url.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_copy_btn(original_text))

    def _reset_copy_btn(self, original_text: str):
        self.btn_copy_url.setText(original_text)
        self.btn_copy_url.setEnabled(True)