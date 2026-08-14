# backend\database\music_storage.py

import logging
from datetime import datetime
from backend.database.manager import DatabaseManager

logger = logging.getLogger("minikick.database.music")

import re
import difflib

def normalize_query(query: str) -> str:
    if not query:
        return ""
    q = query.lower().strip()
    q = re.sub(r'[^\w\s]', '', q)
    tokens = sorted([w for w in q.split() if w])
    return " ".join(tokens)

class SQLiteMusicStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _increment_play_count(self, conn, query_raw: str):
        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE youtube_search_cache SET play_count = COALESCE(play_count, 0) + 1, last_accessed = ? WHERE query_raw = ?",
                (now_str, query_raw)
            )
            conn.commit()
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error incrementing play count: %s", e)

    def get_cached_search(self, query: str) -> dict | None:
        if not self.db_manager or not query:
            return None
        raw_q = query.lower().strip()
        norm_q = normalize_query(query)
        if not norm_q:
            return None

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT title, artist, url, duration, query_raw FROM youtube_search_cache WHERE LOWER(query_raw) IN (?, ?)",
                    (raw_q, norm_q)
                )
                r = cursor.fetchone()
                if r:
                    self._increment_play_count(conn, r[4])
                    return {"title": r[0], "artist": r[1], "url": r[2], "duration": r[3] or "-"}

                cursor.execute("SELECT query_raw, title, artist, url, duration FROM youtube_search_cache")
                rows = cursor.fetchall()
                best_match = None
                best_ratio = 0.0

                for row in rows:
                    c_query = row[0]
                    c_norm = normalize_query(c_query)
                    ratio = difflib.SequenceMatcher(None, norm_q, c_norm).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = row

                if best_ratio >= 0.85 and best_match:
                    logger.info("[SQLiteMusicStorage] Fuzzy match '%s' -> '%s' (ratio: %.2f)", query, best_match[0], best_ratio)
                    self._increment_play_count(conn, best_match[0])
                    return {"title": best_match[1], "artist": best_match[2], "url": best_match[3], "duration": best_match[4] or "-"}

        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error reading search cache: %s", e)
        return None

    def save_search_cache(self, query: str, song_entry: dict) -> None:
        if not self.db_manager or not query or not song_entry:
            return
        norm_q = normalize_query(query) or query.lower().strip()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO youtube_search_cache (query_raw, title, artist, url, duration, play_count, last_accessed) 
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                    ON CONFLICT(query_raw) DO UPDATE SET 
                        title=excluded.title, artist=excluded.artist, url=excluded.url, duration=excluded.duration,
                        play_count = COALESCE(play_count, 0) + 1, last_accessed=?
                """, (
                    norm_q,
                    song_entry["title"],
                    song_entry["artist"],
                    song_entry["url"],
                    song_entry.get("duration", "-"),
                    now_str,
                    now_str
                ))
                conn.commit()
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error saving search cache: %s", e)


    def update_file_size(self, query_or_url: str, size_mb: float) -> None:
        if not self.db_manager or not query_or_url or size_mb <= 0:
            return
        try:
            norm_q = normalize_query(query_or_url) or query_or_url.lower().strip()
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE youtube_search_cache SET file_size_mb = ? WHERE LOWER(query_raw) = ? OR LOWER(url) = ?",
                    (round(size_mb, 2), norm_q, query_or_url.lower().strip())
                )
                conn.commit()
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error updating file size: %s", e)

    def get_least_popular_cached_songs(self) -> list[dict]:
        if not self.db_manager:
            return []
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query_raw, title, artist, url, COALESCE(play_count, 1) as pc, last_accessed, COALESCE(file_size_mb, 4.0) as sz,
                           (COALESCE(play_count, 1) / (
                               ((julianday('now') - julianday(COALESCE(last_accessed, datetime('now')))) + 0.5) * COALESCE(file_size_mb, 4.0)
                           )) AS score
                    FROM youtube_search_cache
                    ORDER BY score ASC
                """)
                rows = cursor.fetchall()
                return [
                    {
                        "query_raw": r[0],
                        "title": r[1],
                        "artist": r[2],
                        "url": r[3],
                        "play_count": r[4],
                        "last_accessed": r[5],
                        "file_size_mb": r[6],
                        "score": r[7]
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error getting least popular cached songs: %s", e)
        return []



    def add_song_to_queue(
        self, title: str, artist: str, url: str, requester: str, provider: str, platform: str = "kick", duration: str = "-"
    ) -> int:
        if not self.db_manager:
            return -1
        try:
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO music_queue (title, artist, url, requester, provider, platform, is_played, duration, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                    (title, artist, url, requester, provider, platform or "kick", duration, local_now)
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
                    "SELECT id, title, artist, url, requester, provider, duration, platform FROM music_queue WHERE provider = ? AND is_played = 0 ORDER BY id ASC",
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
                        "duration": r[6],
                        "platform": r[7] if len(r) > 7 and r[7] else "kick"
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            logger.error("[SQLiteMusicStorage] Error loading pending songs: %s", e)
        return []
