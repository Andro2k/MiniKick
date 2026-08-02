# backend/database/music_storage.py

import logging
from datetime import datetime
from backend.database.manager import DatabaseManager

logger = logging.getLogger("minikick.database.music")

class SQLiteMusicStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_cached_search(self, query: str) -> dict | None:
        if not self.db_manager or not query:
            return None
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT title, artist, url, duration FROM youtube_search_cache WHERE LOWER(query_raw) = ?",
                    (query.lower().strip(),)
                )
                r = cursor.fetchone()
                if r:
                    return {"title": r[0], "artist": r[1], "url": r[2], "duration": r[3] or "-"}
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error reading search cache: %s", e)
        return None

    def save_search_cache(self, query: str, song_entry: dict) -> None:
        if not self.db_manager or not query or not song_entry:
            return
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO youtube_search_cache (query_raw, title, artist, url, duration) 
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(query_raw) DO UPDATE SET 
                        title=excluded.title, artist=excluded.artist, url=excluded.url, duration=excluded.duration, cached_at=CURRENT_TIMESTAMP
                """, (
                    query.lower().strip(),
                    song_entry["title"],
                    song_entry["artist"],
                    song_entry["url"],
                    song_entry.get("duration", "-")
                ))
                conn.commit()
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error saving search cache: %s", e)

    def add_song_to_queue(
        self, title: str, artist: str, url: str, requester: str, provider: str, duration: str = "-"
    ) -> int:
        if not self.db_manager:
            return -1
        try:
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO music_queue (title, artist, url, requester, provider, is_played, duration, created_at) VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
                    (title, artist, url, requester, provider, duration, local_now)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error adding song to queue: %s", e)
        return -1

    def update_song_status(self, db_id: int, status: int) -> None:
        if not self.db_manager or db_id is None or db_id < 0:
            return
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE music_queue SET is_played = ? WHERE id = ?", (status, db_id))
                conn.commit()
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error updating song status: %s", e)

    def load_pending_songs(self, provider: str) -> list[dict]:
        if not self.db_manager:
            return []
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, artist, url, requester, provider, duration FROM music_queue WHERE provider = ? AND is_played = 0 ORDER BY id ASC",
                    (provider,)
                )
                return [
                    {
                        "db_id": r[0],
                        "title": r[1],
                        "artist": r[2],
                        "url": r[3],
                        "requester": r[4],
                        "provider": r[5],
                        "duration": r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error loading pending songs: %s", e)
        return []
