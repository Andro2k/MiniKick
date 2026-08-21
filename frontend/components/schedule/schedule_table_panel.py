# frontend\components\schedule\schedule_table_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal
from frontend.widgets import ModernTableCard
from frontend.widgets.table import TableActionCell
from frontend.dialogs.base_dialog import ModernConfirmDialog
from frontend.common.theme import COLOR_GREEN, COLOR_RED

class ScheduleTablePanel(QWidget):
    new_schedule_clicked = Signal()
    edit_schedule_clicked = Signal(object)
    delete_schedule_requested = Signal(int)
    toggle_schedule_requested = Signal(int, bool)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.schedules_data = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        col_1 = self.i18n.get("stream_info.table.col_name")
        col_2 = self.i18n.get("stream_info.table.col_date")
        col_3 = self.i18n.get("stream_info.table.col_time")
        col_4 = self.i18n.get("stream_info.table.col_platform")
        col_5 = self.i18n.get("stream_info.table.col_title")
        col_6 = self.i18n.get("stream_info.table.col_category")
        col_7 = self.i18n.get("stream_info.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("stream_info.schedule_section.title"),
            headers=[col_1, col_2, col_3, col_4, col_5, col_6, col_7],
            search_placeholder=self.i18n.get("stream_info.table.search_placeholder"),
            add_button_text=self.i18n.get("stream_info.schedule_section.btn_new"),
            add_button_icon="add.svg",
            parent=self
        )
        self.table_card.setup_empty_state(
            title=self.i18n.get("stream_info.empty.title"),
            desc=self.i18n.get("stream_info.empty.desc"),
            icon_name="illustration-stream.svg",
            button_text=self.i18n.get("stream_info.empty.btn"),
            on_button_clicked=self.new_schedule_clicked.emit
        )

        self.table = self.table_card.table
        if self.table_card.btn_add:
            self.table_card.btn_add.clicked.connect(self.new_schedule_clicked.emit)

        if self.table_card.txt_search:
            self.table_card.txt_search.textChanged.connect(self._on_search_text_changed)

        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 130)

        main_layout.addWidget(self.table_card)

    def _on_search_text_changed(self, _text: str):
        self._populate_table()

    def set_schedules(self, schedules: list[dict]):
        self.schedules_data = schedules or []
        self._populate_table()

    def _populate_table(self):
        query = self.table_card.txt_search.text().strip().lower() if self.table_card.txt_search else ""

        filtered: list[dict] = []
        for sched in self.schedules_data:
            if query:
                name = str(sched.get("name", "")).lower()
                title = str(sched.get("title", "")).lower()
                date_str = str(sched.get("date_str", "")).lower()
                kick_cat = str(sched.get("kick_category_name", "")).lower()
                twitch_cat = str(sched.get("twitch_category_name", "")).lower()
                platform = str(sched.get("target_platform", "")).lower()
                if (query not in name and query not in title and query not in date_str
                        and query not in kick_cat and query not in twitch_cat and query not in platform):
                    continue
            filtered.append(sched)

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(filtered))
        for row, sched in enumerate(filtered):
            self.table.setItem(row, 0, self._create_item(sched.get("name", "")))
            self.table.setItem(row, 1, self._create_item(sched.get("date_str", "")))
            self.table.setItem(row, 2, self._create_item(sched.get("time_str", "")))
            self.table.setItem(row, 3, self._create_platform_item(sched.get("target_platform", "all")))
            self.table.setItem(row, 4, self._create_item(sched.get("title", "")))

            cat_display = sched.get("kick_category_name") or sched.get("twitch_category_name") or "-"
            self.table.setItem(row, 5, self._create_item(cat_display))

            action_cell = self._create_actions_cell(sched)
            self.table.setCellWidget(row, 6, action_cell)

        self.table.setUpdatesEnabled(True)
        self.table_card.set_empty(len(filtered) == 0 and len(self.schedules_data) == 0)

        if hasattr(self.table_card, "lbl_title") and self.table_card.lbl_title:
            title_base = self.i18n.get("stream_info.schedule_section.title")
            total_count = len(self.schedules_data)
            self.table_card.lbl_title.setText(f"{title_base} ({total_count})")

    def _create_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(str(text))
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def _create_platform_item(self, platform_str: str) -> QTableWidgetItem:
        display = {
            "all": self.i18n.get("stream_info.platforms.both"),
            "kick": "Kick",
            "twitch": "Twitch"
        }.get(platform_str, platform_str.capitalize())
        return self._create_item(display)

    def _create_actions_cell(self, sched: dict) -> TableActionCell:
        sched_id = sched.get("id")
        cell = TableActionCell(parent=self.table)

        cell.add_switch(
            checked=sched.get("is_active", True),
            callback=lambda checked, s_id=sched_id: self.toggle_schedule_requested.emit(s_id, checked)
        )

        cell.add_button(
            icon_name="edit.svg",
            color=COLOR_GREEN,
            role="action_accent_border",
            tooltip=self.i18n.get("stream_info.schedule_dialog.title_edit"),
            callback=lambda _, s=sched: self.edit_schedule_clicked.emit(s)
        )

        cell.add_button(
            icon_name="trash.svg",
            color=COLOR_RED,
            role="action_danger_border",
            tooltip=self.i18n.get("stream_info.confirm_delete.title"),
            callback=lambda _, s_id=sched_id: self._confirm_delete_schedule(s_id)
        )

        return cell

    def _confirm_delete_schedule(self, schedule_id: int):
        dialog = ModernConfirmDialog(
            self.i18n,
            parent=self,
            title_text=self.i18n.get("stream_info.confirm_delete.title"),
            body_text=self.i18n.get("stream_info.confirm_delete.desc")
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.delete_schedule_requested.emit(schedule_id)
