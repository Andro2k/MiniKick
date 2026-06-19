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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_commands (
                    trigger TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    cooldown INTEGER DEFAULT 5,
                    aliases TEXT DEFAULT '',
                    is_regex INTEGER DEFAULT 0,
                    permission TEXT DEFAULT 'everyone'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spam_filters (
                    filter_id TEXT PRIMARY KEY,
                    is_active INTEGER DEFAULT 0,
                    penalty TEXT DEFAULT 'timeout',
                    duration INTEGER DEFAULT 300,
                    exclude_group TEXT DEFAULT 'none',
                    max_amount INTEGER DEFAULT 0
                )
            """)

            cursor.execute("PRAGMA table_info(obs_alerts)")
            columns = [info[1] for info in cursor.fetchall()]
            if "is_random_pos" not in columns:
                cursor.execute("ALTER TABLE obs_alerts ADD COLUMN is_random_pos INTEGER DEFAULT 0")
                
            cursor.execute("PRAGMA table_info(chat_commands)")
            columns = [info[1] for info in cursor.fetchall()]
            if "permission" not in columns:
                cursor.execute("ALTER TABLE chat_commands ADD COLUMN permission TEXT DEFAULT 'everyone'")
                
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
                return {"access_token": row[0], "refresh_token": row[1], "expires_in": row[2], "scope": row[3], "token_type": row[4]}
            return None

    def save(self, tokens: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens")
            cursor.execute("INSERT INTO tokens (access_token, refresh_token, expires_in, scope, token_type) VALUES (?, ?, ?, ?, ?)", 
                           (tokens.get("access_token"), tokens.get("refresh_token"), tokens.get("expires_in"), tokens.get("scope"), tokens.get("token_type")))
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

class SQLiteAlertsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> dict:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos FROM obs_alerts")
            return {r[0]: {"filepath": r[1], "volume": r[2], "scale": r[3], "pos_x": r[4], "pos_y": r[5], "is_random_pos": bool(r[6])} for r in cursor.fetchall()}

    def save_all(self, mappings: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM obs_alerts")
            for reward, conf in mappings.items():
                cursor.execute("INSERT INTO obs_alerts (reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (reward, conf.get("filepath", ""), conf.get("volume", 1.0), conf.get("scale", 1.0), conf.get("pos_x", 0), conf.get("pos_y", 0), int(conf.get("is_random_pos", False))))
            conn.commit()

class SQLiteCommandsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT trigger, response, is_active, cooldown, aliases, is_regex, permission FROM chat_commands")
            return [{"trigger": r[0], "response": r[1], "is_active": bool(r[2]), "cooldown": r[3], "aliases": r[4], "is_regex": bool(r[5]), "permission": r[6]} for r in cursor.fetchall()]

    def save_command(self, trigger: str, response: str, is_active: bool, cooldown: int, aliases: str, is_regex: bool, permission: str = "everyone") -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_commands (trigger, response, is_active, cooldown, aliases, is_regex, permission) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trigger) DO UPDATE SET 
                    response=excluded.response, is_active=excluded.is_active, cooldown=excluded.cooldown,
                    aliases=excluded.aliases, is_regex=excluded.is_regex, permission=excluded.permission
            """, (trigger, response, int(is_active), cooldown, aliases, int(is_regex), permission))
            conn.commit()

    def delete_command(self, trigger: str) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_commands WHERE trigger=?", (trigger,))
            conn.commit()

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