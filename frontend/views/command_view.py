# frontend\views\command_view.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QHeaderView
from PySide6.QtCore import Qt, Signal
from frontend.widgets.base_view import BaseView
from frontend.widgets.table import ModernTableCard, TableActionCell
from frontend.common.theme import COLOR_RED, COLOR_GREEN

class CommandView(BaseView):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    status_toggled = Signal(str, bool)
    search_text_changed = Signal(str)

    def __init__(self, i18n):
        super().__init__(
            i18n=i18n,
            title_key="command.header.title",
            subtitle_key="command.header.subtitle"
        )
        self._setup_ui()

    def _setup_ui(self):
        col_1 = self.i18n.get("command.table.col_command")
        col_2 = self.i18n.get("command.table.col_permission")
        col_3 = self.i18n.get("command.table.col_aliases")
        col_4 = self.i18n.get("command.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("command.table.title"),
            headers=[col_1, col_2, col_3, col_4],
            search_placeholder=self.i18n.get("command.table.search_placeholder"),
            add_button_text=self.i18n.get("command.table.btn_new"),
            add_button_icon="add.svg"
        )
        self.table_card.setup_empty_state(
            title=self.i18n.get("command.empty.title"),
            desc=self.i18n.get("command.empty.desc"),
            icon_name="illustration_add-files.svg",
            button_text=self.i18n.get("command.empty.btn"),
            on_button_clicked=self.add_requested.emit
        )
        self.table_card.setMinimumHeight(400)
        
        self.table = self.table_card.table
        self.txt_search = self.table_card.txt_search
        self.btn_new_add = self.table_card.btn_add

        self.txt_search.textChanged.connect(self.search_text_changed.emit)
        self.btn_new_add.clicked.connect(self.add_requested.emit)

        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(3, 130)
        
        self.main_layout.addWidget(self.table_card, stretch=1) 

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
        self.table_card.set_empty(len(commands) == 0)

    def _create_command_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 0, 8, 0)       
        lbl_trigger = QLabel(cmd_data["trigger"])
        lbl_trigger.setProperty("role", "body")
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
        translated_text = self.i18n.get(i18n_key) or raw_perm
        tag = QFrame()
        tag.setFixedHeight(22)
        tag.setProperty("role", "badge")
        tag.setProperty("state", raw_perm)
        tag_layout = QHBoxLayout(tag)
        tag_layout.setContentsMargins(5, 0, 5, 0)
        tag_layout.setSpacing(0)
        lbl_txt = QLabel(translated_text)
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
            badge_text = (self.i18n.get("command.table.regex_prefix"))
            badge = QFrame()
            badge.setFixedHeight(20)
            badge.setProperty("role", "badge")
            badge.setProperty("state", "warning")
            b_layout = QHBoxLayout(badge)
            b_layout.setContentsMargins(4, 2, 4, 2)
            lbl_b = QLabel(badge_text)
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
        trigger_name = cmd_data["trigger"]
        cell = TableActionCell()
        
        cell.add_switch(
            checked=cmd_data.get("is_active", True),
            callback=lambda checked, t=trigger_name: self.status_toggled.emit(t, checked)
        )
        
        cell.add_button(
            icon_name="edit.svg", 
            color=COLOR_GREEN, 
            role="action_accent_border", 
            tooltip=self.i18n.get("command.table.tooltip_edit"),
            callback=lambda checked=False, t=trigger_name: self.edit_requested.emit(t)
        )
        
        cell.add_button(
            icon_name="trash.svg", 
            color=COLOR_RED, 
            role="action_danger_border", 
            tooltip=self.i18n.get("command.table.tooltip_delete"),
            callback=lambda checked=False, t=trigger_name: self.delete_requested.emit(t)
        )
        
        return cell

    def show_add_dialog(self) -> dict | None:
        from frontend.dialogs import CommandConfigWizard
        dialog = CommandConfigWizard(self.i18n, parent=self)
        if dialog.exec():
            return dialog.get_command_data()
        return None

    def show_edit_dialog(self, existing_config: dict) -> dict | None:
        from frontend.dialogs import CommandConfigWizard
        dialog = CommandConfigWizard(self.i18n, parent=self, existing_config=existing_config)
        if dialog.exec():
            return dialog.get_command_data()
        return None
