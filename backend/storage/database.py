# backend\storage\database.py

import os
import sqlite3

class DatabaseManager:
    def __init__(self, db_name="minikick.db"):
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        self.db_dir = os.path.join(app_data_dir, '.Minikick')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_name = os.path.join(self.db_dir, db_name)
        
        try:
            if os.path.exists(self.db_name):
                conn = sqlite3.connect(self.db_name)
                try:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    res = cursor.fetchone()
                    if not res or res[0] != "ok":
                        raise sqlite3.DatabaseError("Database integrity check failed")
                finally:
                    conn.close()
            self._create_tables()
        except sqlite3.DatabaseError as e:
            import logging
            logger = logging.getLogger("minikick.database")
            logger.error("Database file is malformed at startup, recreating: %s", e)
            self._handle_corrupt_database()

    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-20000")
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except sqlite3.DatabaseError as e:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            if "malformed" in str(e).lower() or "corrupt" in str(e).lower():
                import logging
                logger = logging.getLogger("minikick.database")
                logger.error("Database error in get_connection, recreating database: %s", e)
                self._handle_corrupt_database()
                return sqlite3.connect(self.db_name)
            else:
                raise e

    def _handle_corrupt_database(self):
        import logging
        logger = logging.getLogger("minikick.database")
        for ext in ("", "-wal", "-shm"):
            file_path = self.db_name + ext
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info("Deleted corrupt database file: %s", file_path)
                except Exception as del_err:
                    logger.warning("Could not delete database file %s: %s", file_path, del_err)
        self._create_tables()

    def _create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT DEFAULT 'kick',
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
                CREATE TABLE IF NOT EXISTS obs_rewards (
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_timers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    messages TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    interval_online INTEGER,
                    interval_offline INTEGER,
                    chat_lines INTEGER DEFAULT 0,
                    keywords TEXT DEFAULT '[]',
                    categories TEXT DEFAULT '[]'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_trigger TEXT NOT NULL,
                    username TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (command_trigger) REFERENCES chat_commands(trigger) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_command_logs AFTER INSERT ON command_execution_logs
                BEGIN
                    DELETE FROM command_execution_logs WHERE timestamp < datetime('now', '-30 days');
                END;
            """)
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS command_analytics AS
                SELECT 
                    c.trigger,
                    c.response,
                    c.is_active,
                    COUNT(l.id) AS usage_count,
                    MAX(l.timestamp) AS last_used
                FROM chat_commands c
                LEFT JOIN command_execution_logs l ON c.trigger = l.command_trigger
                GROUP BY c.trigger
            """)
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS active_features_summary AS
                SELECT 
                    (SELECT COUNT(*) FROM chat_commands) AS total_commands,
                    (SELECT COUNT(*) FROM chat_commands WHERE is_active = 1) AS active_commands,
                    (SELECT COUNT(*) FROM chat_timers) AS total_timers,
                    (SELECT COUNT(*) FROM chat_timers WHERE is_active = 1) AS active_timers,
                    (SELECT COUNT(*) FROM command_execution_logs) AS total_command_usages
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS youtube_search_cache (
                    query_raw TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    url TEXT NOT NULL,
                    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS avatar_cache (
                    url TEXT PRIMARY KEY,
                    image_bytes BLOB NOT NULL,
                    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_youtube_cache AFTER INSERT ON youtube_search_cache
                BEGIN
                    DELETE FROM youtube_search_cache WHERE cached_at < datetime('now', '-15 days');
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_avatar_cache AFTER INSERT ON avatar_cache
                BEGIN
                    DELETE FROM avatar_cache WHERE cached_at < datetime('now', '-15 days');
                END;
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_system_logs AFTER INSERT ON system_logs
                WHEN (SELECT COUNT(*) FROM system_logs) > 2000
                BEGIN
                    DELETE FROM system_logs WHERE id IN (
                        SELECT id FROM system_logs ORDER BY id ASC LIMIT (SELECT COUNT(*) - 2000 FROM system_logs)
                    );
                END;
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spam_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    sender_id INTEGER NOT NULL,
                    filter_id TEXT NOT NULL,
                    message_content TEXT,
                    penalty_type TEXT NOT NULL,
                    duration INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spam_violations_user ON spam_violations(username)")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS timer_execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timer_id INTEGER NOT NULL,
                    message_sent TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(timer_id) REFERENCES chat_timers(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timer_logs_timer ON timer_execution_logs(timer_id)")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS music_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    url TEXT NOT NULL,
                    requester TEXT,
                    provider TEXT NOT NULL,
                    is_played INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reward_redemptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reward_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(reward_name) REFERENCES obs_rewards(reward_name) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reward_redemptions_name ON reward_redemptions(reward_name)")
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_spam_violations AFTER INSERT ON spam_violations
                WHEN (SELECT COUNT(*) FROM spam_violations) > 1000
                BEGIN
                    DELETE FROM spam_violations WHERE id IN (
                        SELECT id FROM spam_violations ORDER BY id ASC LIMIT (SELECT COUNT(*) - 1000 FROM spam_violations)
                    );
                END;
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_timer_logs AFTER INSERT ON timer_execution_logs
                WHEN (SELECT COUNT(*) FROM timer_execution_logs) > 1000
                BEGIN
                    DELETE FROM timer_execution_logs WHERE id IN (
                        SELECT id FROM timer_execution_logs ORDER BY id ASC LIMIT (SELECT COUNT(*) - 1000 FROM timer_execution_logs)
                    );
                END;
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_music_queue AFTER INSERT ON music_queue
                WHEN (SELECT COUNT(*) FROM music_queue WHERE is_played = 2) > 100
                BEGIN
                    DELETE FROM music_queue WHERE id IN (
                        SELECT id FROM music_queue WHERE is_played = 2 ORDER BY id ASC LIMIT (SELECT COUNT(*) - 100 FROM music_queue WHERE is_played = 2)
                    );
                END;
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_reward_redemptions AFTER INSERT ON reward_redemptions
                WHEN (SELECT COUNT(*) FROM reward_redemptions) > 1000
                BEGIN
                    DELETE FROM reward_redemptions WHERE id IN (
                        SELECT id FROM reward_redemptions ORDER BY id ASC LIMIT (SELECT COUNT(*) - 1000 FROM reward_redemptions)
                    );
                END;
            """)

            cursor.execute("PRAGMA table_info(obs_rewards)")
            columns = [info[1] for info in cursor.fetchall()]
            if "is_random_pos" not in columns:
                cursor.execute("ALTER TABLE obs_rewards ADD COLUMN is_random_pos INTEGER DEFAULT 0")
            cursor.execute("PRAGMA table_info(chat_commands)")
            columns = [info[1] for info in cursor.fetchall()]
            if "permission" not in columns:
                cursor.execute("ALTER TABLE chat_commands ADD COLUMN permission TEXT DEFAULT 'everyone'")
            cursor.execute("PRAGMA table_info(tokens)")
            columns = [info[1] for info in cursor.fetchall()]
            if "provider" not in columns:
                cursor.execute("ALTER TABLE tokens ADD COLUMN provider TEXT DEFAULT 'kick'")
                
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_provider ON tokens (provider)")
            conn.commit()

    def log_spam_violation(self, username: str, sender_id: int, filter_id: str, message_content: str, penalty_type: str, duration: int) -> None:
        try:
            from datetime import datetime
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO spam_violations (username, sender_id, filter_id, message_content, penalty_type, duration, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (username, sender_id, filter_id, message_content, penalty_type, duration, local_now)
                )
                conn.commit()
        except Exception as e:
            import logging
            logging.error("[DatabaseManager] Error logging spam violation: %s", e)

    def log_timer_execution(self, timer_id: int, message_sent: str) -> None:
        try:
            from datetime import datetime
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO timer_execution_logs (timer_id, message_sent, timestamp) VALUES (?, ?, ?)",
                    (timer_id, message_sent, local_now)
                )
                conn.commit()
        except Exception as e:
            import logging
            logging.error("[DatabaseManager] Error logging timer execution: %s", e)

    def log_reward_redemption(self, reward_name: str, username: str) -> None:
        try:
            from datetime import datetime
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reward_redemptions (reward_name, username, timestamp) VALUES (?, ?, ?)",
                    (reward_name, username, local_now)
                )
                conn.commit()
        except Exception as e:
            import logging
            logging.error("[DatabaseManager] Error logging reward redemption: %s", e)

    def add_song_to_queue(self, title: str, artist: str, url: str, requester: str, provider: str) -> int:
        try:
            from datetime import datetime
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO music_queue (title, artist, url, requester, provider, is_played, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
                    (title, artist, url, requester, provider, local_now)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            import logging
            logging.error("[DatabaseManager] Error adding song to queue: %s", e)
        return -1

    def update_song_status(self, db_id: int, status: int) -> None:
        if db_id is None or db_id < 0:
            return
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE music_queue SET is_played = ? WHERE id = ?", (status, db_id))
                conn.commit()
        except Exception as e:
            import logging
            logging.error("[DatabaseManager] Error updating song status: %s", e)

    def load_pending_songs(self, provider: str) -> list[dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, artist, url, requester, provider FROM music_queue WHERE provider = ? AND is_played = 0 ORDER BY id ASC",
                    (provider,)
                )
                return [
                    {
                        "db_id": r[0],
                        "title": r[1],
                        "artist": r[2],
                        "url": r[3],
                        "requester": r[4],
                        "provider": r[5]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            import logging
            logging.error("[DatabaseManager] Error loading pending songs: %s", e)
        return []

class SQLiteTokenStorage:
    def __init__(self, db_manager: DatabaseManager, provider: str = "kick"):
        self.db_manager = db_manager
        self.provider = provider

    def load(self) -> dict | None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT access_token, refresh_token, expires_in, scope, token_type FROM tokens WHERE provider = ? ORDER BY id DESC LIMIT 1",
                (self.provider,)
            )
            row = cursor.fetchone()
            if row:
                return {"access_token": row[0], "refresh_token": row[1], "expires_in": row[2], "scope": row[3], "token_type": row[4]}
            return None

    def save(self, tokens: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens WHERE provider = ?", (self.provider,))
            cursor.execute(
                "INSERT INTO tokens (provider, access_token, refresh_token, expires_in, scope, token_type) VALUES (?, ?, ?, ?, ?, ?)", 
                (self.provider, tokens.get("access_token"), tokens.get("refresh_token"), tokens.get("expires_in"), tokens.get("scope"), tokens.get("token_type"))
            )
            conn.commit()

    def clear(self) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens WHERE provider = ?", (self.provider,))
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

class SQLiteRewardsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> dict:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos FROM obs_rewards")
            return {r[0]: {"filepath": r[1], "volume": r[2], "scale": r[3], "pos_x": r[4], "pos_y": r[5], "is_random_pos": bool(r[6])} for r in cursor.fetchall()}

    def save_all(self, mappings: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM obs_rewards")
            for reward, conf in mappings.items():
                cursor.execute("INSERT INTO obs_rewards (reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
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

    def search_commands(self, query: str) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{query.strip().lower()}%"
            cursor.execute("""
                SELECT trigger, response, is_active, cooldown, aliases, is_regex, permission 
                FROM chat_commands 
                WHERE LOWER(trigger) LIKE ? OR LOWER(response) LIKE ? OR LOWER(aliases) LIKE ?
            """, (pattern, pattern, pattern))
            return [{"trigger": r[0], "response": r[1], "is_active": bool(r[2]), "cooldown": r[3], "aliases": r[4], "is_regex": bool(r[5]), "permission": r[6]} for r in cursor.fetchall()]

    def log_command_execution(self, trigger: str, username: str) -> None:
        from datetime import datetime
        local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO command_execution_logs (command_trigger, username, timestamp) VALUES (?, ?, ?)", (trigger, username, local_now))
            conn.commit()

    def get_command_analytics(self) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT trigger, response, is_active, usage_count, last_used FROM command_analytics ORDER BY usage_count DESC")
            return [{"trigger": r[0], "response": r[1], "is_active": bool(r[2]), "usage_count": r[3], "last_used": r[4]} for r in cursor.fetchall()]

    def get_active_features_summary(self) -> dict:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_commands, active_commands, total_timers, active_timers, total_command_usages FROM active_features_summary")
            r = cursor.fetchone()
            if r:
                return {
                    "total_commands": r[0],
                    "active_commands": r[1],
                    "total_timers": r[2],
                    "active_timers": r[3],
                    "total_command_usages": r[4]
                }
            return {
                "total_commands": 0,
                "active_commands": 0,
                "total_timers": 0,
                "active_timers": 0,
                "total_command_usages": 0
            }

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

class SQLiteTimersStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories FROM chat_timers")
            import json
            timers = []
            for r in cursor.fetchall():
                try:
                    messages = json.loads(r[2])
                except Exception:
                    messages = [r[2]] if r[2] else []
                try:
                    keywords = json.loads(r[7])
                except Exception:
                    keywords = [k.strip() for k in r[7].split(",") if k.strip()] if r[7] else []
                try:
                    categories = json.loads(r[8])
                except Exception:
                    categories = [c.strip() for c in r[8].split(",") if c.strip()] if r[8] else []

                timers.append({
                    "id": r[0],
                    "name": r[1],
                    "messages": messages,
                    "is_active": bool(r[3]),
                    "interval_online": r[4],
                    "interval_offline": r[5],
                    "chat_lines": r[6],
                    "keywords": keywords,
                    "categories": categories
                })
            return timers

    def save_timer(self, name: str, messages: list[str], is_active: bool, interval_online: int, interval_offline: int, chat_lines: int, keywords: list[str], categories: list[str], timer_id: int = None) -> None:
        import json
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            messages_json = json.dumps(messages)
            keywords_json = json.dumps(keywords)
            categories_json = json.dumps(categories)
            if timer_id is not None:
                cursor.execute("""
                    INSERT INTO chat_timers (id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name, messages=excluded.messages, is_active=excluded.is_active,
                        interval_online=excluded.interval_online, interval_offline=excluded.interval_offline,
                        chat_lines=excluded.chat_lines, keywords=excluded.keywords, categories=excluded.categories
                """, (timer_id, name, messages_json, int(is_active), interval_online, interval_offline, chat_lines, keywords_json, categories_json))
            else:
                cursor.execute("""
                    INSERT INTO chat_timers (name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        messages=excluded.messages, is_active=excluded.is_active,
                        interval_online=excluded.interval_online, interval_offline=excluded.interval_offline,
                        chat_lines=excluded.chat_lines, keywords=excluded.keywords, categories=excluded.categories
                """, (name, messages_json, int(is_active), interval_online, interval_offline, chat_lines, keywords_json, categories_json))
            conn.commit()

    def delete_timer(self, timer_id: int) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_timers WHERE id=?", (timer_id,))
            conn.commit()

    def search_timers(self, query: str) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{query.strip().lower()}%"
            cursor.execute("""
                SELECT id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories 
                FROM chat_timers 
                WHERE LOWER(name) LIKE ? OR LOWER(messages) LIKE ?
            """, (pattern, pattern))
            import json
            timers = []
            for r in cursor.fetchall():
                try:
                    messages = json.loads(r[2])
                except Exception:
                    messages = [r[2]] if r[2] else []
                try:
                    keywords = json.loads(r[7])
                except Exception:
                    keywords = [k.strip() for k in r[7].split(",") if k.strip()] if r[7] else []
                try:
                    categories = json.loads(r[8])
                except Exception:
                    categories = [c.strip() for c in r[8].split(",") if c.strip()] if r[8] else []

                timers.append({
                    "id": r[0],
                    "name": r[1],
                    "messages": messages,
                    "is_active": bool(r[3]),
                    "interval_online": r[4],
                    "interval_offline": r[5],
                    "chat_lines": r[6],
                    "keywords": keywords,
                    "categories": categories
                })
            return timers