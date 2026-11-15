# frontend\components\music\playlist_songs_panel.py
"""Panel con las canciones de la playlist seleccionada."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QAbstractItemView, QTableWidgetItem
from PySide6.QtCore import Signal, Qt
from frontend.common import BrandColors, Size
from frontend.widgets import ModernTable, ModernTableCard
from .table_cell_utils import build_action_cell, build_icon_button


class MusicPlaylistSongsPanel(QWidget):
    song_remove_requested = Signal(int)

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
            self.i18n.get("music.queue.col_duration"),
            self.i18n.get("music.queue.col_actions"),
        ]
        self.songs_table = ModernTable(headers, parent=self)
        self.card_songs = ModernTableCard(
            title_text=self.i18n.get("music.playlists.songs_title"),
            headers=headers,
            parent=self,
            custom_table=self.songs_table,
        )
        self.card_songs.setProperty("tab_flush", "true")

        table = self.songs_table
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.setMinimumHeight(200)

        modes = (QHeaderView.ResizeMode.Stretch, QHeaderView.ResizeMode.Stretch,
                 QHeaderView.ResizeMode.ResizeToContents, QHeaderView.ResizeMode.ResizeToContents)
        for col, mode in enumerate(modes):
            table.horizontalHeader().setSectionResizeMode(col, mode)

        self.card_songs.setup_empty_state(
            title=self.i18n.get("music.playlists.songs_empty_title"),
            desc=self.i18n.get("music.playlists.songs_empty_desc"),
            icon_name="illustration-music.svg",
            button_text="",
            on_button_clicked=lambda: None,
        )
        if getattr(self.card_songs, "btn_empty_action", None):
            self.card_songs.btn_empty_action.setVisible(False)

        layout.addWidget(self.card_songs)

    def _create_remove_cell(self, item_id: int) -> QWidget:
        return build_action_cell(build_icon_button(
            "trash-outline.svg", BrandColors.RED, self.i18n.get("music.playlists.remove_tooltip"), lambda: self.song_remove_requested.emit(item_id)
        ))

    def set_songs(self, playlist_name: str | None, songs: list[dict]):
        signature = (playlist_name, [(s["item_id"], s["url"]) for s in songs])
        if signature == self._signature:
            return
        self._signature = signature

        base = self.i18n.get("music.playlists.songs_title")
        if getattr(self.card_songs, "lbl_title", None):
            self.card_songs.lbl_title.setText(f"{playlist_name} ({len(songs)})" if playlist_name else base)
        self.card_songs.set_empty(not songs)

        table = self.songs_table
        table.setUpdatesEnabled(False)
        try:
            table.setRowCount(len(songs))
            for row, song in enumerate(songs):
                dur_item = QTableWidgetItem(song.get("duration") or "-")
                dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 0, QTableWidgetItem(song.get("title") or self.i18n.get("music.player.unknown_song")))
                table.setItem(row, 1, QTableWidgetItem(song.get("artist") or "-"))
                table.setItem(row, 2, dur_item)
                table.setCellWidget(row, 3, self._create_remove_cell(song["item_id"]))
        finally:
            table.setUpdatesEnabled(True)
