# resources\tests\test_music_playlist_ui.py
"""Pruebas de la UI de playlists de música (paneles, diálogo y vista con su controlador)."""

import pytest
from PySide6.QtWidgets import QPushButton

from backend.controllers import MusicPlaylistController
from backend.database import DatabaseManager, SQLiteMusicPlaylistStorage
from frontend.components.music import MusicPlaylistsPanel, MusicPlaylistSongsPanel
from frontend.dialogs import AddToPlaylistModal
from frontend.views.music_view import MusicView


class _I18n:
    def get(self, key: str, default: str = "") -> str:
        return default or key


class _Toast:
    def show_toast(self, *_args):
        pass


PLAYLISTS = [{"id": 1, "name": "Rock", "song_count": 2}, {"id": 2, "name": "Pop", "song_count": 0}]


def test_panel_playlists_muestra_filas_y_emite_seleccion(qapp):
    panel = MusicPlaylistsPanel(_I18n())
    picked = []
    panel.selected.connect(picked.append)
    panel.set_playlists(PLAYLISTS)
    assert panel.playlists_table.rowCount() == 2
    assert panel.name_of(2) == "Pop" and panel.name_of(99) is None
    panel._on_cell_clicked(1, 0)
    assert picked == [2]


def test_panel_playlists_crear_ignora_vacio_y_limpia_el_campo(qapp):
    panel = MusicPlaylistsPanel(_I18n())
    created = []
    panel.create_requested.connect(created.append)
    panel.txt_name.setText("   ")
    panel.btn_create.click()
    panel.txt_name.setText(" Jazz ")
    panel.btn_create.click()
    assert created == ["Jazz"] and panel.txt_name.text() == ""


def test_panel_playlists_conserva_la_seleccion_al_refrescar(qapp):
    panel = MusicPlaylistsPanel(_I18n())
    panel.set_playlists(PLAYLISTS)
    panel._on_cell_clicked(0, 0)
    panel.set_playlists([{"id": 1, "name": "Rock", "song_count": 3}] + PLAYLISTS[1:])
    assert panel.playlists_table.currentRow() == 0


def test_panel_canciones_muestra_filas_y_emite_quitar(qapp):
    panel = MusicPlaylistSongsPanel(_I18n())
    removed = []
    panel.song_remove_requested.connect(removed.append)
    panel.set_songs("Rock", [{"item_id": 7, "title": "T", "artist": "A", "url": "u", "duration": "3:05"}])
    assert panel.songs_table.rowCount() == 1
    assert panel.card_songs.lbl_title.text() == "Rock (1)"
    panel.songs_table.cellWidget(0, 3).findChild(QPushButton).click()
    assert removed == [7]


def test_dialogo_sin_playlists_solo_permite_crear(qapp):
    modal = AddToPlaylistModal([], _I18n())
    assert modal.rb_new.isChecked() and not modal.rb_existing.isEnabled()
    assert not modal.btn_confirm.isEnabled()
    modal.txt_name.setText(" Nueva ")
    assert modal.btn_confirm.isEnabled()
    assert modal.get_selection() == (None, "Nueva")


def test_dialogo_con_playlists_devuelve_la_elegida(qapp):
    modal = AddToPlaylistModal(PLAYLISTS, _I18n())
    assert modal.rb_existing.isChecked() and modal.btn_confirm.isEnabled()
    modal.cmb_playlists.setCurrentIndex(1)
    assert modal.get_selection() == (2, "")
    modal.rb_new.setChecked(True)
    assert not modal.btn_confirm.isEnabled()


def test_vista_y_controlador_flujo_completo(qapp, tmp_path):
    storage = SQLiteMusicPlaylistStorage(DatabaseManager(str(tmp_path / "test.db")))
    view = MusicView(_I18n())
    song = {"title": "T", "artist": "A", "url": "u1", "duration": 185000}
    controller = MusicPlaylistController(None, storage, lambda: song, _Toast(), _I18n())
    controller.attach_view(view)

    view.playlists_panel.create_requested.emit("Rock")
    assert view.playlists_panel.playlists_table.rowCount() == 1
    pid = view.playlists_panel.playlists[0]["id"]

    view.playlist_add_current_requested.emit(pid)
    view.playlists_panel.selected.emit(pid)
    assert view.queue_tabs.currentWidget() is view.playlist_songs_panel
    assert view.playlist_songs_panel.songs_table.rowCount() == 1
    assert view.playlist_songs_panel.card_songs.lbl_title.text() == "Rock (1)"

    view.playlist_song_remove_requested.emit(storage.get_songs(pid)[0]["item_id"])
    assert view.playlist_songs_panel.songs_table.rowCount() == 0
