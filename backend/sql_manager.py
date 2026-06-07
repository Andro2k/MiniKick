# backend/sql_manager.py

import os
import sqlite3

class DatabaseManager:
    def __init__(self, db_name="minikick.db"):
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        self.db_dir = os.path.join(app_data_dir, '.Minikick')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_name = os.path.join(self.db_dir, db_name)
        self._create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def _create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    access_token TEXT,
                    refresh_token TEXT,
                    expires_in INTEGER,
                    scope TEXT,
                    token_type TEXT
                )
            """)        
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)           
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obs_alerts (
                    reward_name TEXT PRIMARY KEY,
                    filepath TEXT NOT NULL,
                    volume REAL DEFAULT 1.0,
                    scale REAL DEFAULT 1.0,
                    pos_x INTEGER DEFAULT 0,
                    pos_y INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("PRAGMA table_info(obs_alerts)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if "is_random_pos" not in columns:
                print("🔄 Actualizando base de datos")
                cursor.execute("ALTER TABLE obs_alerts ADD COLUMN is_random_pos INTEGER DEFAULT 0")
                
            conn.commit()

class SQLiteTokenStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load(self) -> dict | None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT access_token, refresh_token, expires_in, scope, token_type FROM tokens ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return {
                    "access_token": row[0],
                    "refresh_token": row[1],
                    "expires_in": row[2],
                    "scope": row[3],
                    "token_type": row[4]
                }
            return None

    def save(self, tokens: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens")
            cursor.execute("""
                INSERT INTO tokens (access_token, refresh_token, expires_in, scope, token_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                tokens.get("access_token"),
                tokens.get("refresh_token"),
                tokens.get("expires_in"),
                tokens.get("scope"),
                tokens.get("token_type"),
            ))
            conn.commit()

    def clear(self) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens")
            conn.commit()

class SQLiteSettingsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def save_string(self, key: str, value: str) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, value))
            conn.commit()

    def load_string(self, key: str, default: str = "") -> str:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return default

    def save_bool(self, key: str, value: bool) -> None:
        self.save_string(key, "1" if value else "0")

    def load_bool(self, key: str, default: bool = False) -> bool:
        val = self.load_string(key, None)
        if val is None:
            return default
        return val == "1"

class SQLiteAlertsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> dict:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos FROM obs_alerts")
            rows = cursor.fetchall()
            
            mappings = {}
            for row in rows:
                mappings[row[0]] = {
                    "filepath": row[1],
                    "volume": row[2],
                    "scale": row[3],
                    "pos_x": row[4],
                    "pos_y": row[5],
                    "is_random_pos": bool(row[6])
                }
            return mappings

    def save_all(self, mappings: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM obs_alerts")
            
            for reward, config in mappings.items():
                cursor.execute("""
                    INSERT INTO obs_alerts (reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    reward,
                    config.get("filepath", ""),
                    config.get("volume", 1.0),
                    config.get("scale", 1.0),
                    config.get("pos_x", 0),
                    config.get("pos_y", 0),
                    int(config.get("is_random_pos", False))
                ))
            conn.commit()