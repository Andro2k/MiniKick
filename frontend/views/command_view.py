# frontend\views\command_view.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QHeaderView
from PySide6.QtCore import Qt, Signal
from frontend.widgets import BaseView, ModernTableCard, TableActionCell, create_badge
from frontend.common.theme import COLOR_RED, COLOR_GREEN, COLOR_TWITCH, COLOR_YOUTUBE, COLOR_TIKTOK
from frontend.common.icons import get_pixmap_colored

class CommandView(BaseView):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    status_toggled = Signal(str, bool)
    search_text_changed = Signal(str)
    view_shown = Signal()

    _PERM_KEYS: dict[str, str] = {
        "everyone":    "command.dialog.perm_everyone",
        "subscriber":  "command.dialog.perm_subscriber",
        "vip":         "command.dialog.perm_vip",
        "moderator":   "command.dialog.perm_moderator",
        "broadcaster": "command.dialog.perm_broadcaster",
    }

    _PERM_RANKS: dict[str, int] = {
        "everyone": 0,
        "subscriber": 1,
        "vip": 2,
        "moderator": 3,
        "broadcaster": 4,
    }

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="command.header.title", subtitle_key="command.header.subtitle", parent=parent)
        self._raw_commands: list[dict] = []
        self._current_sort: tuple[int, str] | None = None
        self._setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def _setup_ui(self):
        col_1 = self.i18n.get("command.table.col_command")
        col_2 = self.i18n.get("command.table.col_type")
        col_3 = self.i18n.get("command.table.col_permission")
        col_4 = self.i18n.get("command.table.col_platforms")
        col_5 = self.i18n.get("command.table.col_aliases")
        col_6 = self.i18n.get("command.table.col_actions")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("command.table.title"),
            headers=[col_1, col_2, col_3, col_4, col_5, col_6],
            search_placeholder=self.i18n.get("command.table.search_placeholder"),
            add_button_text=self.i18n.get("command.table.btn_new"),
            add_button_icon="add.svg"
        )
        self.table_card.setup_empty_state(
            title=self.i18n.get("command.empty.title"),
            desc=self.i18n.get("command.empty.desc"),
            icon_name="illustration-menu.svg",
            button_text=self.i18n.get("command.empty.btn"),
            on_button_clicked=self.add_requested.emit
        )
        self.table_card.setMinimumHeight(400)
        
        self.table = self.table_card.table
        self.txt_search = self.table_card.txt_search
        self.btn_new_add = self.table_card.btn_add

        self.txt_search.textChanged.connect(self._apply_filters)
        self.btn_new_add.clicked.connect(self.add_requested.emit)

        self.filter_header = self.table_card.enable_filter_header()
        
        sort_asc_text = self.i18n.get("command.table.filter_sort_asc")
        sort_desc_text = self.i18n.get("command.table.filter_sort_desc")
        all_text = self.i18n.get("command.table.filter_all")

        type_options = [
            {"id": "custom", "label": self.i18n.get("command.table.type_custom")},
            {"id": "plugin", "label": self.i18n.get("command.table.type_plugin")}
        ]
        self.filter_header.set_column_filter(
            col_idx=1,
            title=col_2,
            options=type_options,
            all_label=all_text,
            sort_asc_label=sort_asc_text,
            sort_desc_label=sort_desc_text
        )

        perm_options = [
            {"id": k, "label": self.i18n.get(v)} for k, v in self._PERM_KEYS.items()
        ]
        self.filter_header.set_column_filter(
            col_idx=2,
            title=col_3,
            options=perm_options,
            all_label=all_text,
            sort_asc_label=sort_asc_text,
            sort_desc_label=sort_desc_text
        )

        self.filter_header.filter_changed.connect(self._apply_filters)
        self.filter_header.sort_requested.connect(self._on_sort_requested)

        self.filter_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.filter_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.filter_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.filter_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.filter_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(5, 130)
        
        self.main_layout.addWidget(self.table_card, stretch=1) 

    def _on_sort_requested(self, col_idx: int, order: str):
        self._current_sort = (col_idx, order)
        self._apply_filters()

    def populate_table(self, commands: list[dict]):
        self._raw_commands = commands or []
        self._apply_filters()

    def _apply_filters(self):
        query = self.txt_search.text().strip().lower() if self.txt_search else ""
        active_filters = self.filter_header.get_active_filters()

        type_active = active_filters.get(1, set())
        perm_active = active_filters.get(2, set())

        filtered: list[dict] = []
        for cmd in self._raw_commands:
            is_plugin = "[PLUGIN_" in cmd.get("response", "")
            cmd_type = "plugin" if is_plugin else "custom"
            if cmd_type not in type_active:
                continue

            raw_perm = cmd.get("permission", "everyone")
            if raw_perm not in perm_active:
                continue
            if query:
                trig = cmd.get("trigger", "").lower()
                resp = cmd.get("response", "").lower()
                alias = cmd.get("aliases", "").lower()
                if query not in trig and query not in resp and query not in alias:
                    continue

            filtered.append(cmd)

        if self._current_sort:
            col_idx, order = self._current_sort
            reverse = (order == "desc")

            def get_sort_key(c: dict):
                if col_idx == 0:
                    return c.get("trigger", "").lower()
                elif col_idx == 1:
                    return "plugin" if "[PLUGIN_" in c.get("response", "") else "custom"
                elif col_idx == 2:
                    p = c.get("permission", "everyone")
                    return self._PERM_RANKS.get(p, 0)
                elif col_idx == 3:
                    return int(c.get("apply_kick", True)) + int(c.get("apply_twitch", True)) + int(c.get("apply_youtube", True)) + int(c.get("apply_tiktok", True))
                elif col_idx == 4:
                    return c.get("aliases", "").lower()
                return 0

            filtered.sort(key=get_sort_key, reverse=reverse)

        self._render_rows(filtered)

    def _render_rows(self, commands: list[dict]):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(commands))
        for row, cmd in enumerate(commands):
            self.table.setCellWidget(row, 0, self._create_command_cell(cmd))
            self.table.setCellWidget(row, 1, self._create_type_cell(cmd))
            self.table.setCellWidget(row, 2, self._create_permission_cell(cmd))
            self.table.setCellWidget(row, 3, self._create_platforms_cell(cmd))
            self.table.setCellWidget(row, 4, self._create_aliases_cell(cmd))
            self.table.setCellWidget(row, 5, self._create_actions_cell(cmd))
        self.table.setUpdatesEnabled(True)
        self.table_card.set_empty(len(commands) == 0 and len(self._raw_commands) == 0)
        self.table_card.set_title_count(self.i18n.get("command.table.title"), len(self._raw_commands))

    def _create_command_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 0, 8, 0)
        lbl_trigger = QLabel(cmd_data["trigger"])
        lbl_trigger.setProperty("role", "body")
        layout.addWidget(lbl_trigger)
        layout.addStretch()
        return container

    def _create_type_cell(self, cmd_data: dict) -> QWidget:
        is_plugin = "[PLUGIN_" in cmd_data.get("response", "")
        type_key = "command.table.type_plugin" if is_plugin else "command.table.type_custom"
        state = "plugin" if is_plugin else "everyone"
        return create_badge(self.i18n.get(type_key), state=state)

    def _create_permission_cell(self, cmd_data: dict) -> QWidget:
        raw_perm = cmd_data.get("permission", "everyone")
        i18n_key = self._PERM_KEYS.get(raw_perm, "command.dialog.perm_everyone")
        return create_badge(self.i18n.get(i18n_key), state=raw_perm)

    def set_connected_platforms(self, connected_platforms: dict[str, bool]):
        self.connected_platforms = connected_platforms or {}
        if self._raw_commands:
            self.populate_table(self._raw_commands)

    def _create_platforms_cell(self, cmd_data: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        connected = getattr(self, "connected_platforms", {})
        has_conn_filter = isinstance(connected, dict) and bool(connected)

        apply_kick = cmd_data.get("apply_kick", True) and (connected.get("kick", False) if has_conn_filter else True)
        apply_twitch = cmd_data.get("apply_twitch", True) and (connected.get("twitch", False) if has_conn_filter else True)
        apply_youtube = cmd_data.get("apply_youtube", True) and (connected.get("youtube", False) if has_conn_filter else True)
        apply_tiktok = cmd_data.get("apply_tiktok", True) and (connected.get("tiktok", False) if has_conn_filter else True)

        platforms = [
            ("brand-kick.svg", COLOR_GREEN, "Kick", apply_kick),
            ("brand-twitch.svg", COLOR_TWITCH, "Twitch", apply_twitch),
            ("brand-youtube.svg", COLOR_YOUTUBE, "YouTube", apply_youtube),
            ("brand-tiktok.svg", COLOR_TIKTOK, "TikTok", apply_tiktok)
        ]

        active_count = 0
        for icon_name, color, name, is_active in platforms:
            if is_active:
                lbl_icon = QLabel()
                lbl_icon.setPixmap(get_pixmap_colored(icon_name, color, 16))
                lbl_icon.setToolTip(name)
                lbl_icon.setFixedSize(18, 18)
                lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(lbl_icon)
                active_count += 1

        if active_count == 0:
            lbl_none = QLabel("-")
            lbl_none.setProperty("role", "body")
            layout.addWidget(lbl_none)

        layout.addStretch()
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
        
        def _on_toggled(checked: bool, t: str = trigger_name):
            for cmd in self._raw_commands:
                if cmd.get("trigger") == t:
                    cmd["is_active"] = checked
                    break
            self.status_toggled.emit(t, checked)

        cell.add_switch(
            checked=cmd_data.get("is_active", True),
            callback=_on_toggled
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

    def show_add_dialog(self, connected_platforms: dict[str, bool] = None) -> dict | None:
        from frontend.dialogs import CommandConfigWizard
        dialog = CommandConfigWizard(self.i18n, parent=self, connected_platforms=connected_platforms)
        if dialog.exec():
            return dialog.get_command_data()
        return None

    def show_edit_dialog(self, existing_config: dict, connected_platforms: dict[str, bool] = None) -> dict | None:
        from frontend.dialogs import CommandConfigWizard
        dialog = CommandConfigWizard(self.i18n, parent=self, existing_config=existing_config, connected_platforms=connected_platforms)
        if dialog.exec():
            return dialog.get_command_data()
        return None
