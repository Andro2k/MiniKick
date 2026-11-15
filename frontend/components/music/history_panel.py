# frontend\components\music\history_panel.py
"""Panel del historial de música."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QAbstractItemView, QTableWidgetItem
from PySide6.QtCore import Signal, Qt
from frontend.common import BrandColors, Size
from frontend.widgets import ModernTable, ModernTableCard
from .queue_panel import requester_style
from .table_cell_utils import build_action_cell, build_icon_button


class MusicHistoryPanel(QWidget):
    requeue_requested = Signal(str, str, str)
    add_to_playlist_requested = Signal(dict)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._signature = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Size.Margin.MRG_NON)
        layout.setSpacing(Size.SPACING_NN)

        headers = [
            self.i18n.get("music.queue.col_title"),
            self.i18n.get("music.queue.col_artist"),
            self.i18n.get("music.queue.col_requester"),
            self.i18n.get("music.queue.col_duration"),
            self.i18n.get("music.queue.col_actions"),
        ]
        self.history_table = ModernTable(headers, parent=self)
        self.card_history = ModernTableCard(
            title_text=self.i18n.get("music.queue.history_title"),
            headers=headers,
            parent=self,
            custom_table=self.history_table,
        )
        self.card_history.setProperty("tab_flush", "true")

        table = self.history_table
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.setMinimumHeight(200)

        modes = (QHeaderView.ResizeMode.Stretch, QHeaderView.ResizeMode.Stretch,
                 QHeaderView.ResizeMode.ResizeToContents, QHeaderView.ResizeMode.ResizeToContents,
                 QHeaderView.ResizeMode.ResizeToContents)
        for col, mode in enumerate(modes):
            table.horizontalHeader().setSectionResizeMode(col, mode)

        self.card_history.setup_empty_state(
            title=self.i18n.get("music.queue.history_empty"),
            desc=self.i18n.get("music.queue.history_empty_desc"),
            icon_name="illustration-music.svg",
            button_text="",
            on_button_clicked=lambda: None,
        )
        if getattr(self.card_history, "btn_empty_action", None):
            self.card_history.btn_empty_action.setVisible(False)

        layout.addWidget(self.card_history)

    def _create_action_buttons(self, song: dict) -> QWidget:
        url = song.get("url") or ""
        requeue_args = (url, song.get("requester") or "", song.get("platform") or "kick")
        playlist_song = {"title": song.get("title") or "", "artist": song.get("artist") or "", "url": url, "duration": song.get("duration") or "-"}
        return build_action_cell(
            build_icon_button("plus-filled.svg", BrandColors.GREEN, self.i18n.get("music.queue.requeue_tooltip"), lambda: self.requeue_requested.emit(*requeue_args)),
            build_icon_button("music-notes-filled.svg", BrandColors.GREEN, self.i18n.get("music.playlists.add_tooltip"), lambda: self.add_to_playlist_requested.emit(playlist_song)),
        )

    def update_history(self, items: list[dict]):
        signature = [(s.get("db_id"), s.get("url")) for s in items]
        if signature == self._signature:
            return
        self._signature = signature

        base = self.i18n.get("music.queue.history_title")
        if getattr(self.card_history, "lbl_title", None):
            self.card_history.lbl_title.setText(f"{base} ({len(items)})")
        self.card_history.set_empty(not items)

        table = self.history_table
        table.setUpdatesEnabled(False)
        try:
            table.setRowCount(len(items))
            for row, song in enumerate(items):
                requester = song.get("requester", "")
                color, icon = requester_style(song.get("platform"), requester)
                req_item = QTableWidgetItem(f" {requester}" if requester else "-")
                if color is not None:
                    req_item.setForeground(color)
                if icon is not None and requester:
                    req_item.setIcon(icon)
                dur_item = QTableWidgetItem(song.get("duration", "-"))
                dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                table.setItem(row, 0, QTableWidgetItem(song.get("title") or self.i18n.get("music.player.unknown_song")))
                table.setItem(row, 1, QTableWidgetItem(song.get("artist") or "-"))
                table.setItem(row, 2, req_item)
                table.setItem(row, 3, dur_item)
                table.setCellWidget(row, 4, self._create_action_buttons(song))
        finally:
            table.setUpdatesEnabled(True)
