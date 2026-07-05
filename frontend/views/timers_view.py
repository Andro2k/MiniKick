# frontend/views/timers_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                               QTableWidget, QHeaderView, QScrollArea, 
                               QLineEdit)
from PySide6.QtCore import Qt, Signal

from frontend.widgets.controls_component import ModernButton, ModernSwitch
from frontend.widgets.blocks_component import ViewHeader
from frontend.common.theme import COLOR_BLACK, COLOR_DANGER, COLOR_TEXT_PRIMARY, COLOR_ACCENT
from frontend.common.utils import get_icon_colored

class TimersView(QWidget):
    add_requested = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    status_toggled = Signal(int, bool)
    search_text_changed = Signal(str)

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
            title_text=self.i18n.get("timer.header.title"),
            subtitle_text=self.i18n.get("timer.header.subtitle"),
            icon_name="clock.svg",
            icon_color=COLOR_TEXT_PRIMARY
        )
        self.main_layout.addWidget(self.header)

        table_card = QFrame()
        table_card.setProperty("role", "card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(8, 8, 8, 8)
        table_layout.setSpacing(6)

        table_header_layout = QHBoxLayout()
        lbl_table_title = QLabel(self.i18n.get("timer.header.title"))
        lbl_table_title.setProperty("role", "h3")      
        table_header_layout.addWidget(lbl_table_title)
        table_header_layout.addStretch()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(self.i18n.get("timer.table.search_placeholder"))
        self.txt_search.textChanged.connect(self.search_text_changed.emit)
        table_header_layout.addWidget(self.txt_search)

        self.btn_new_add = ModernButton(self.i18n.get("timer.table.btn_new"), role="action_accent")
        self.btn_new_add.setIcon(get_icon_colored("add.svg", COLOR_BLACK, 16))
        self.btn_new_add.clicked.connect(self.add_requested.emit)
        table_header_layout.addWidget(self.btn_new_add)

        table_layout.addLayout(table_header_layout)

        self.table = QTableWidget(0, 6)

        col_1 = self.i18n.get("timer.table.col_name")
        col_2 = self.i18n.get("timer.table.col_message")
        col_3 = self.i18n.get("timer.table.col_interval_online")
        col_4 = self.i18n.get("timer.table.col_interval_offline")
        col_5 = self.i18n.get("timer.table.col_chat_lines")
        col_6 = self.i18n.get("timer.table.col_actions")
        self.table.setHorizontalHeaderLabels([col_1, col_2, col_3, col_4, col_5, col_6])
        
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(5, 130)
        
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        table_layout.addWidget(self.table)
        self.main_layout.addWidget(table_card, stretch=1) 

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def populate_table(self, timers: list[dict]):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)       
        for timer in timers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setCellWidget(row, 0, self._create_name_cell(timer))
            self.table.setCellWidget(row, 1, self._create_message_cell(timer))
            self.table.setCellWidget(row, 2, self._create_online_cell(timer))
            self.table.setCellWidget(row, 3, self._create_offline_cell(timer))
            self.table.setCellWidget(row, 4, self._create_lines_cell(timer))
            self.table.setCellWidget(row, 5, self._create_actions_cell(timer))
        self.table.setUpdatesEnabled(True)

    def _create_name_cell(self, timer_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)       
        lbl_name = QLabel(timer_data["name"])
        lbl_name.setProperty("role", "h3")
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

    def _create_online_cell(self, timer_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        online = timer_data.get("interval_online")
        unit_min = self.i18n.get("timer.table.unit_minutes")
        txt = f"{online} {unit_min}" if online else "-"
        
        lbl = QLabel(txt)
        lbl.setProperty("role", "body")
        layout.addWidget(lbl)
        return container

    def _create_offline_cell(self, timer_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        offline = timer_data.get("interval_offline")
        unit_min = self.i18n.get("timer.table.unit_minutes")
        txt = f"{offline} {unit_min}" if offline else "-"
        
        lbl = QLabel(txt)
        lbl.setProperty("role", "body")
        layout.addWidget(lbl)
        return container

    def _create_lines_cell(self, timer_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lines = timer_data.get("chat_lines", 0)
        unit_lines = self.i18n.get("timer.table.unit_lines")
        txt = f"{lines} {unit_lines}" if lines else "-"
        
        lbl = QLabel(txt)
        lbl.setProperty("role", "body")
        layout.addWidget(lbl)
        return container

    def _create_actions_cell(self, timer_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        timer_id = timer_data["id"]

        sw_status = ModernSwitch()
        sw_status.setChecked(timer_data.get("is_active", True))
        sw_status.toggled.connect(lambda checked, tid=timer_id: self.status_toggled.emit(tid, checked))
        layout.addWidget(sw_status)
        layout.addSpacing(4)

        btn_edit = ModernButton("", role="action_accent_border")
        btn_edit.setFixedSize(28, 28)
        btn_edit.setIcon(get_icon_colored("edit.svg", COLOR_ACCENT, 16))
        btn_edit.setToolTip(self.i18n.get("timer.table.tooltip_edit"))
        btn_edit.clicked.connect(lambda checked=False, tid=timer_id: self.edit_requested.emit(tid))
        layout.addWidget(btn_edit)
        
        btn_del = ModernButton("", role="action_danger_border")
        btn_del.setFixedSize(28, 28)
        btn_del.setIcon(get_icon_colored("trash.svg", COLOR_DANGER, 16))
        btn_del.setToolTip(self.i18n.get("timer.table.tooltip_delete"))
        btn_del.clicked.connect(lambda checked=False, tid=timer_id: self.delete_requested.emit(tid))
        layout.addWidget(btn_del)
        
        return container
