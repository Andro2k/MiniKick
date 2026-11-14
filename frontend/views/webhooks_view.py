# frontend\views\webhooks_view.py

from PySide6.QtWidgets import QHeaderView, QTableWidgetItem
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from frontend.views.base_view import BaseView
from frontend.widgets import ModernTableCard, TableActionCell, create_badge, RowMenuAction
from frontend.common import Palette


class WebhooksView(BaseView):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    status_toggled = Signal(str, bool)
    search_text_changed = Signal(str)
    test_requested = Signal(object)

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="webhooks.header.title", subtitle_key="webhooks.header.subtitle", parent=parent)
        self._active_dialog = None
        self._setup_ui()

    def _setup_ui(self):
        self.table_card = ModernTableCard(
            title_text=self.i18n.get("webhooks.header.title"),
            headers=[
                self.i18n.get("webhooks.table.col_name"),
                self.i18n.get("webhooks.table.col_preset"),
                self.i18n.get("webhooks.table.col_events"),
                self.i18n.get("webhooks.table.col_platforms"),
                self.i18n.get("webhooks.table.col_actions"),
            ],
            search_placeholder=self.i18n.get("webhooks.table.search_placeholder"),
            add_button_text=self.i18n.get("webhooks.table.btn_new"),
            add_button_icon="plus-filled.svg",
        )
        self.table_card.setup_empty_state(
            title=self.i18n.get("webhooks.empty.title"),
            desc=self.i18n.get("webhooks.empty.desc"),
            icon_name="illustration-request-timeout.svg",
            button_text=self.i18n.get("webhooks.empty.btn"),
            on_button_clicked=self.add_requested.emit,
        )

        self.table = self.table_card.table
        self.table.setSelectionMode(self.table.SelectionMode.NoSelection)
        self.txt_search = self.table_card.txt_search
        self.btn_new_add = self.table_card.btn_add
        self.txt_search.textChanged.connect(self.search_text_changed.emit)
        self.btn_new_add.clicked.connect(self.add_requested.emit)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 96)

        self.main_layout.addWidget(self.table_card, stretch=1)

    def populate_table(self, endpoints: list):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(endpoints))
        for row, endpoint in enumerate(endpoints):
            self.table.setItem(row, 0, self._create_item(endpoint.name))
            self.table.setCellWidget(row, 1, create_badge(
                self.i18n.get(f"webhooks.presets.{endpoint.formatter}"),
                state="plugin" if endpoint.formatter == "discord" else "everyone",
            ))
            self.table.setItem(row, 2, self._create_events_item(endpoint))
            self.table.setItem(row, 3, self._create_platforms_item(endpoint))
            self.table.setCellWidget(row, 4, self._create_actions_cell(endpoint))
        self.table.setUpdatesEnabled(True)
        self.table_card.set_empty(len(endpoints) == 0)
        self.table_card.set_title_count(self.i18n.get("webhooks.header.title"), len(endpoints))

    def _create_item(self, text: str, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        item.setForeground(QColor(Palette.NEUTRAL_400))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _create_events_item(self, endpoint) -> QTableWidgetItem:
        names = sorted(self.i18n.get(f"webhooks.events.{e}") for e in endpoint.events)
        item = self._create_item(str(len(names)), Qt.AlignmentFlag.AlignCenter)
        item.setToolTip("\n".join(f"- {n}" for n in names))
        return item

    def _create_platforms_item(self, endpoint) -> QTableWidgetItem:
        names = sorted(self.i18n.get(f"webhooks.platforms.{p}") for p in endpoint.platforms)
        return self._create_item(", ".join(names) or "-")

    def _create_actions_cell(self, endpoint):
        endpoint_id = endpoint.endpoint_id
        cell = TableActionCell()
        cell.add_switch(
            checked=endpoint.enabled,
            callback=lambda checked, eid=endpoint_id: self.status_toggled.emit(eid, checked),
        )
        cell.add_menu(
            [
                RowMenuAction(
                    text=self.i18n.get("common.row_menu.edit"),
                    icon_name="edit-filled.svg",
                    callback=lambda eid=endpoint_id: self.edit_requested.emit(eid),
                ),
                RowMenuAction(
                    text=self.i18n.get("common.row_menu.delete"),
                    icon_name="trash-filled.svg",
                    callback=lambda eid=endpoint_id, name=endpoint.name: self._confirm_delete(eid, name),
                    role="row_action_danger",
                ),
            ],
            tooltip=self.i18n.get("common.row_menu.more"),
        )
        return cell

    def _confirm_delete(self, endpoint_id: str, name: str) -> None:
        from frontend.dialogs import ModernConfirmDialog
        dialog = ModernConfirmDialog(
            self.i18n,
            parent=self,
            title_text=self.i18n.get("webhooks.confirm_delete.title"),
            body_text=self.i18n.get("webhooks.confirm_delete.desc").replace("{name}", name),
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.delete_requested.emit(endpoint_id)

    def set_ping_result(self, result) -> None:
        if self._active_dialog:
            self._active_dialog.set_ping_result(result)

    def show_add_dialog(self, **options) -> dict | None:
        return self._run_dialog(existing=None, **options)

    def show_edit_dialog(self, existing, **options) -> dict | None:
        return self._run_dialog(existing=existing, **options)

    def _run_dialog(self, existing, event_types, platforms, url_validator) -> dict | None:
        from frontend.dialogs import WebhookEndpointDialog
        dialog = WebhookEndpointDialog(
            self.i18n,
            event_types=event_types,
            platforms=platforms,
            url_validator=url_validator,
            existing=existing,
            parent=self,
        )
        dialog.test_requested.connect(self.test_requested.emit)
        self._active_dialog = dialog
        try:
            if dialog.exec():
                return dialog.get_data()
        finally:
            self._active_dialog = None
        return None
