# frontend\views\timers_view.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QHeaderView, QTableWidgetItem, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from frontend.widgets import BaseView, ModernTableCard, TableActionCell, create_badge
from frontend.common.theme import COLOR_RED, COLOR_GREEN, COLOR_NEUTRAL_400

class TimersView(BaseView):
    add_requested = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    status_toggled = Signal(int, bool)
    search_text_changed = Signal(str)

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="timer.header.title", subtitle_key="timer.header.subtitle", parent=parent)
        self._setup_ui()

    def _setup_ui(self):
        col_1 = self.i18n.get("timer.table.col_name")
        col_2 = self.i18n.get("timer.table.col_message")
        col_3 = self.i18n.get("timer.table.col_platforms")
        col_4 = self.i18n.get("timer.table.col_interval_online")
        col_5 = self.i18n.get("timer.table.col_interval_offline")
        col_6 = self.i18n.get("timer.table.col_chat_lines")
        col_7 = self.i18n.get("timer.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("timer.header.title"),
            headers=[col_1, col_2, col_3, col_4, col_5, col_6, col_7],
            search_placeholder=self.i18n.get("timer.table.search_placeholder"),
            add_button_text=self.i18n.get("timer.table.btn_new"),
            add_button_icon="add.svg"
        )
        self.table_card.setup_empty_state(
            title=self.i18n.get("timer.empty.title"),
            desc=self.i18n.get("timer.empty.desc"),
            icon_name="illustration-time.svg",
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
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(6, 130)
        
        self.main_layout.addWidget(self.table_card, stretch=1) 

    def populate_table(self, timers: list[dict]):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(timers))
        for row, timer in enumerate(timers):
            self.table.setItem(row, 0, self._create_name_item(timer))
            self.table.setItem(row, 1, self._create_message_item(timer))
            self.table.setCellWidget(row, 2, self._create_platforms_cell(timer))
            self.table.setItem(row, 3, self._create_online_item(timer))
            self.table.setItem(row, 4, self._create_offline_item(timer))
            self.table.setItem(row, 5, self._create_lines_item(timer))
            self.table.setCellWidget(row, 6, self._create_actions_cell(timer))
        self.table.setUpdatesEnabled(True)
        self.table_card.set_empty(len(timers) == 0)
        self.table_card.set_title_count(self.i18n.get("timer.header.title"), len(timers))

    def _create_table_item(self, text: str, align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        item.setForeground(QColor(COLOR_NEUTRAL_400))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _create_name_item(self, timer_data: dict) -> QTableWidgetItem:
        return self._create_table_item(timer_data["name"])

    def _create_message_item(self, timer_data: dict) -> QTableWidgetItem:
        messages = timer_data.get("messages", [])
        if not messages:
            preview_text = "-"
            tooltip_text = ""
        else:
            first_msg = messages[0]
            if len(messages) > 1:
                preview_text = f"{first_msg} (+{len(messages)-1})"
                tooltip_text = "\n".join(f"- {m}" for m in messages)
            else:
                preview_text = first_msg
                tooltip_text = first_msg
                
        item = self._create_table_item(preview_text)
        if tooltip_text:
            item.setToolTip(tooltip_text)
        return item

    def _create_platforms_cell(self, timer_data: dict) -> QWidget:
        apply_kick = timer_data.get("apply_kick", True)
        apply_twitch = timer_data.get("apply_twitch", True)
        
        if not apply_kick and not apply_twitch:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(8, 0, 8, 0)
            lbl_none = QLabel("-")
            lbl_none.setProperty("role", "body")
            layout.addWidget(lbl_none)
            return container

        if apply_kick and apply_twitch:
            return create_badge(self.i18n.get("timer.table.platform_both"), state="warning")
        elif apply_kick:
            return create_badge("Kick", state="everyone")
        else:
            return create_badge("Twitch", state="plugin")

    def _create_online_item(self, timer_data: dict) -> QTableWidgetItem:
        online = timer_data.get("interval_online")
        unit_min = self.i18n.get("timer.table.unit_minutes")
        return self._create_table_item(f"{online} {unit_min}" if online else "-", Qt.AlignmentFlag.AlignCenter)

    def _create_offline_item(self, timer_data: dict) -> QTableWidgetItem:
        offline = timer_data.get("interval_offline")
        unit_min = self.i18n.get("timer.table.unit_minutes")
        return self._create_table_item(f"{offline} {unit_min}" if offline else "-", Qt.AlignmentFlag.AlignCenter)

    def _create_lines_item(self, timer_data: dict) -> QTableWidgetItem:
        lines = timer_data.get("chat_lines", 0)
        unit_lines = self.i18n.get("timer.table.unit_lines")
        return self._create_table_item(f"{lines} {unit_lines}" if lines else "-", Qt.AlignmentFlag.AlignCenter)

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
