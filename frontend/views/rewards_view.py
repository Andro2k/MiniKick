# frontend\views\rewards_view.py

import os
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView, QApplication
from PySide6.QtCore import QTimer, Qt, Signal, Slot, QSize, QRectF
from PySide6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QPainterPath
from frontend.widgets import BaseView, SettingRow, ModernCard, ModernTableCard, TableActionCell, ModernButton
from frontend.common import (
    COLOR_GREEN, COLOR_NEUTRAL_200, COLOR_NEUTRAL_400, COLOR_RED, COLOR_TWITCH, COLOR_AMBER,
    get_pixmap_colored, get_icon_colored
)

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
        self._raw_mappings: dict = {}
        self._current_sort: tuple[int, str] | None = None
        self.connected_platforms: dict[str, bool] = {"kick": True, "twitch": True}
        self.remote_rewards_map: dict = {}
        self.remote_loaded: dict[str, bool] = {"kick": False, "twitch": False}
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
        col_0 = self.i18n.get("rewards.table.col_reward")
        col_plat = self.i18n.get("rewards.table.col_platform")
        col_cost = self.i18n.get("rewards.table.col_cost")
        col_file = self.i18n.get("rewards.table.col_file")
        col_pos = self.i18n.get("rewards.table.col_pos")
        col_vol = self.i18n.get("rewards.table.col_volume")
        col_actions = self.i18n.get("rewards.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("rewards.table.title"),
            headers=[col_0, col_plat, col_cost, col_file, col_pos, col_vol, col_actions],
            search_placeholder=self.i18n.get("rewards.table.search_placeholder"),
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
        
        self.txt_search = self.table_card.txt_search
        if self.txt_search:
            self.txt_search.textChanged.connect(self._apply_filters)

        self.filter_header = self.table_card.enable_filter_header()
        sort_asc_text = self.i18n.get("rewards.table.filter_sort_asc")
        sort_desc_text = self.i18n.get("rewards.table.filter_sort_desc")
        all_text = self.i18n.get("rewards.table.filter_all")

        self.filter_header.set_column_filter(
            col_idx=0,
            title=col_0,
            options=None,
            sort_asc_label=sort_asc_text,
            sort_desc_label=sort_desc_text
        )

        plat_options = [
            {"id": "kick", "label": "Kick"},
            {"id": "twitch", "label": "Twitch"}
        ]
        self.filter_header.set_column_filter(
            col_idx=1,
            title=col_plat,
            options=plat_options,
            all_label=all_text,
            sort_asc_label=sort_asc_text,
            sort_desc_label=sort_desc_text
        )

        self.filter_header.set_column_filter(
            col_idx=2,
            title=col_cost,
            options=None,
            sort_asc_label=self.i18n.get("rewards.table.filter_cost_asc"),
            sort_desc_label=self.i18n.get("rewards.table.filter_cost_desc")
        )

        self.filter_header.filter_changed.connect(self._apply_filters)
        self.filter_header.sort_requested.connect(self._on_sort_requested)

        self.filter_header.setMinimumSectionSize(80)
        self.filter_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.filter_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.filter_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.table_rewards.setColumnWidth(0, 180)
        self.table_rewards.setColumnWidth(1, 115)
        self.table_rewards.setColumnWidth(2, 95)
        self.table_rewards.setColumnWidth(4, 115)
        self.table_rewards.setColumnWidth(5, 85)
        self.table_rewards.setColumnWidth(6, 140)
        
        self.main_layout.addWidget(self.table_card, stretch=1) 

    def _on_sort_requested(self, col_idx: int, order: str):
        self._current_sort = (col_idx, order)
        self._apply_filters()

    def populate_table(self, mappings: dict, remote_rewards_map: dict = None, connected_platforms: dict = None, remote_loaded: dict = None):
        self._raw_mappings = mappings or {}
        if remote_rewards_map is not None:
            self.remote_rewards_map = remote_rewards_map
        if connected_platforms is not None:
            self.connected_platforms = connected_platforms
        if remote_loaded is not None:
            self.remote_loaded = remote_loaded
        self._apply_filters()

    def set_connected_platforms(self, connected_platforms: dict):
        self.connected_platforms = connected_platforms or {}
        self._apply_filters()

    def _apply_filters(self):
        query = self.txt_search.text().strip().lower() if self.txt_search else ""
        active_filters = self.filter_header.get_active_filters() if hasattr(self, 'filter_header') and self.filter_header else {}
        plat_active = active_filters.get(1, set())

        filtered: list[tuple[str, dict]] = []
        for reward, config in self._raw_mappings.items():
            conf_dict = config if isinstance(config, dict) else {}
            plat = conf_dict.get("platform", "kick").lower()
            if plat_active and plat not in plat_active:
                continue

            if query:
                filepath = config if isinstance(config, str) else conf_dict.get("filepath", "")
                cost_str = str(conf_dict.get("cost", 0))
                if (query not in reward.lower() and 
                    query not in filepath.lower() and 
                    query not in plat and 
                    query not in cost_str):
                    continue

            filtered.append((reward, conf_dict))

        if self._current_sort:
            col_idx, order = self._current_sort
            reverse = (order == "desc")

            def get_sort_key(item: tuple[str, dict]):
                name, conf = item
                if col_idx == 0:
                    return name.lower()
                elif col_idx == 1:
                    return conf.get("platform", "kick").lower()
                elif col_idx == 2:
                    try:
                        return int(conf.get("cost", 0))
                    except (ValueError, TypeError):
                        return 0
                elif col_idx == 3:
                    fp = conf.get("filepath", "")
                    return os.path.basename(fp).lower()
                elif col_idx == 4:
                    return int(conf.get("is_random_pos", False))
                elif col_idx == 5:
                    try:
                        return float(conf.get("volume", 1.0))
                    except (ValueError, TypeError):
                        return 1.0
                return name.lower()

            filtered.sort(key=get_sort_key, reverse=reverse)

        self._render_rows(filtered)

    def _render_rows(self, items: list[tuple[str, dict]]):
        self.table_rewards.setUpdatesEnabled(False)
        self.table_rewards.setRowCount(0)
        str_unknown = self.i18n.get("rewards.table.unknown_file")
        missing_tag = self.i18n.get("rewards.table.file_not_found_tag")
        missing_tooltip_base = self.i18n.get("rewards.table.file_not_found_tooltip")
        missing_count = 0
        
        for reward, conf_dict in items:
            row = self.table_rewards.rowCount()
            self.table_rewards.insertRow(row)
            
            filepath = conf_dict.get("filepath", str_unknown)
            
            is_valid_file = bool(filepath) and filepath != str_unknown and os.path.exists(filepath) and os.path.isfile(filepath)
            if not is_valid_file:
                missing_count += 1
            
            item_reward = QTableWidgetItem(reward)
            item_reward.setIcon(_create_reward_icon(conf_dict, filepath, is_valid_file=is_valid_file))
            item_reward.setFlags(item_reward.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not is_valid_file:
                item_reward.setToolTip(f"{reward}\n⚠️ {missing_tooltip_base}")
            self.table_rewards.setItem(row, 0, item_reward)
            
            plat = conf_dict.get("platform", "kick")
            is_twitch = plat.lower() == "twitch"
            plat_name = "Twitch" if is_twitch else "Kick"
            plat_color = COLOR_TWITCH if is_twitch else COLOR_GREEN
            icon_name = "brand-twitch.svg" if is_twitch else "brand-kick.svg"

            is_plat_connected = self.connected_platforms.get(plat.lower(), False)
            is_remote_loaded = self.remote_loaded.get(plat.lower(), False)
            has_remote_id = bool(conf_dict.get("id"))
            exists_remotely = (reward in self.remote_rewards_map and self.remote_rewards_map[reward].get("platform", "").lower() == plat.lower())

            if not is_plat_connected:
                offline_tag = self.i18n.get("rewards.table.status_offline_tag")
                item_plat = QTableWidgetItem(f"{plat_name} ({offline_tag})")
                item_plat.setIcon(get_icon_colored(icon_name, "#6E7681", 16))
                item_plat.setForeground(QColor("#6E7681"))
                item_plat.setToolTip(self.i18n.get("rewards.table.status_offline_tooltip").replace("{platform}", plat_name))
            elif is_remote_loaded and not exists_remotely and has_remote_id:
                unlinked_tag = self.i18n.get("rewards.table.status_unlinked_tag")
                item_plat = QTableWidgetItem(f"{plat_name} ({unlinked_tag})")
                item_plat.setIcon(get_icon_colored("alert-triangle.svg", COLOR_AMBER, 16))
                item_plat.setForeground(QColor(COLOR_AMBER))
                item_plat.setToolTip(self.i18n.get("rewards.table.status_unlinked_tooltip").replace("{platform}", plat_name))
            else:
                item_plat = QTableWidgetItem(plat_name)
                item_plat.setIcon(get_icon_colored(icon_name, plat_color, 16))
                item_plat.setForeground(QColor(plat_color))
            
            item_plat.setFlags(item_plat.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 1, item_plat)

            cost_val = conf_dict.get("cost", 0)
            try:
                cost_num = int(cost_val)
            except (ValueError, TypeError):
                cost_num = 0
            cost_str = self.i18n.get("rewards.table.pts_suffix").replace("{cost}", f"{cost_num:,}")
            item_cost = QTableWidgetItem(cost_str)
            item_cost.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_cost.setFlags(item_cost.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 2, item_cost)

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
            self.table_rewards.setItem(row, 3, item_file)
            
            is_random = conf_dict.get("is_random_pos", False)
            if is_random:
                pos_str = self.i18n.get("rewards.table.pos_random")
            else:
                pos_x = conf_dict.get("pos_x", 0)
                pos_y = conf_dict.get("pos_y", 0)
                pos_str = f"X: {pos_x}, Y: {pos_y}"
            item_pos = QTableWidgetItem(pos_str)
            item_pos.setFlags(item_pos.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 4, item_pos)
            
            vol = conf_dict.get("volume", 1.0)
            vol_pct = int(round(vol * 100)) if isinstance(vol, (int, float)) else 100
            item_vol = QTableWidgetItem(f"{vol_pct}%")
            item_vol.setFlags(item_vol.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_rewards.setItem(row, 5, item_vol)
            
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
            
            self.table_rewards.setCellWidget(row, 6, cell)

        self.table_rewards.setUpdatesEnabled(True)
        total_mappings_count = len(self._raw_mappings)
        self.table_card.set_empty(len(items) == 0 and total_mappings_count == 0)

        if hasattr(self.table_card, "lbl_title") and self.table_card.lbl_title:
            title_base = self.i18n.get("rewards.table.title")
            if missing_count > 0:
                warning_label = self.i18n.get("rewards.table.missing_files_warning")
                self.table_card.lbl_title.setText(f"{title_base} ({total_mappings_count}) • {missing_count} {warning_label}")
            else:
                self.table_card.lbl_title.setText(f"{title_base} ({total_mappings_count})")

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

    def show_add_dialog(self, available_rewards: list, rewards_details_map: dict = None, kick_authenticated: bool = True, twitch_authenticated: bool = True) -> tuple[str, dict] | None:
        from frontend.dialogs import RewardsConfigWizard
        self._active_dialog = RewardsConfigWizard(
            self.i18n, 
            parent=self, 
            rewards_list=available_rewards,
            rewards_details_map=rewards_details_map,
            kick_authenticated=kick_authenticated,
            twitch_authenticated=twitch_authenticated
        )
        try:
            if self._active_dialog.exec():
                return self._active_dialog.get_config_data()
        finally:
            self._active_dialog = None
        return None

    def show_edit_dialog(self, available_rewards: list, existing_config: dict, existing_reward: str, rewards_details_map: dict = None, kick_authenticated: bool = True, twitch_authenticated: bool = True) -> tuple[str, dict] | None:
        from frontend.dialogs import RewardsConfigWizard
        self._active_dialog = RewardsConfigWizard(
            self.i18n, 
            parent=self, 
            rewards_list=available_rewards, 
            rewards_details_map=rewards_details_map,
            existing_config=existing_config, 
            existing_reward=existing_reward,
            kick_authenticated=kick_authenticated,
            twitch_authenticated=twitch_authenticated
        )
        try:
            if self._active_dialog.exec():
                return self._active_dialog.get_config_data()
        finally:
            self._active_dialog = None
        return None

    def update_active_dialog_rewards(self, available_rewards: list, rewards_details_map: dict = None):
        if hasattr(self, '_active_dialog') and self._active_dialog:
            self._active_dialog.update_rewards(available_rewards, rewards_details_map)
