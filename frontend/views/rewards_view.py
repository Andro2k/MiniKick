# frontend\views\rewards_view.py

import os
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView, QApplication
from PySide6.QtCore import QTimer, Qt, Signal, Slot, QSize, QRectF
from PySide6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QPainterPath
from frontend.widgets import BaseView, SettingRow, ModernCard, ModernTableCard, TableActionCell, ModernButton
from frontend.common.theme import COLOR_GREEN, COLOR_NEUTRAL_200, COLOR_NEUTRAL_400, COLOR_RED
from frontend.common import get_pixmap_colored, get_icon_colored

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma"}

def _create_reward_icon(config: dict, filepath: str, is_valid_file: bool = True) -> QIcon:
    target_w, target_h = 48, 32
    
    if not is_valid_file:
        pixmap = QPixmap(target_w, target_h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, target_w, target_h)
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        painter.fillPath(path, QColor("#2d1215"))
        painter.setPen(QColor(COLOR_RED))
        painter.drawPath(path)
        
        icon_pixmap = get_pixmap_colored("alert-triangle.svg", COLOR_RED, 18)
        if not icon_pixmap.isNull():
            x = (target_w - 18) / 2
            y = (target_h - 18) / 2
            painter.drawPixmap(int(x), int(y), icon_pixmap)
        painter.end()
        return QIcon(pixmap)

    ext = os.path.splitext(filepath)[1].lower() if filepath else ""
    is_audio = ext in AUDIO_EXTENSIONS
    
    if is_audio:
        pixmap = QPixmap(target_w, target_h)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, target_w, target_h)
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        painter.fillPath(path, QColor("#1e293b"))
        
        icon_pixmap = get_pixmap_colored("volume.svg", COLOR_GREEN, 18)
        if not icon_pixmap.isNull():
            x = (target_w - 18) / 2
            y = (target_h - 18) / 2
            painter.drawPixmap(int(x), int(y), icon_pixmap)
            
        painter.end()
        return QIcon(pixmap)
        
    thumb_bytes = config.get("thumbnail_bytes") if isinstance(config, dict) else None
    if thumb_bytes:
        img = QImage()
        if img.loadFromData(thumb_bytes):
            scaled = img.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            final_pix = QPixmap(target_w, target_h)
            final_pix.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(final_pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, target_w, target_h), 6, 6)
            painter.setClipPath(path)
            
            x = (target_w - scaled.width()) / 2
            y = (target_h - scaled.height()) / 2
            painter.drawImage(int(x), int(y), scaled)
            painter.end()
            return QIcon(final_pix)
            
    pixmap = QPixmap(target_w, target_h)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, target_w, target_h), 6, 6)
    painter.fillPath(path, QColor("#1e293b"))
    
    icon_pixmap = get_pixmap_colored("movie.svg", COLOR_NEUTRAL_400, 18)
    if not icon_pixmap.isNull():
        x = (target_w - 18) / 2
        y = (target_h - 18) / 2
        painter.drawPixmap(int(x), int(y), icon_pixmap)
    painter.end()
    return QIcon(pixmap)

