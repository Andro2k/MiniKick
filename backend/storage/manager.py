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
