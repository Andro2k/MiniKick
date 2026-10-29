# backend\database\settings_storage.py

import logging
import threading
from .database_manager import DatabaseManager

logger = logging.getLogger("minikick.database.settings_storage")

class SQLiteSettingsStorage:
    _cache_lock = threading.Lock()
    _snapshots: dict[str, dict] = {}

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _snapshot(self) -> dict:
        db_key = self.db_manager.db_name
        with self._cache_lock:
            snapshot = self._snapshots.get(db_key)
            if snapshot is None:
                with self.db_manager.get_connection() as conn:
                    snapshot = dict(conn.execute("SELECT key, value FROM settings").fetchall())
                self._snapshots[db_key] = snapshot
            return snapshot

    def _invalidate(self) -> None:
        with self._cache_lock:
            self._snapshots.pop(self.db_manager.db_name, None)

    def save_string(self, key: str, value: str) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
                conn.commit()
            self._invalidate()
            logger.debug("[SettingsStorage] Saved setting '%s'", key)
        except Exception as e:
            logger.error("[SettingsStorage] Error saving setting '%s': %s", key, e)

    def load_string(self, key: str, default: str = "") -> str:
        try:
            snapshot = self._snapshot()
        except Exception as e:
            logger.error("[SettingsStorage] Error loading setting '%s': %s", key, e)
            return default
        return snapshot[key] if key in snapshot else default

    def save_bool(self, key: str, value: bool) -> None:
        self.save_string(key, "1" if value else "0")

    def load_bool(self, key: str, default: bool = False) -> bool:
        val = self.load_string(key, None)
        return default if val is None else val == "1"
    
    def get_all(self) -> dict:
        try:
            return {k: (v == "1" if v in ("1", "0") else v) for k, v in self._snapshot().items()}
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
            self._invalidate()
            logger.debug("[SettingsStorage] Batch saved %d settings", len(data))
        except Exception as e:
            logger.error("[SettingsStorage] Error batch saving settings: %s", e)

    def delete_key_prefix(self, prefix: str) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM settings WHERE key LIKE ?", (f"{prefix}%",))
                conn.commit()
            self._invalidate()
            logger.debug("[SettingsStorage] Deleted settings matching prefix '%s'", prefix)
        except Exception as e:
            logger.error("[SettingsStorage] Error deleting settings matching prefix '%s': %s", prefix, e)