class RewardsView(BaseView):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    preview_requested = Signal(str)
    refresh_rewards_requested = Signal()

    def __init__(self, i18n, overlay_url="http://localhost:8090/overlay", parent=None):
        super().__init__(i18n=i18n, title_key="rewards.header.title", subtitle_key="rewards.header.subtitle", parent=parent)
        self.overlay_url = overlay_url
        self._setup_ui()

    def _setup_ui(self):
        self._build_obs_card()
        self._build_table_card()

    def _build_obs_card(self):
        obs_card = ModernCard(parent=self)

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
        col_3 = self.i18n.get("rewards.table.col_pos")
        col_4 = self.i18n.get("rewards.table.col_volume")
        col_5 = self.i18n.get("rewards.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("rewards.table.title"),
            headers=[col_1, col_2, col_3, col_4, col_5],
            add_button_text=self.i18n.get("rewards.table.btn_new"),
            add_button_icon="add.svg"
        )
        self.table_card.setup_empty_state(
            title=self.i18n.get("rewards.empty.title"),
            desc=self.i18n.get("rewards.empty.desc"),
            icon_name="illustration-picture.svg",
            button_text=self.i18n.get("rewards.empty.btn"),
            on_button_clicked=self.add_requested.emit
        )
        self.table_card.setMinimumHeight(300)
        
        self.table_rewards = self.table_card.table
        self.table_rewards.setIconSize(QSize(48, 32))
        self.btn_new_rewards = self.table_card.btn_add
        self.btn_new_rewards.clicked.connect(self.add_requested.emit)
        
        self.table_rewards.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_rewards.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_rewards.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_rewards.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_rewards.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table_rewards.setColumnWidth(2, 130)
        self.table_rewards.setColumnWidth(3, 90)
        self.table_rewards.setColumnWidth(4, 140)
        
        self.main_layout.addWidget(self.table_card, stretch=1) 

    def populate_table(self, mappings: dict):
        self.table_rewards.setUpdatesEnabled(False)
        self.table_rewards.setRowCount(0)
        str_unknown = self.i18n.get("rewards.table.unknown_file")
        missing_tag = self.i18n.get("rewards.table.file_not_found_tag")
        missing_tooltip_base = self.i18n.get("rewards.table.file_not_found_tooltip")
        missing_count = 0
        
        for reward, config in mappings.items():
            row = self.table_rewards.rowCount()
            self.table_rewards.insertRow(row)
            
            filepath = config if isinstance(config, str) else config.get("filepath", str_unknown)
            conf_dict = config if isinstance(config, dict) else {}
            
            is_valid_file = bool(filepath) and filepath != str_unknown and os.path.exists(filepath) and os.path.isfile(filepath)
            if not is_valid_file:
                missing_count += 1
            
            item_reward = QTableWidgetItem(reward)
            item_reward.setIcon(_create_reward_icon(conf_dict, filepath, is_valid_file=is_valid_file))
            item_reward.setFlags(item_reward.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not is_valid_file:
                item_reward.setToolTip(f"{reward}\n⚠️ {missing_tooltip_base}")
            self.table_rewards.setItem(row, 0, item_reward)
            
            file_basename = os.path.basename(filepath) if filepath else str_unknown
            if not is_valid_file:
                item_file = QTableWidgetItem(f"{file_basename} ({missing_tag})")
                item_file.setIcon(get_icon_colored("alert-triangle.svg", COLOR_RED, 16))
                item_file.setForeground(QColor(COLOR_RED))
                item_file.setToolTip(f"⚠️ {missing_tooltip_base}:\n{filepath}")
            else:
                item_file = QTableWidgetItem(file_basename)
                item_file.setToolTip(filepath)
            item_file.setFlags(item_file.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 1, item_file)
            
            is_random = conf_dict.get("is_random_pos", False)
            if is_random:
                pos_str = self.i18n.get("rewards.table.pos_random")
            else:
                pos_x = conf_dict.get("pos_x", 0)
                pos_y = conf_dict.get("pos_y", 0)
                pos_str = f"X: {pos_x}, Y: {pos_y}"
            item_pos = QTableWidgetItem(pos_str)
            item_pos.setFlags(item_pos.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 2, item_pos)
            
            vol = conf_dict.get("volume", 1.0)
            vol_pct = int(round(vol * 100)) if isinstance(vol, (int, float)) else 100
            item_vol = QTableWidgetItem(f"{vol_pct}%")
            item_vol.setFlags(item_vol.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 3, item_vol)
            
            cell = TableActionCell()
            play_tooltip = self.i18n.get("rewards.table.tooltip_play") if is_valid_file else self.i18n.get("rewards.table.tooltip_play_missing")
            cell.add_button(
                icon_name="player-play.svg", 
                color=COLOR_NEUTRAL_200 if is_valid_file else COLOR_RED, 
                role="action_neutral_border" if is_valid_file else "action_danger_border", 
                tooltip=play_tooltip, 
                callback=lambda checked=False, r=reward: self.preview_requested.emit(r)
            )
            cell.add_button(
                icon_name="edit.svg", 
                color=COLOR_GREEN, 
                role="action_accent_border", 
                tooltip=self.i18n.get("rewards.table.tooltip_edit"), 
                callback=lambda checked=False, r=reward: self.edit_requested.emit(r)
            )
            cell.add_button(
                icon_name="trash.svg", 
                color=COLOR_RED, 
                role="action_danger_border", 
                tooltip=self.i18n.get("rewards.table.tooltip_delete"), 
                callback=lambda checked=False, r=reward: self.delete_requested.emit(r)
            )
            
            self.table_rewards.setCellWidget(row, 4, cell)

        self.table_rewards.setUpdatesEnabled(True)
        self.table_card.set_empty(len(mappings) == 0)

        if hasattr(self.table_card, "lbl_title") and self.table_card.lbl_title:
            title_base = self.i18n.get("rewards.table.title")
            total_count = len(mappings)
            if missing_count > 0:
                warning_label = self.i18n.get("rewards.table.missing_files_warning")
                self.table_card.lbl_title.setText(f"{title_base} ({total_count}) • {missing_count} {warning_label}")
            else:
                self.table_card.lbl_title.setText(f"{title_base} ({total_count})")

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

    def show_add_dialog(self, available_rewards: list, rewards_details_map: dict = None) -> tuple[str, dict] | None:
        from frontend.dialogs.rewards_dialog import RewardsConfigWizard
        self._active_dialog = RewardsConfigWizard(
            self.i18n, 
            parent=self, 
            rewards_list=available_rewards,
            rewards_details_map=rewards_details_map
        )
        try:
            if self._active_dialog.exec():
                return self._active_dialog.get_config_data()
        finally:
            self._active_dialog = None
        return None

    def show_edit_dialog(self, available_rewards: list, existing_config: dict, existing_reward: str, rewards_details_map: dict = None) -> tuple[str, dict] | None:
        from frontend.dialogs.rewards_dialog import RewardsConfigWizard
        self._active_dialog = RewardsConfigWizard(
            self.i18n, 
            parent=self, 
            rewards_list=available_rewards, 
            rewards_details_map=rewards_details_map,
            existing_config=existing_config, 
            existing_reward=existing_reward
        )
        try:
            if self._active_dialog.exec():
                return self._active_dialog.get_config_data()
        finally:
            self._active_dialog = None
        return None

    def update_active_dialog_rewards(self, available_rewards: list):
        if hasattr(self, '_active_dialog') and self._active_dialog:
            self._active_dialog.update_rewards(available_rewards)
