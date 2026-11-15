# backend\controllers\music_playlist_controller.py
"""Controlador de playlists de música.

Contrato de la vista (se conecta con attach_view):
  señales: playlist_create_requested(str), playlist_delete_requested(int), playlist_selected(int),
           playlist_add_current_requested(int), playlist_create_and_add_current_requested(str),
           playlist_add_song_requested(int, dict), playlist_create_and_add_song_requested(str, dict),
           playlist_enqueue_requested(int), playlist_song_remove_requested(int), view_shown()
  métodos: set_playlists(list[dict]), set_playlist_songs(int | None, list[dict])
"""

import logging
from typing import Callable
from PySide6.QtCore import QObject, Slot
from backend.interfaces import IMusicPlaylistStorage

logger = logging.getLogger("minikick.controllers.music_playlist")


def _format_duration_ms(ms) -> str:
    seconds = int((ms or 0) // 1000)
    if seconds <= 0:
        return "-"
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


class MusicPlaylistController(QObject):
    def __init__(
        self,
        view,
        playlist_storage: IMusicPlaylistStorage,
        current_song_provider: Callable[[], dict | None],
        enqueue_song: Callable[[str], bool],
        toast_manager,
        i18n,
    ):
        super().__init__()
        self.view = view
        self.playlist_storage = playlist_storage
        self.current_song_provider = current_song_provider
        self.enqueue_song = enqueue_song
        self.toast = toast_manager
        self.i18n = i18n
        self._selected_id: int | None = None
        self._signals_connected = False
        if self.view is not None:
            self._connect_signals()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.refresh()

    def _connect_signals(self):
        if self._signals_connected:
            return
        self._signals_connected = True
        self.view.playlist_create_requested.connect(self.create_playlist)
        self.view.playlist_delete_requested.connect(self.delete_playlist)
        self.view.playlist_selected.connect(self.select_playlist)
        self.view.playlist_add_current_requested.connect(self.add_current_song)
        self.view.playlist_create_and_add_current_requested.connect(self.create_playlist_and_add_current)
        self.view.playlist_add_song_requested.connect(self.add_song)
        self.view.playlist_create_and_add_song_requested.connect(self.create_playlist_and_add_song)
        self.view.playlist_enqueue_requested.connect(self.enqueue_playlist)
        self.view.playlist_song_remove_requested.connect(self.remove_song)
        self.view.view_shown.connect(self.refresh)

    def _notify(self, key: str, level: str) -> None:
        if self.toast:
            self.toast.show_toast(self.i18n.get("music.header.title"), self.i18n.get(key), level)

    def refresh(self) -> None:
        if self.view is None:
            return
        self.view.set_playlists(self.playlist_storage.list_playlists())
        self.view.set_playlist_songs(
            self._selected_id, self.playlist_storage.get_songs(self._selected_id) if self._selected_id else []
        )

    def _create_or_warn(self, name: str) -> int:
        playlist_id = self.playlist_storage.create_playlist(name)
        if playlist_id < 0:
            self._notify("music.toast.playlist_name_invalid", "warning")
        return playlist_id

    @Slot(str)
    def create_playlist(self, name: str) -> None:
        if self._create_or_warn(name) < 0:
            return
        logger.info("[User Action] Playlist created")
        self._notify("music.toast.playlist_created", "success")
        self.refresh()

    @Slot(int)
    def delete_playlist(self, playlist_id: int) -> None:
        if not self.playlist_storage.delete_playlist(playlist_id):
            return
        if self._selected_id == playlist_id:
            self._selected_id = None
        logger.info("[User Action] Playlist deleted")
        self._notify("music.toast.playlist_deleted", "success")
        self.refresh()

    @Slot(int)
    def select_playlist(self, playlist_id: int) -> None:
        self._selected_id = playlist_id
        self.refresh()

    def _add_song(self, playlist_id: int, song: dict | None) -> None:
        if not song or not song.get("url"):
            self._notify("music.toast.playlist_no_song", "warning")
            return
        added = self.playlist_storage.add_song(
            playlist_id, song.get("title", ""), song.get("artist", ""), song["url"], song.get("duration") or "-"
        )
        self._notify("music.toast.playlist_song_added" if added else "music.toast.playlist_song_duplicate", "success" if added else "warning")
        self.refresh()

    @Slot(int)
    def add_current_song(self, playlist_id: int) -> None:
        song = self.current_song_provider()
        self._add_song(playlist_id, {**song, "duration": _format_duration_ms(song.get("duration"))} if song else None)

    @Slot(int, object)
    def add_song(self, playlist_id: int, song: dict) -> None:
        self._add_song(playlist_id, song)

    @Slot(str)
    def create_playlist_and_add_current(self, name: str) -> None:
        playlist_id = self._create_or_warn(name)
        if playlist_id > 0:
            self.add_current_song(playlist_id)

    @Slot(str, object)
    def create_playlist_and_add_song(self, name: str, song: dict) -> None:
        playlist_id = self._create_or_warn(name)
        if playlist_id > 0:
            self.add_song(playlist_id, song)

    @Slot(int)
    def enqueue_playlist(self, playlist_id: int) -> None:
        queued = sum(1 for song in self.playlist_storage.get_songs(playlist_id) if self.enqueue_song(song["url"]))
        if not queued:
            self._notify("music.toast.playlist_nothing_enqueued", "warning")
            return
        logger.info("[User Action] Playlist added to queue")
        if self.toast:
            message = self.i18n.get("music.toast.playlist_enqueued").replace("{count}", str(queued))
            self.toast.show_toast(self.i18n.get("music.header.title"), message, "success")

    @Slot(int)
    def remove_song(self, item_id: int) -> None:
        if self.playlist_storage.remove_song(item_id):
            self.refresh()
