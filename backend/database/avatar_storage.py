# backend\database\avatar_storage.py

import logging
from backend.database.manager import DatabaseManager

class SQLiteAvatarStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_cached(self, url: str) -> bytes | None:
        if not self.db_manager or not url:
            return None
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image_bytes FROM avatar_cache WHERE url = ?", (url.strip(),))
                r = cursor.fetchone()
                if r:
                    return r[0]
        except Exception as e:
            logging.error("[SQLiteAvatarStorage] Error reading from cache: %s", e)
        return None

    def save_to_cache(self, url: str, data: bytes) -> None:
        if not self.db_manager or not url:
            return
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO avatar_cache (url, image_bytes) VALUES (?, ?)
                    ON CONFLICT(url) DO UPDATE SET image_bytes=excluded.image_bytes, cached_at=CURRENT_TIMESTAMP
                """, (url.strip(), data))
                conn.commit()
        except Exception as e:
            logging.error("[SQLiteAvatarStorage] Error saving to cache: %s", e)
