# frontend/views/command_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, 
                               QLineEdit)
from PySide6.QtCore import Qt, Signal

from frontend.components.controls import ModernButton, ModernSwitch
from frontend.components.blocks import ViewHeader
from frontend.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY
from frontend.utils import get_icon_colored

class CommandView(QWidget):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    status_toggled = Signal(str, bool)
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
        scroll_content.setObjectName("ScrollContent")
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        self.header = ViewHeader(
            title_text=self.i18n.get("command.header.title"),
            subtitle_text=self.i18n.get("command.header.subtitle"),
            icon_name="code.svg",
            icon_color=COLOR_ACCENT
        )
        self.main_layout.addWidget(self.header)

        table_card = QFrame()
        table_card.setProperty("role", "card")
        table_card.setMinimumHeight(400)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(10)

        table_header_layout = QHBoxLayout()
        lbl_table_title = QLabel(self.i18n.get("command.table.title"))
        lbl_table_title.setProperty("role", "h3")
        
        table_header_layout.addWidget(lbl_table_title)
        table_header_layout.addStretch()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(self.i18n.get("command.table.search_placeholder"))
        self.txt_search.setFixedWidth(250)
        self.txt_search.textChanged.connect(self.search_text_changed.emit)
        table_header_layout.addWidget(self.txt_search)

        self.btn_new_alert = ModernButton(self.i18n.get("command.table.btn_new"), role="action_accent")
        self.btn_new_alert.clicked.connect(self.add_requested.emit)
        table_header_layout.addWidget(self.btn_new_alert)

        table_layout.addLayout(table_header_layout)

        self.table = QTableWidget(0, 4)

        col_1 = self.i18n.get("command.table.col_command")
        col_2 = self.i18n.get("command.table.col_aliases")
        col_3 = self.i18n.get("command.table.col_response")
        col_4 = self.i18n.get("command.table.col_actions")
        self.table.setHorizontalHeaderLabels([col_1, col_2, col_3, col_4])
        
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(3, 130)
        
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.table)
        self.main_layout.addWidget(table_card, stretch=1) 

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def populate_table(self, commands: list[dict]):
        self.table.setRowCount(0)
        prefix_regex = self.i18n.get("command.table.regex_prefix")
        
        for cmd in commands:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            cmd_widget = self._create_command_cell(cmd)
            self.table.setCellWidget(row, 0, cmd_widget)
            
            raw_aliases = cmd.get("aliases", "")
            aliases_text = raw_aliases if raw_aliases else "-"
            
            if cmd.get("is_regex"):
                aliases_text = f"{prefix_regex}: {raw_aliases}"
            
            item_aliases = QTableWidgetItem(aliases_text)
            item_aliases.setToolTip(aliases_text)
            item_aliases.setFlags(item_aliases.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_aliases)

            item_response = QTableWidgetItem(cmd["response"])
            item_response.setToolTip(cmd["response"])
            item_response.setFlags(item_response.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item_response)
            
            actions_widget = self._create_actions_cell(cmd)
            self.table.setCellWidget(row, 3, actions_widget)

    def _create_command_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        lbl_status_dot = QLabel("●")
        lbl_status_dot.setProperty("role", "status_dot")
        lbl_status_dot.setProperty("state", "active" if cmd_data.get("is_active") else "inactive")
        layout.addWidget(lbl_status_dot)
        
        lbl_icon = QLabel()
        icon_obj = get_icon_colored("hash.svg", COLOR_TEXT_PRIMARY, 16)
        lbl_icon.setPixmap(icon_obj.pixmap(16, 16))
        
        lbl_trigger = QLabel(cmd_data["trigger"])
        lbl_trigger.setProperty("role", "monospace")
        layout.addWidget(lbl_trigger)
        
        permission = cmd_data.get("permission", "everyone")
        if permission != "everyone":
            lbl_perm = QLabel(permission.upper())
            lbl_perm.setProperty("role", "tag_permission")           
            layout.addWidget(lbl_perm)
        
        layout.addStretch()
        return container

    def _create_actions_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        trigger_name = cmd_data["trigger"]

        sw_status = ModernSwitch()
        sw_status.setChecked(cmd_data.get("is_active", True))
        sw_status.toggled.connect(lambda checked, t=trigger_name: self.status_toggled.emit(t, checked))
        layout.addWidget(sw_status)
        layout.addSpacing(4)

        btn_edit = ModernButton("", role="action_accent")
        btn_edit.setFixedSize(28, 28)
        btn_edit.setIcon(get_icon_colored("edit.svg", "#000000", 16))
        btn_edit.setToolTip(self.i18n.get("command.table.tooltip_edit"))
        btn_edit.clicked.connect(lambda checked=False, t=trigger_name: self.edit_requested.emit(t))
        layout.addWidget(btn_edit)
        
        btn_del = ModernButton("", role="action_danger")
        btn_del.setFixedSize(28, 28)
        btn_del.setIcon(get_icon_colored("trash.svg", "#ef4444", 16))
        btn_del.setToolTip(self.i18n.get("command.table.tooltip_delete"))
        btn_del.clicked.connect(lambda checked=False, t=trigger_name: self.delete_requested.emit(t))
        layout.addWidget(btn_del)
        
        return container