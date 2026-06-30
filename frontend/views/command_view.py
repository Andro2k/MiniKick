# frontend\views\command_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                               QTableWidget, QHeaderView, QScrollArea, 
                               QLineEdit)
from PySide6.QtCore import Qt, Signal

from frontend.widgets.controls_component import ModernButton, ModernSwitch
from frontend.widgets.blocks_component import ViewHeader
from frontend.common.theme import COLOR_ACCENT, COLOR_BLACK, COLOR_DANGER
from frontend.common.utils import get_icon_colored

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
        table_layout.setContentsMargins(8, 8, 8, 8)
        table_layout.setSpacing(6)

        table_header_layout = QHBoxLayout()
        lbl_table_title = QLabel(self.i18n.get("command.table.title"))
        lbl_table_title.setProperty("role", "h3")      
        table_header_layout.addWidget(lbl_table_title)
        table_header_layout.addStretch()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(self.i18n.get("command.table.search_placeholder"))
        self.txt_search.textChanged.connect(self.search_text_changed.emit)
        table_header_layout.addWidget(self.txt_search)

        self.btn_new_add = ModernButton(self.i18n.get("command.table.btn_new"), role="action_accent")
        self.btn_new_add.setIcon(get_icon_colored("add.svg", COLOR_BLACK, 16))
        self.btn_new_add.clicked.connect(self.add_requested.emit)
        table_header_layout.addWidget(self.btn_new_add)

        table_layout.addLayout(table_header_layout)

        self.table = QTableWidget(0, 4)

        col_1 = self.i18n.get("command.table.col_command")
        col_2 = self.i18n.get("command.table.col_permission")
        col_3 = self.i18n.get("command.table.col_aliases")
        col_4 = self.i18n.get("command.table.col_actions")
        self.table.setHorizontalHeaderLabels([col_1, col_2, col_3, col_4])
        
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(3, 130)
        
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        table_layout.addWidget(self.table)
        self.main_layout.addWidget(table_card, stretch=1) 

        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def populate_table(self, commands: list[dict]):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)       
        for cmd in commands:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setCellWidget(row, 0, self._create_command_cell(cmd))
            self.table.setCellWidget(row, 1, self._create_permission_cell(cmd))
            self.table.setCellWidget(row, 2, self._create_aliases_cell(cmd))
            self.table.setCellWidget(row, 3, self._create_actions_cell(cmd))
        self.table.setUpdatesEnabled(True)

    def _create_command_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 0, 8, 0)       
        lbl_trigger = QLabel(cmd_data["trigger"])
        lbl_trigger.setProperty("role", "cmd_trigger")
        layout.addWidget(lbl_trigger)        
        layout.addStretch()
        return container

    def _create_permission_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        raw_perm = cmd_data.get("permission", "everyone")
        perm_keys = {
            "everyone": "command.dialog.perm_everyone",
            "subscriber": "command.dialog.perm_subscriber",
            "vip": "command.dialog.perm_vip",
            "moderator": "command.dialog.perm_moderator",
            "broadcaster": "command.dialog.perm_broadcaster"
        }
        i18n_key = perm_keys.get(raw_perm, "command.dialog.perm_everyone")
        translated_text = self.i18n.get(i18n_key) or raw_perm.upper()
        tag = QFrame()
        tag.setFixedHeight(22)
        tag.setProperty("role", "tag_pill")
        tag.setProperty("perm_level", raw_perm)
        tag_layout = QHBoxLayout(tag)
        tag_layout.setContentsMargins(10, 0, 10, 0)
        tag_layout.setSpacing(0)
        lbl_txt = QLabel(translated_text)
        lbl_txt.setProperty("role", "pill_text")
        lbl_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_layout.addWidget(lbl_txt)
        layout.addWidget(tag)
        return container

    def _create_aliases_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        raw_aliases = cmd_data.get("aliases", "").strip()
        is_regex = cmd_data.get("is_regex", False)

        if not raw_aliases:
            lbl_empty = QLabel("-")
            lbl_empty.setProperty("role", "body")
            layout.addWidget(lbl_empty)
            return container

        if is_regex:
            badge_text = (self.i18n.get("command.table.regex_prefix")).upper()
            badge = QFrame()
            badge.setFixedHeight(20)
            badge.setProperty("role", "badge_regex")
            b_layout = QHBoxLayout(badge)
            b_layout.setContentsMargins(2, 2, 2, 2)
            lbl_b = QLabel(badge_text)
            lbl_b.setProperty("role", "badge_regex_text")
            b_layout.addWidget(lbl_b)
            layout.addWidget(badge)
            lbl_text = QLabel(raw_aliases)
            lbl_text.setProperty("role", "monospace")
        else:
            lbl_text = QLabel(raw_aliases)
            lbl_text.setProperty("role", "body")

        layout.addWidget(lbl_text)
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
        btn_edit.setIcon(get_icon_colored("edit.svg", COLOR_BLACK, 16))
        btn_edit.setToolTip(self.i18n.get("command.table.tooltip_edit"))
        btn_edit.clicked.connect(lambda checked=False, t=trigger_name: self.edit_requested.emit(t))
        layout.addWidget(btn_edit)
        
        btn_del = ModernButton("", role="action_danger")
        btn_del.setFixedSize(28, 28)
        btn_del.setIcon(get_icon_colored("trash.svg", COLOR_DANGER, 16))
        btn_del.setToolTip(self.i18n.get("command.table.tooltip_delete"))
        btn_del.clicked.connect(lambda checked=False, t=trigger_name: self.delete_requested.emit(t))
        layout.addWidget(btn_del)
        
        return container