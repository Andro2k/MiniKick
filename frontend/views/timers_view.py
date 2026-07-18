# frontend\views\timers_view.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QHeaderView
from PySide6.QtCore import Qt, Signal
from frontend.widgets import BaseView, ModernTableCard, TableActionCell
from frontend.common.theme import COLOR_RED, COLOR_GREEN

class TimersView(BaseView):
    add_requested = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    status_toggled = Signal(int, bool)
    search_text_changed = Signal(str)

    def __init__(self, i18n):
        super().__init__(i18n=i18n, title_key="timer.header.title", subtitle_key="timer.header.subtitle")
        self._setup_ui()

    def _setup_ui(self):
        col_1 = self.i18n.get("timer.table.col_name")
        col_2 = self.i18n.get("timer.table.col_message")
        col_3 = self.i18n.get("timer.table.col_interval_online")
        col_4 = self.i18n.get("timer.table.col_interval_offline")
        col_5 = self.i18n.get("timer.table.col_chat_lines")
        col_6 = self.i18n.get("timer.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("timer.header.title"),
            headers=[col_1, col_2, col_3, col_4, col_5, col_6],
            search_placeholder=self.i18n.get("timer.table.search_placeholder"),
            add_button_text=self.i18n.get("timer.table.btn_new"),
            add_button_icon="add.svg"
        )
        self.table_card.setup_empty_state(
            title=self.i18n.get("timer.empty.title"),
            desc=self.i18n.get("timer.empty.desc"),
            icon_name="illustration_clock.svg",
            button_text=self.i18n.get("timer.empty.btn"),
            on_button_clicked=self.add_requested.emit
        )
        
        self.table = self.table_card.table
        self.txt_search = self.table_card.txt_search
        self.btn_new_add = self.table_card.btn_add

        self.txt_search.textChanged.connect(self.search_text_changed.emit)
        self.btn_new_add.clicked.connect(self.add_requested.emit)

        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(5, 130)
        
        self.main_layout.addWidget(self.table_card, stretch=1) 

    def populate_table(self, timers: list[dict]):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(timers))
        for row, timer in enumerate(timers):
            self.table.setCellWidget(row, 0, self._create_name_cell(timer))
            self.table.setCellWidget(row, 1, self._create_message_cell(timer))
            self.table.setCellWidget(row, 2, self._create_online_cell(timer))
            self.table.setCellWidget(row, 3, self._create_offline_cell(timer))
            self.table.setCellWidget(row, 4, self._create_lines_cell(timer))
            self.table.setCellWidget(row, 5, self._create_actions_cell(timer))
        self.table.setUpdatesEnabled(True)
        self.table_card.set_empty(len(timers) == 0)

    def _create_name_cell(self, timer_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)       
        lbl_name = QLabel(timer_data["name"])
        lbl_name.setProperty("role", "body")
        layout.addWidget(lbl_name)        
        layout.addStretch()
        return container

    def _create_message_cell(self, timer_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        messages = timer_data.get("messages", [])
        if not messages:
            preview_text = "-"
        else:
            first_msg = messages[0]
            if len(first_msg) > 60:
                first_msg = first_msg[:57] + "..."
            if len(messages) > 1:
                preview_text = f"{first_msg} (+{len(messages)-1})"
            else:
                preview_text = first_msg
                
        lbl_msg = QLabel(preview_text)
        lbl_msg.setProperty("role", "body")
        layout.addWidget(lbl_msg)
        layout.addStretch()
        return container

    @staticmethod
    def _create_centered_label_cell(text: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(text)
        lbl.setProperty("role", "body")
        layout.addWidget(lbl)
        return container

    def _create_online_cell(self, timer_data: dict) -> QWidget:
        online = timer_data.get("interval_online")
        unit_min = self.i18n.get("timer.table.unit_minutes")
        return self._create_centered_label_cell(f"{online} {unit_min}" if online else "-")

    def _create_offline_cell(self, timer_data: dict) -> QWidget:
        offline = timer_data.get("interval_offline")
        unit_min = self.i18n.get("timer.table.unit_minutes")
        return self._create_centered_label_cell(f"{offline} {unit_min}" if offline else "-")

    def _create_lines_cell(self, timer_data: dict) -> QWidget:
        lines = timer_data.get("chat_lines", 0)
        unit_lines = self.i18n.get("timer.table.unit_lines")
        return self._create_centered_label_cell(f"{lines} {unit_lines}" if lines else "-")

    def _create_actions_cell(self, timer_data: dict) -> QWidget:
        timer_id = timer_data["id"]
        cell = TableActionCell()
        
        cell.add_switch(
            checked=timer_data.get("is_active", True),
            callback=lambda checked, tid=timer_id: self.status_toggled.emit(tid, checked)
        )
        
        cell.add_button(
            icon_name="edit.svg", 
            color=COLOR_GREEN, 
            role="action_accent_border", 
            tooltip=self.i18n.get("timer.table.tooltip_edit"),
            callback=lambda checked=False, tid=timer_id: self.edit_requested.emit(tid)
        )
        
        cell.add_button(
            icon_name="trash.svg", 
            color=COLOR_RED, 
            role="action_danger_border", 
            tooltip=self.i18n.get("timer.table.tooltip_delete"),
            callback=lambda checked=False, tid=timer_id: self.delete_requested.emit(tid)
        )
        
        return cell

    def show_add_dialog(self) -> dict | None:
        from frontend.dialogs.timer_dialog import TimerConfigWizard
        dialog = TimerConfigWizard(self.i18n, parent=self)
        if dialog.exec():
            return dialog.get_timer_data()
        return None

    def show_edit_dialog(self, existing_config: dict) -> dict | None:
        from frontend.dialogs.timer_dialog import TimerConfigWizard
        dialog = TimerConfigWizard(self.i18n, parent=self, existing_config=existing_config)
        if dialog.exec():
            return dialog.get_timer_data()
        return None
