# backend\database\system_log_storage.py

import logging
import sys
from .database_manager import DatabaseManager
from backend.core.log_format import LEVEL_ALIASES

logger = logging.getLogger("minikick.database.system_logs")

class SQLiteSystemLogStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def append_log(self, level: str, timestamp: str, message: str) -> int | None:
        if not self.db_manager:
            return None
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO system_logs (level, timestamp, message) VALUES (?, ?, ?)",
                    (level, timestamp, message)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            if sys.__stderr__ is not None:
                try:
                    sys.__stderr__.write(f"Error inserting log into DB: {e}\n")
                except Exception:
                    pass
        return None

    def append_logs(self, records: list[tuple[str, str, str]]) -> None:
        if not self.db_manager or not records:
            return
        with self.db_manager.get_connection() as conn:
            conn.executemany(
                "INSERT INTO system_logs (level, timestamp, message) VALUES (?, ?, ?)",
                records
            )
            conn.commit()

    def clear_logs(self) -> None:
        if not self.db_manager:
            return
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM system_logs")
                conn.commit()
        except Exception as e:
            logger.error("[SQLiteSystemLogStorage] Error clearing logs in DB: %s", e)

    def get_all_logs(self) -> list[tuple[str, str, str]]:
        if not self.db_manager:
            return []
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT level, timestamp, message FROM system_logs ORDER BY id ASC")
                return [(r[0], r[1], r[2]) for r in cursor.fetchall()]
        except Exception as e:
            logger.error("[SQLiteSystemLogStorage] Error fetching logs from DB: %s", e)
        return []

    def get_filtered_logs(
        self, filter_level: str, all_label: str, search_term: str, date_threshold: str = ""
    ) -> list[tuple[str, str, str]]:
        if not self.db_manager:
            return []
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT level, timestamp, message FROM system_logs WHERE 1=1"
                params = []
                
                if filter_level != all_label:
                    level_aliases = LEVEL_ALIASES.get(filter_level.upper())
                    if level_aliases:
                        placeholders = ", ".join("?" for _ in level_aliases)
                        query += f" AND level IN ({placeholders})"
                        params.extend(level_aliases)
                    else:
                        query += " AND level = ?"
                        params.append(filter_level)
                    
                if date_threshold:
                    query += " AND timestamp >= ?"
                    params.append(date_threshold)
                    
                if search_term.strip():
                    term = f"%{search_term.strip().lower()}%"
                    query += " AND (LOWER(level) LIKE ? OR LOWER(timestamp) LIKE ? OR LOWER(message) LIKE ?)"
                    params.extend([term, term, term])
                    
                query += " ORDER BY id DESC LIMIT 300"
                cursor.execute(query, params)
                rows = cursor.fetchall()
                rows.reverse()
                return [(r[0], r[1], r[2]) for r in rows]
        except Exception as e:
            logger.error("[SQLiteSystemLogStorage] Error fetching filtered logs from DB: %s", e)
        return []
