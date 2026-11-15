# backend\database\music_playlist_storage.py
"""Almacenamiento SQLite de playlists de música."""

import logging
import sqlite3
from .database_manager import DatabaseManager

logger = logging.getLogger("minikick.database.music_playlist")


class SQLiteMusicPlaylistStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def list_playlists(self) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT p.id, p.name, COUNT(i.id) FROM music_playlists p "
                    "LEFT JOIN music_playlist_items i ON i.playlist_id = p.id "
                    "GROUP BY p.id ORDER BY p.name COLLATE NOCASE"
                ).fetchall()
            return [{"id": r[0], "name": r[1], "song_count": r[2]} for r in rows]
        except Exception as e:
            logger.error("[SQLiteMusicPlaylistStorage] Error listing playlists: %s", e)
        return []

    def create_playlist(self, name: str) -> int:
        """Devuelve el id de la playlist creada, o -1 si el nombre es vacío, repetido o falla."""
        name = (name or "").strip()
        if not name:
            return -1
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("INSERT INTO music_playlists (name) VALUES (?)", (name,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.info("[SQLiteMusicPlaylistStorage] Playlist already exists: %s", name)
        except Exception as e:
            logger.error("[SQLiteMusicPlaylistStorage] Error creating playlist: %s", e)
        return -1

    def delete_playlist(self, playlist_id: int) -> bool:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("DELETE FROM music_playlists WHERE id = ?", (playlist_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("[SQLiteMusicPlaylistStorage] Error deleting playlist: %s", e)
        return False

    def add_song(self, playlist_id: int, title: str, artist: str, url: str, duration: str = "-") -> bool:
        """Devuelve False si la canción ya está en la playlist o si falla."""
        if not url:
            return False
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT INTO music_playlist_items (playlist_id, title, artist, url, duration) VALUES (?, ?, ?, ?, ?)",
                    (playlist_id, title or "", artist or "", url, duration or "-"),
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.info("[SQLiteMusicPlaylistStorage] Song already in playlist %s or playlist missing", playlist_id)
        except Exception as e:
            logger.error("[SQLiteMusicPlaylistStorage] Error adding song: %s", e)
        return False

    def remove_song(self, item_id: int) -> bool:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("DELETE FROM music_playlist_items WHERE id = ?", (item_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("[SQLiteMusicPlaylistStorage] Error removing song: %s", e)
        return False

    def get_songs(self, playlist_id: int) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, title, artist, url, duration FROM music_playlist_items "
                    "WHERE playlist_id = ? ORDER BY id",
                    (playlist_id,),
                ).fetchall()
            return [{"item_id": r[0], "title": r[1], "artist": r[2], "url": r[3], "duration": r[4] or "-"} for r in rows]
        except Exception as e:
            logger.error("[SQLiteMusicPlaylistStorage] Error loading playlist songs: %s", e)
        return []
