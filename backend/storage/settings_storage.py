from backend.storage.manager import DatabaseManager

class SQLiteSettingsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_string(self, key: str, value: str) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
            conn.commit()

    def load_string(self, key: str, default: str = "") -> str:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def save_bool(self, key: str, value: bool) -> None:
        self.save_string(key, "1" if value else "0")

    def load_bool(self, key: str, default: bool = False) -> bool:
        val = self.load_string(key, None)
        return default if val is None else val == "1"
    
    def get_all(self) -> dict:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {k: (v == "1" if v in ("1", "0") else v) for k, v in cursor.fetchall()}

    def save_all(self, settings: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            for key, value in settings.items():
                str_val = "1" if value is True else "0" if value is False else str(value)
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str_val))
            conn.commit()
