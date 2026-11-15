# resources\tests\test_music_playlist_storage.py
"""Pruebas del almacenamiento SQLite de playlists de música."""

import pytest

from backend.database import DatabaseManager, SQLiteMusicPlaylistStorage
from backend.interfaces import IMusicPlaylistStorage


@pytest.fixture
def storage(tmp_path):
    return SQLiteMusicPlaylistStorage(DatabaseManager(str(tmp_path / "test.db")))


def test_cumple_la_interfaz(storage):
    assert isinstance(storage, IMusicPlaylistStorage)


def test_crear_y_listar_ordenado_con_conteo(storage):
    b = storage.create_playlist("Beta")
    a = storage.create_playlist("alfa")
    storage.add_song(b, "T1", "A1", "u1")
    assert [(p["name"], p["song_count"]) for p in storage.list_playlists()] == [("alfa", 0), ("Beta", 1)]
    assert a > 0 and b > 0


def test_nombre_vacio_o_repetido_devuelve_menos_uno(storage):
    assert storage.create_playlist("   ") == -1
    assert storage.create_playlist("Rock") > 0
    assert storage.create_playlist("rock") == -1


def test_agregar_cancion_sin_duplicados(storage):
    pid = storage.create_playlist("Rock")
    assert storage.add_song(pid, "T", "A", "u1", "3:00") is True
    assert storage.add_song(pid, "T", "A", "u1") is False
    assert storage.add_song(pid, "T", "A", "") is False
    assert storage.add_song(9999, "T", "A", "u2") is False
    assert storage.get_songs(pid)[0]["duration"] == "3:00"


def test_quitar_cancion_y_borrar_playlist_en_cascada(storage):
    pid = storage.create_playlist("Rock")
    storage.add_song(pid, "T1", "A", "u1")
    storage.add_song(pid, "T2", "A", "u2")
    first = storage.get_songs(pid)[0]["item_id"]
    assert storage.remove_song(first) is True
    assert storage.remove_song(first) is False
    assert [s["url"] for s in storage.get_songs(pid)] == ["u2"]
    assert storage.delete_playlist(pid) is True
    assert storage.get_songs(pid) == []
    assert storage.delete_playlist(pid) is False
