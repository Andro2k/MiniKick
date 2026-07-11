# backend\storage\spam_storage.py

from backend.storage.manager import DatabaseManager

class SQLiteSpamStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> dict:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filter_id, is_active, penalty, duration, exclude_group, max_amount FROM spam_filters")
            filters = {}
            for row in cursor.fetchall():
                filters[row[0]] = {
                    "is_active": bool(row[1]),
                    "penalty": row[2],
                    "duration": row[3],
                    "exclude_group": row[4],
                    "max_amount": row[5]
                }
            return filters

    def save_filter(self, filter_id: str, config: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO spam_filters (filter_id, is_active, penalty, duration, exclude_group, max_amount)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(filter_id) DO UPDATE SET
                    is_active=excluded.is_active, penalty=excluded.penalty, duration=excluded.duration,
                    exclude_group=excluded.exclude_group, max_amount=excluded.max_amount
            """, (
                filter_id, int(config.get("is_active", False)), config.get("penalty", "timeout"),
                config.get("duration", 300), config.get("exclude_group", "none"), config.get("max_amount", 0)
            ))
            conn.commit()
