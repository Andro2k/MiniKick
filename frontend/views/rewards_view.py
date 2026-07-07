# frontend\views\rewards_view.py

import os
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView, QApplication
from PySide6.QtCore import QTimer, Qt, Signal, Slot

from frontend.widgets.base_view import BaseView
from frontend.widgets.blocks_component import SettingRow, ModernCard
from frontend.widgets.table_component import ModernTableCard, TableActionCell
from frontend.widgets.controls_component import ModernButton
from frontend.common.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_DANGER
from frontend.common.utils import get_icon_colored

class RewardsView(BaseView):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    preview_requested = Signal(str)
    refresh_rewards_requested = Signal()

    def __init__(self, i18n, overlay_url="http://localhost:8090/overlay"):
        super().__init__(
            i18n=i18n,
            title_key="rewards.header.title",
            subtitle_key="rewards.header.subtitle",
            icon_name="layout-dashboard.svg", 
            icon_color=COLOR_TEXT_PRIMARY
        )
        self.overlay_url = overlay_url
        self._setup_ui()

    def _setup_ui(self):
        self._build_obs_card()
        self._build_table_card()

    def _build_obs_card(self):
        obs_card = ModernCard()

        self.btn_copy_url = ModernButton(self.i18n.get("common.buttons.copy"), role="action_neutral_border")
        self.btn_copy_url.clicked.connect(self._copy_obs_url)
        
        obs_row = SettingRow(
            icon_name="link.svg",
            title_text=self.i18n.get("rewards.obs.title"),
            desc_text=self.i18n.get("rewards.obs.desc"),
            right_widget=self.btn_copy_url
        )
        
        obs_card.addWidget(obs_row)
        self.main_layout.addWidget(obs_card)

    def _build_table_card(self):
        col_1 = self.i18n.get("rewards.table.col_reward")
        col_2 = self.i18n.get("rewards.table.col_file")
        col_3 = self.i18n.get("rewards.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("rewards.table.title"),
            headers=[col_1, col_2, col_3],
            add_button_text=self.i18n.get("rewards.table.btn_new"),
            add_button_icon="add.svg"
        )
        self.table_card.setMinimumHeight(300)
        
        self.table_rewards = self.table_card.table
        self.btn_new_rewards = self.table_card.btn_add

        self.btn_new_rewards.clicked.connect(self.add_requested.emit)
        
        self.table_rewards.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_rewards.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_rewards.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_rewards.setColumnWidth(2, 140) 
        
        self.main_layout.addWidget(self.table_card, stretch=1) 

    def populate_table(self, mappings: dict):
        self.table_rewards.setUpdatesEnabled(False)
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
            
            cell = TableActionCell()
            cell.add_button(
                icon_name="play.svg", 
                color=COLOR_TEXT_PRIMARY, 
                role="action_neutral_border", 
                tooltip=self.i18n.get("rewards.table.tooltip_play"), 
                callback=lambda checked=False, r=reward: self.preview_requested.emit(r)
            )
            cell.add_button(
                icon_name="edit.svg", 
                color=COLOR_ACCENT, 
                role="action_accent_border", 
                tooltip=self.i18n.get("rewards.table.tooltip_edit"), 
                callback=lambda checked=False, r=reward: self.edit_requested.emit(r)
            )
            cell.add_button(
                icon_name="trash.svg", 
                color=COLOR_DANGER, 
                role="action_danger_border", 
                tooltip=self.i18n.get("rewards.table.tooltip_delete"), 
                callback=lambda checked=False, r=reward: self.delete_requested.emit(r)
            )
            
            self.table_rewards.setCellWidget(row, 2, cell)

        self.table_rewards.setUpdatesEnabled(True)

    @Slot()
    def _copy_obs_url(self):
        QApplication.clipboard().setText(self.overlay_url)
        original_text = self.btn_copy_url.text()
        self.btn_copy_url.setText(self.i18n.get("rewards.obs.copied"))
        self.btn_copy_url.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_copy_btn(original_text))

    def _reset_copy_btn(self, original_text: str):
        self.btn_copy_url.setText(original_text)
        self.btn_copy_url.setEnabled(True)