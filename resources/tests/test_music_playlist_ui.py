# resources\tests\test_music_playlist_ui.py
"""Pruebas de la UI de playlists de música (paneles, diálogo y vista con su controlador)."""

import pytest
from PySide6.QtWidgets import QPushButton

from backend.controllers import MusicPlaylistController
from backend.database import DatabaseManager, SQLiteMusicPlaylistStorage
from frontend.components.music import MusicHistoryPanel, MusicPlaylistsPanel, MusicPlaylistSongsPanel
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
    controller = MusicPlaylistController(None, storage, lambda: song, lambda url: True, _Toast(), _I18n())
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


def test_boton_crear_solo_se_activa_con_nombre(qapp):
    panel = MusicPlaylistsPanel(_I18n())
    assert not panel.btn_create.isEnabled()
    panel.txt_name.setText("   ")
    assert not panel.btn_create.isEnabled()
    panel.txt_name.setText("Jazz")
    assert panel.btn_create.isEnabled()
    panel.btn_create.click()
    assert not panel.btn_create.isEnabled()


def test_boton_encolar_playlist_emite_id_y_se_desactiva_si_esta_vacia(qapp):
    panel = MusicPlaylistsPanel(_I18n())
    queued = []
    panel.enqueue_requested.connect(queued.append)
    panel.set_playlists(PLAYLISTS)
    with_songs = panel.playlists_table.cellWidget(0, 2).findChildren(QPushButton)
    empty = panel.playlists_table.cellWidget(1, 2).findChildren(QPushButton)
    assert len(with_songs) == 2 and with_songs[0].isEnabled() and not empty[0].isEnabled()
    with_songs[0].click()
    assert queued == [1]


def test_historial_tiene_encolar_y_agregar_a_playlist(qapp):
    panel = MusicHistoryPanel(_I18n())
    requeued, to_playlist = [], []
    panel.requeue_requested.connect(lambda *args: requeued.append(args))
    panel.add_to_playlist_requested.connect(to_playlist.append)
    panel.update_history([{"db_id": 1, "title": "T", "artist": "A", "url": "u1", "requester": "ana", "platform": "kick", "duration": "3:05"}])
    buttons = panel.history_table.cellWidget(0, panel.history_table.columnCount() - 1).findChildren(QPushButton)
    assert len(buttons) == 2
    buttons[0].click()
    buttons[1].click()
    assert requeued == [("u1", "ana", "kick")]
    assert to_playlist == [{"title": "T", "artist": "A", "url": "u1", "duration": "3:05"}]


class _FakeModal:
    selection = (None, "")

    def __init__(self, *_args, **_kwargs):
        pass

    def exec(self):
        return True

    def get_selection(self):
        return _FakeModal.selection


@pytest.mark.parametrize(
    "selection, song, expected",
    [
        ((3, ""), None, ("playlist_add_current_requested", (3,))),
        ((None, "Nueva"), None, ("playlist_create_and_add_current_requested", ("Nueva",))),
        ((3, ""), {"url": "u"}, ("playlist_add_song_requested", (3, {"url": "u"}))),
        ((None, "Nueva"), {"url": "u"}, ("playlist_create_and_add_song_requested", ("Nueva", {"url": "u"}))),
    ],
)
def test_vista_emite_la_senal_correcta_segun_destino_y_cancion(qapp, monkeypatch, selection, song, expected):
    monkeypatch.setattr("frontend.views.music_view.AddToPlaylistModal", _FakeModal)
    _FakeModal.selection = selection
    view = MusicView(_I18n())
    received = []
    getattr(view, expected[0]).connect(lambda *args: received.append(args))
    view._prompt_playlist_target(song)
    assert received == [expected[1]]
