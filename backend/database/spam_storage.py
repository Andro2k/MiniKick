# backend\database\spam_storage.py

import logging
from backend.database.manager import DatabaseManager

logger = logging.getLogger("minikick.database.spam_storage")

class SQLiteSpamStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> dict:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT filter_id, is_active, penalty, duration, exclude_group, max_amount, allowlist, apply_kick, apply_twitch, apply_youtube FROM spam_filters")
                filters = {}
                for row in cursor.fetchall():
                    filters[row[0]] = {
                        "is_active": bool(row[1]),
                        "penalty": row[2],
                        "duration": row[3],
                        "exclude_group": row[4],
                        "max_amount": row[5],
                        "allowlist": row[6] if len(row) > 6 and row[6] is not None else "",
                        "apply_kick": bool(row[7]) if len(row) > 7 and row[7] is not None else True,
                        "apply_twitch": bool(row[8]) if len(row) > 8 and row[8] is not None else True,
                        "apply_youtube": bool(row[9]) if len(row) > 9 and row[9] is not None else True
                    }
                return filters
        except Exception as e:
            logger.error("[SpamStorage] Error loading all spam filters: %s", e)
            return {}

    def save_filter(self, filter_id: str, config: dict) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO spam_filters (filter_id, is_active, penalty, duration, exclude_group, max_amount, allowlist, apply_kick, apply_twitch, apply_youtube)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(filter_id) DO UPDATE SET
                        is_active=excluded.is_active, penalty=excluded.penalty, duration=excluded.duration,
                        exclude_group=excluded.exclude_group, max_amount=excluded.max_amount, allowlist=excluded.allowlist,
                        apply_kick=excluded.apply_kick, apply_twitch=excluded.apply_twitch, apply_youtube=excluded.apply_youtube
                """, (
                    filter_id, int(config.get("is_active", False)), config.get("penalty", "timeout"),
                    config.get("duration", 300), config.get("exclude_group", "none"), config.get("max_amount", 0),
                    config.get("allowlist", ""), int(config.get("apply_kick", True)), int(config.get("apply_twitch", True)),
                    int(config.get("apply_youtube", True))
                ))
                conn.commit()
            logger.debug("[SpamStorage] Saved spam filter '%s' (active=%s)", filter_id, config.get("is_active"))
        except Exception as e:
            logger.error("[SpamStorage] Error saving spam filter '%s': %s", filter_id, e)
