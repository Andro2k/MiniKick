# backend\database\settings_storage.py

import logging
from backend.database.manager import DatabaseManager

logger = logging.getLogger("minikick.database.settings_storage")

class SQLiteSettingsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_string(self, key: str, value: str) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
                conn.commit()
            logger.debug("[SettingsStorage] Saved setting '%s'", key)
        except Exception as e:
            logger.error("[SettingsStorage] Error saving setting '%s': %s", key, e)

    def load_string(self, key: str, default: str = "") -> str:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception as e:
            logger.error("[SettingsStorage] Error loading setting '%s': %s", key, e)
            return default

    def save_bool(self, key: str, value: bool) -> None:
        self.save_string(key, "1" if value else "0")

    def load_bool(self, key: str, default: bool = False) -> bool:
        val = self.load_string(key, None)
        return default if val is None else val == "1"
    
    def get_all(self) -> dict:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM settings")
                return {k: (v == "1" if v in ("1", "0") else v) for k, v in cursor.fetchall()}
        except Exception as e:
            logger.error("[SettingsStorage] Error fetching all settings: %s", e)
            return {}

    def save_all(self, settings: dict) -> None:
        data = [
            (key, "1" if val is True else "0" if val is False else str(val))
            for key, val in settings.items()
        ]
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    data
                )
                conn.commit()
            logger.debug("[SettingsStorage] Batch saved %d settings", len(data))
        except Exception as e:
            logger.error("[SettingsStorage] Error batch saving settings: %s", e)
