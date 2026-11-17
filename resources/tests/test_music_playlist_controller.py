# resources\tests\test_music_playlist_controller.py
"""Pruebas del controlador de playlists de música."""

import pytest
from PySide6.QtCore import QObject, Signal

from backend.controllers import MusicPlaylistController
from backend.database import DatabaseManager, SQLiteMusicPlaylistStorage


class FakeView(QObject):
    playlist_create_requested = Signal(str)
    playlist_delete_requested = Signal(int)
    playlist_selected = Signal(int)
    playlist_add_current_requested = Signal(int)
    playlist_create_and_add_current_requested = Signal(str)
    playlist_add_song_requested = Signal(int, object)
    playlist_create_and_add_song_requested = Signal(str, object)
    playlist_enqueue_requested = Signal(int)
    playlist_song_remove_requested = Signal(int)
    view_shown = Signal()

    def __init__(self):
        super().__init__()
        self.playlists = []
        self.songs = (None, [])

    def set_playlists(self, playlists):
        self.playlists = playlists

    def set_playlist_songs(self, playlist_id, songs):
        self.songs = (playlist_id, songs)


class FakeToast:
    def __init__(self):
        self.calls = []

    def show_toast(self, title, message, level):
        self.calls.append((message, level))


class FakeI18n:
    def get(self, key, **kwargs):
        return key


SONG = {"title": "T", "artist": "A", "url": "u1", "duration": 185000}


@pytest.fixture
def env(tmp_path):
    storage = SQLiteMusicPlaylistStorage(DatabaseManager(str(tmp_path / "test.db")))
    view, toast = FakeView(), FakeToast()
    current = {"song": SONG, "queued": []}

    def enqueue(url):
        current["queued"].append(url)
        return url != "bad"

    controller = MusicPlaylistController(view, storage, lambda: current["song"], enqueue, toast, FakeI18n())
    return controller, view, toast, storage, current


def test_crear_playlist_actualiza_vista_y_avisa(env):
    _c, view, toast, _s, _cur = env
    view.playlist_create_requested.emit("Rock")
    assert [p["name"] for p in view.playlists] == ["Rock"]
    assert toast.calls[-1] == ("music.toast.playlist_created", "success")


def test_nombre_invalido_avisa_y_no_crea(env):
    _c, view, toast, _s, _cur = env
    view.playlist_create_requested.emit("  ")
    assert view.playlists == []
    assert toast.calls[-1] == ("music.toast.playlist_name_invalid", "warning")


def test_agregar_cancion_actual_con_duracion_formateada_y_sin_duplicados(env):
    _c, view, toast, storage, _cur = env
    pid = storage.create_playlist("Rock")
    view.playlist_selected.emit(pid)
    view.playlist_add_current_requested.emit(pid)
    assert toast.calls[-1] == ("music.toast.playlist_song_added", "success")
    assert view.songs[0] == pid and view.songs[1][0]["duration"] == "3:05"
    view.playlist_add_current_requested.emit(pid)
    assert toast.calls[-1] == ("music.toast.playlist_song_duplicate", "warning")
    assert len(view.songs[1]) == 1


def test_sin_cancion_actual_avisa(env):
    _c, view, toast, storage, cur = env
    cur["song"] = None
    pid = storage.create_playlist("Rock")
    view.playlist_add_current_requested.emit(pid)
    assert toast.calls[-1] == ("music.toast.playlist_no_song", "warning")
    assert storage.get_songs(pid) == []


def test_crear_y_agregar_en_un_paso(env):
    _c, view, toast, storage, _cur = env
    view.playlist_create_and_add_current_requested.emit("Nueva")
    pid = view.playlists[0]["id"]
    assert [s["url"] for s in storage.get_songs(pid)] == ["u1"]
    assert toast.calls[-1] == ("music.toast.playlist_song_added", "success")


def test_quitar_cancion_y_borrar_playlist_limpia_seleccion(env):
    _c, view, _t, storage, _cur = env
    pid = storage.create_playlist("Rock")
    storage.add_song(pid, "T", "A", "u1")
    view.playlist_selected.emit(pid)
    view.playlist_song_remove_requested.emit(view.songs[1][0]["item_id"])
    assert view.songs == (pid, [])
    view.playlist_delete_requested.emit(pid)
    assert view.playlists == [] and view.songs == (None, [])


def test_attach_view_posterior_carga_las_playlists(tmp_path):
    storage = SQLiteMusicPlaylistStorage(DatabaseManager(str(tmp_path / "test.db")))
    storage.create_playlist("Rock")
    controller = MusicPlaylistController(None, storage, lambda: None, lambda url: True, FakeToast(), FakeI18n())
    view = FakeView()
    controller.attach_view(view)
    assert [p["name"] for p in view.playlists] == ["Rock"]


HISTORY_SONG = {"title": "H", "artist": "A", "url": "h1", "duration": "4:10"}


def test_agregar_cancion_explicita_del_historial(env):
    _c, view, toast, storage, _cur = env
    pid = storage.create_playlist("Rock")
    view.playlist_selected.emit(pid)
    view.playlist_add_song_requested.emit(pid, HISTORY_SONG)
    assert toast.calls[-1] == ("music.toast.playlist_song_added", "success")
    assert view.songs[1][0]["duration"] == "4:10" and view.songs[1][0]["url"] == "h1"


def test_crear_y_agregar_cancion_explicita(env):
    _c, view, _t, storage, _cur = env
    view.playlist_create_and_add_song_requested.emit("Nueva", HISTORY_SONG)
    assert [s["url"] for s in storage.get_songs(view.playlists[0]["id"])] == ["h1"]


def test_encolar_playlist_envia_las_canciones_en_orden(env):
    _c, view, toast, storage, cur = env
    pid = storage.create_playlist("Rock")
    for url in ("u1", "bad", "u2"):
        storage.add_song(pid, "T", "A", url)
    view.playlist_enqueue_requested.emit(pid)
    assert cur["queued"] == ["u1", "bad", "u2"]
    assert toast.calls[-1] == ("music.toast.playlist_enqueued", "success")


def test_encolar_playlist_sin_exitos_avisa(env):
    _c, view, toast, storage, cur = env
    empty = storage.create_playlist("Vacia")
    view.playlist_enqueue_requested.emit(empty)
    assert cur["queued"] == [] and toast.calls[-1] == ("music.toast.playlist_nothing_enqueued", "warning")
    only_bad = storage.create_playlist("Mala")
    storage.add_song(only_bad, "T", "A", "bad")
    view.playlist_enqueue_requested.emit(only_bad)
    assert toast.calls[-1] == ("music.toast.playlist_nothing_enqueued", "warning")
