# frontend\components\music\playlists_panel.py
"""Panel con la lista de playlists de música (crear, seleccionar y eliminar)."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QAbstractItemView, QTableWidgetItem, QLineEdit
from PySide6.QtCore import Signal, Qt
from frontend.common import BrandColors, Size
from frontend.dialogs import ModernConfirmDialog
from frontend.widgets import ModernButton, ModernTable, ModernTableCard
from .table_cell_utils import build_action_cell, build_icon_button


class MusicPlaylistsPanel(QWidget):
    create_requested = Signal(str)
    delete_requested = Signal(int)
    selected = Signal(int)
    enqueue_requested = Signal(int)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._playlists: list[dict] = []
        self._selected_id: int | None = None
        self._setup_ui()

    @property
    def playlists(self) -> list[dict]:
        return list(self._playlists)

    def name_of(self, playlist_id: int | None) -> str | None:
        return next((p["name"] for p in self._playlists if p["id"] == playlist_id), None)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Size.Margin.MRG_NON)
        layout.setSpacing(Size.SPACING_NN)

        headers = [
            self.i18n.get("music.playlists.col_name"),
            self.i18n.get("music.playlists.col_songs"),
            self.i18n.get("music.queue.col_actions"),
        ]
        self.playlists_table = ModernTable(headers, parent=self)
        self.card_playlists = ModernTableCard(
            title_text=self.i18n.get("music.playlists.title"),
            headers=headers,
            parent=self,
            custom_table=self.playlists_table,
        )
        self.card_playlists.setProperty("tab_flush", "true")

        self.txt_name = QLineEdit(self)
        self.txt_name.setPlaceholderText(self.i18n.get("music.playlists.name_placeholder"))
        self.txt_name.returnPressed.connect(self._on_create_clicked)
        self.btn_create = ModernButton(self.i18n.get("music.playlists.create_btn"), role="action_outlined", icon_name="plus.svg", parent=self)
        self.btn_create.setEnabled(False)
        self.btn_create.clicked.connect(self._on_create_clicked)
        self.txt_name.textChanged.connect(lambda text: self.btn_create.setEnabled(bool(text.strip())))
        self.card_playlists.add_header_control(self.txt_name)
        self.card_playlists.add_action_button(self.btn_create)

        table = self.playlists_table
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.setMinimumHeight(200)
        table.cellClicked.connect(self._on_cell_clicked)

        modes = (QHeaderView.ResizeMode.Stretch, QHeaderView.ResizeMode.ResizeToContents, QHeaderView.ResizeMode.ResizeToContents)
        for col, mode in enumerate(modes):
            table.horizontalHeader().setSectionResizeMode(col, mode)

        self.card_playlists.setup_empty_state(
            title=self.i18n.get("music.playlists.empty_title"),
            desc=self.i18n.get("music.playlists.empty_desc"),
            icon_name="illustration-music.svg",
            button_text="",
            on_button_clicked=lambda: None,
        )
        if getattr(self.card_playlists, "btn_empty_action", None):
            self.card_playlists.btn_empty_action.setVisible(False)

        layout.addWidget(self.card_playlists)

    def _on_create_clicked(self):
        name = self.txt_name.text().strip()
        if not name:
            return
        self.txt_name.clear()
        self.create_requested.emit(name)

    def _on_cell_clicked(self, row: int, _col: int):
        item = self.playlists_table.item(row, 0)
        if item is None:
            return
        self._selected_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected.emit(self._selected_id)

    def _confirm_delete(self, playlist: dict):
        body = self.i18n.get("music.playlists.delete_confirm_body", name=playlist["name"])
        dialog = ModernConfirmDialog(
            self.i18n, parent=self, title_text=self.i18n.get("music.playlists.delete_confirm_title"), body_text=body
        )
        if dialog.exec():
            self.delete_requested.emit(playlist["id"])

    def _create_delete_cell(self, playlist: dict) -> QWidget:
        btn_enqueue = build_icon_button(
            "play.svg", BrandColors.GREEN, self.i18n.get("music.playlists.enqueue_tooltip"), lambda: self.enqueue_requested.emit(playlist["id"])
        )
        btn_enqueue.setEnabled(playlist["song_count"] > 0)
        btn_delete = build_icon_button(
            "trash.svg", BrandColors.RED, self.i18n.get("music.playlists.delete_tooltip"), lambda: self._confirm_delete(playlist)
        )
        return build_action_cell(btn_enqueue, btn_delete)

    def set_playlists(self, playlists: list[dict]):
        if playlists == self._playlists:
            return
        self._playlists = list(playlists)
        if self._selected_id not in {p["id"] for p in playlists}:
            self._selected_id = None

        if getattr(self.card_playlists, "lbl_title", None):
            base = self.i18n.get("music.playlists.title")
            self.card_playlists.lbl_title.setText(f"{base} ({len(playlists)})")
        self.card_playlists.set_empty(not playlists)

        table = self.playlists_table
        table.setUpdatesEnabled(False)
        try:
            table.setRowCount(len(playlists))
            for row, playlist in enumerate(playlists):
                name_item = QTableWidgetItem(playlist["name"])
                name_item.setData(Qt.ItemDataRole.UserRole, playlist["id"])
                count_item = QTableWidgetItem(str(playlist["song_count"]))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 0, name_item)
                table.setItem(row, 1, count_item)
                table.setCellWidget(row, 2, self._create_delete_cell(playlist))
                if playlist["id"] == self._selected_id:
                    table.selectRow(row)
        finally:
            table.setUpdatesEnabled(True)
