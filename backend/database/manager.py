# backend\database\manager.py

import os
import json
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger("minikick.database")

class AutoCloseConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()

class DatabaseManager:
    def __init__(self, db_name="minikick.db"):
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        self.db_dir = os.path.join(app_data_dir, '.Minikick')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_name = os.path.join(self.db_dir, db_name)
        
        self._initialize_database()

    def _initialize_database(self) -> None:
        try:
            if os.path.exists(self.db_name):
                with sqlite3.connect(self.db_name, timeout=10.0, factory=AutoCloseConnection) as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    res = cursor.fetchone()
                    if not res or res[0] != "ok":
                        raise sqlite3.DatabaseError("Database integrity check failed")
            
            with sqlite3.connect(self.db_name, timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL")

            self._create_tables()
            self._upgrade_schema()
            self._create_indexes_and_views()
        except sqlite3.DatabaseError as e:
            if "malformed" in str(e).lower() or "corrupt" in str(e).lower() or "integrity" in str(e).lower():
                logger.error("Database file is malformed at startup, recreating: %s", e)
                self._handle_corrupt_database()
            else:
                logger.error("Database initialization error: %s", e)
                raise e

    def get_connection(self) -> sqlite3.Connection:
        conn = None
        try:
            conn = sqlite3.connect(self.db_name, timeout=10.0, factory=AutoCloseConnection)
            conn.execute("PRAGMA busy_timeout=5000")
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
                logger.error("Database error in get_connection, recreating database: %s", e)
                self._handle_corrupt_database()
                return sqlite3.connect(self.db_name, timeout=10.0, factory=AutoCloseConnection)
            raise e

    def _handle_corrupt_database(self) -> None:
        for ext in ("", "-wal", "-shm"):
            file_path = self.db_name + ext
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info("Deleted corrupt database file: %s", file_path)
                except Exception as del_err:
                    logger.warning("Could not delete database file %s: %s", file_path, del_err)
        self._create_tables()
        self._upgrade_schema()
        self._create_indexes_and_views()

    def _create_tables(self) -> None:
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
                    pos_y INTEGER DEFAULT 0,
                    is_random_pos INTEGER DEFAULT 0,
                    thumbnail_bytes BLOB,
                    reward_id TEXT,
                    cost INTEGER DEFAULT 100,
                    description TEXT DEFAULT '',
                    background_color TEXT DEFAULT '#00e701',
                    is_user_input_required INTEGER DEFAULT 0,
                    platform TEXT DEFAULT 'kick'
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
                    permission TEXT DEFAULT 'everyone',
                    apply_kick INTEGER DEFAULT 1,
                    apply_twitch INTEGER DEFAULT 1,
                    apply_youtube INTEGER DEFAULT 1,
                    apply_tiktok INTEGER DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spam_filters (
                    filter_id TEXT PRIMARY KEY,
                    is_active INTEGER DEFAULT 0,
                    penalty TEXT DEFAULT 'timeout',
                    duration INTEGER DEFAULT 5,
                    exclude_group TEXT DEFAULT 'none',
                    max_amount INTEGER DEFAULT 0,
                    allowlist TEXT DEFAULT '',
                    apply_kick INTEGER DEFAULT 1,
                    apply_twitch INTEGER DEFAULT 1,
                    apply_youtube INTEGER DEFAULT 1
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
                    categories TEXT DEFAULT '[]',
                    apply_kick INTEGER DEFAULT 1,
                    apply_twitch INTEGER DEFAULT 1,
                    apply_youtube INTEGER DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_trigger TEXT NOT NULL,
                    username TEXT NOT NULL,
                    platform TEXT DEFAULT 'kick',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (command_trigger) REFERENCES chat_commands(trigger) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS youtube_search_cache (
                    query_raw TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    url TEXT NOT NULL,
                    duration TEXT DEFAULT '-',
                    play_count INTEGER DEFAULT 1,
                    last_accessed TEXT,
                    file_size_mb REAL DEFAULT 4.0,
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
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS widgets_config (
                    widget_id TEXT PRIMARY KEY,
                    is_active INTEGER DEFAULT 1,
                    command TEXT NOT NULL,
                    cooldown INTEGER DEFAULT 3,
                    permission TEXT DEFAULT 'everyone',
                    config_json TEXT DEFAULT '{}'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spam_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    filter_id TEXT NOT NULL,
                    message_content TEXT,
                    penalty_type TEXT NOT NULL,
                    duration INTEGER,
                    platform TEXT DEFAULT 'kick',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS timer_execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timer_id INTEGER NOT NULL,
                    message_sent TEXT NOT NULL,
                    platform TEXT DEFAULT 'all',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(timer_id) REFERENCES chat_timers(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stream_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date_str TEXT DEFAULT '',
                    time_str TEXT NOT NULL,
                    target_platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    kick_category_id INTEGER,
                    kick_category_name TEXT,
                    twitch_category_id TEXT,
                    twitch_category_name TEXT,
                    is_active INTEGER DEFAULT 1,
                    last_executed_date TEXT DEFAULT ''
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS music_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    url TEXT NOT NULL,
                    requester TEXT,
                    provider TEXT NOT NULL,
                    platform TEXT DEFAULT 'kick',
                    is_played INTEGER DEFAULT 0,
                    duration TEXT DEFAULT '-',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reward_redemptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reward_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    platform TEXT DEFAULT 'kick',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(reward_name) REFERENCES obs_rewards(reward_name) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_profiles (
                    platform TEXT PRIMARY KEY,
                    username TEXT,
                    bio TEXT,
                    avatar_url TEXT,
                    followers INTEGER DEFAULT 0,
                    room_id TEXT,
                    category TEXT,
                    affiliate_status TEXT,
                    vods_enabled INTEGER DEFAULT 0,
                    created_at TEXT,
                    raw_json TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_configs (
                    platform TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    sound_path TEXT DEFAULT '',
                    media_path TEXT DEFAULT '',
                    text_template TEXT DEFAULT '{user}',
                    duration_ms INTEGER NOT NULL DEFAULT 5000,
                    sound_volume REAL NOT NULL DEFAULT 0.8,
                    tts_read INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (platform, alert_type)
                )
            """)
            conn.commit()

    def _create_indexes_and_views(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_provider ON tokens (provider)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_logs_trigger ON command_execution_logs(command_trigger)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_logs_timestamp ON command_execution_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_logs_platform ON command_execution_logs(platform)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_logs_level_timestamp ON system_logs(level, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_youtube_cache_play_count ON youtube_search_cache(play_count DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spam_violations_user ON spam_violations(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spam_violations_filter ON spam_violations(filter_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spam_violations_ts ON spam_violations(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spam_violations_platform_ts ON spam_violations(platform, timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timer_logs_timer ON timer_execution_logs(timer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timer_logs_platform ON timer_execution_logs(platform)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_music_queue_provider_status_id ON music_queue(provider, is_played, id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reward_redemptions_name ON reward_redemptions(reward_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reward_redemptions_platform ON reward_redemptions(platform)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reward_redemptions_name_ts ON reward_redemptions(reward_name, timestamp DESC)")

            try:
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS youtube_search_cache_fts USING fts5(
                        query_raw,
                        title,
                        artist,
                        tokenize='trigram'
                    )
                """)
                cursor.execute("DROP TRIGGER IF EXISTS trg_yt_cache_delete")
                cursor.execute("DROP TRIGGER IF EXISTS trg_yt_cache_update")
                cursor.execute("DROP TRIGGER IF EXISTS trg_yt_cache_insert")

                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_yt_cache_insert AFTER INSERT ON youtube_search_cache BEGIN
                        INSERT INTO youtube_search_cache_fts(rowid, query_raw, title, artist)
                        VALUES (new.rowid, new.query_raw, new.title, new.artist);
                    END;
                """)
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_yt_cache_delete AFTER DELETE ON youtube_search_cache BEGIN
                        DELETE FROM youtube_search_cache_fts WHERE rowid = old.rowid;
                    END;
                """)
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_yt_cache_update AFTER UPDATE OF query_raw, title, artist ON youtube_search_cache BEGIN
                        DELETE FROM youtube_search_cache_fts WHERE rowid = old.rowid;
                        INSERT INTO youtube_search_cache_fts(rowid, query_raw, title, artist)
                        VALUES (new.rowid, new.query_raw, new.title, new.artist);
                    END;
                """)
                cursor.execute("""
                    INSERT INTO youtube_search_cache_fts(rowid, query_raw, title, artist)
                    SELECT rowid, query_raw, title, artist FROM youtube_search_cache
                    WHERE rowid NOT IN (SELECT rowid FROM youtube_search_cache_fts)
                """)
            except Exception as fts_init_err:
                logger.debug("[DatabaseManager] FTS5 trigram initialization note: %s", fts_init_err)

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
                CREATE TRIGGER IF NOT EXISTS prune_command_logs AFTER INSERT ON command_execution_logs
                BEGIN
                    DELETE FROM command_execution_logs WHERE timestamp < datetime('now', '-30 days');
                END;
            """)
            cursor.execute("DROP TRIGGER IF EXISTS prune_youtube_cache")
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_avatar_cache AFTER INSERT ON avatar_cache
                BEGIN
                    DELETE FROM avatar_cache WHERE cached_at < datetime('now', '-15 days');
                END;
            """)
            
            cursor.execute("DROP TRIGGER IF EXISTS prune_system_logs")
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_system_logs AFTER INSERT ON system_logs
                BEGIN
                    DELETE FROM system_logs WHERE id <= (NEW.id - 2000);
                END;
            """)
            
            cursor.execute("DROP TRIGGER IF EXISTS prune_spam_violations")
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_spam_violations AFTER INSERT ON spam_violations
                BEGIN
                    DELETE FROM spam_violations WHERE id <= (NEW.id - 1000);
                END;
            """)
            
            cursor.execute("DROP TRIGGER IF EXISTS prune_timer_logs")
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_timer_logs AFTER INSERT ON timer_execution_logs
                BEGIN
                    DELETE FROM timer_execution_logs WHERE id <= (NEW.id - 1000);
                END;
            """)
            
            cursor.execute("DROP TRIGGER IF EXISTS prune_music_queue")
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_music_queue AFTER INSERT ON music_queue
                WHEN NEW.is_played = 2
                BEGIN
                    DELETE FROM music_queue WHERE is_played = 2 AND id <= (NEW.id - 100);
                END;
            """)
            
            cursor.execute("DROP TRIGGER IF EXISTS prune_reward_redemptions")
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prune_reward_redemptions AFTER INSERT ON reward_redemptions
                BEGIN
                    DELETE FROM reward_redemptions WHERE id <= (NEW.id - 1000);
                END;
            """)
            conn.commit()

    def _upgrade_schema(self) -> None:
        expected_columns = {
            "spam_filters": [
                ("apply_kick", "INTEGER DEFAULT 1"),
                ("apply_twitch", "INTEGER DEFAULT 1"),
                ("apply_youtube", "INTEGER DEFAULT 1"),
                ("allowlist", "TEXT DEFAULT ''"),
                ("max_amount", "INTEGER DEFAULT 0"),
                ("exclude_group", "TEXT DEFAULT 'none'"),
                ("duration", "INTEGER DEFAULT 5"),
                ("penalty", "TEXT DEFAULT 'timeout'"),
                ("is_active", "INTEGER DEFAULT 0")
            ],
            "chat_commands": [
                ("is_active", "INTEGER DEFAULT 1"),
                ("cooldown", "INTEGER DEFAULT 5"),
                ("aliases", "TEXT DEFAULT ''"),
                ("is_regex", "INTEGER DEFAULT 0"),
                ("permission", "TEXT DEFAULT 'everyone'"),
                ("apply_kick", "INTEGER DEFAULT 1"),
                ("apply_twitch", "INTEGER DEFAULT 1"),
                ("apply_youtube", "INTEGER DEFAULT 1"),
                ("apply_tiktok", "INTEGER DEFAULT 1")
            ],
            "obs_rewards": [
                ("volume", "REAL DEFAULT 1.0"),
                ("scale", "REAL DEFAULT 1.0"),
                ("pos_x", "INTEGER DEFAULT 0"),
                ("pos_y", "INTEGER DEFAULT 0"),
                ("is_random_pos", "INTEGER DEFAULT 0"),
                ("thumbnail_bytes", "BLOB"),
                ("reward_id", "TEXT"),
                ("cost", "INTEGER DEFAULT 100"),
                ("description", "TEXT DEFAULT ''"),
                ("background_color", "TEXT DEFAULT '#00e701'"),
                ("is_user_input_required", "INTEGER DEFAULT 0"),
                ("platform", "TEXT DEFAULT 'kick'")
            ],
            "stream_schedules": [
                ("date_str", "TEXT DEFAULT ''"),
                ("days", "TEXT DEFAULT ''")
            ],
            "chat_timers": [
                ("apply_kick", "INTEGER DEFAULT 1"),
                ("apply_twitch", "INTEGER DEFAULT 1"),
                ("apply_youtube", "INTEGER DEFAULT 1"),
                ("is_active", "INTEGER DEFAULT 1"),
                ("interval_online", "INTEGER"),
                ("interval_offline", "INTEGER"),
                ("chat_lines", "INTEGER DEFAULT 0"),
                ("keywords", "TEXT DEFAULT '[]'"),
                ("categories", "TEXT DEFAULT '[]'")
            ],
            "youtube_search_cache": [
                ("duration", "TEXT DEFAULT '-'"),
                ("play_count", "INTEGER DEFAULT 1"),
                ("last_accessed", "TEXT"),
                ("file_size_mb", "REAL DEFAULT 4.0")
            ],
            "music_queue": [
                ("duration", "TEXT DEFAULT '-'"),
                ("platform", "TEXT DEFAULT 'kick'")
            ],
            "command_execution_logs": [
                ("platform", "TEXT DEFAULT 'kick'")
            ],
            "spam_violations": [
                ("platform", "TEXT DEFAULT 'kick'")
            ],
            "timer_execution_logs": [
                ("platform", "TEXT DEFAULT 'all'")
            ],
            "reward_redemptions": [
                ("platform", "TEXT DEFAULT 'kick'")
            ]
        }

        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for table, cols in expected_columns.items():
                    cursor.execute(f"PRAGMA table_info({table})")
                    current_cols = {row[1].lower() for row in cursor.fetchall()}
                    if not current_cols:
                        continue
                    for col_name, col_type in cols:
                        if col_name.lower() not in current_cols:
                            logger.info("Upgrading table %s: adding column %s", table, col_name)
                            try:
                                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                            except sqlite3.OperationalError as alter_err:
                                logger.error("Error adding column %s to table %s: %s", col_name, table, alter_err)
                conn.commit()
        except Exception as e:
            logger.error("Error executing database schema upgrade: %s", e)

    def log_spam_violation(self, username: str, sender_id: str | int, filter_id: str, message_content: str, penalty_type: str, duration: int, platform: str = "kick") -> None:
        try:
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO spam_violations (username, sender_id, filter_id, message_content, penalty_type, duration, platform, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (username, str(sender_id), filter_id, message_content, penalty_type, duration, platform or "kick", local_now)
                )
                conn.commit()
        except Exception as e:
            logger.error("[DatabaseManager] Error logging spam violation: %s", e)

    def log_timer_execution(self, timer_id: int, message_sent: str, platform: str = "all") -> None:
        try:
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO timer_execution_logs (timer_id, message_sent, platform, timestamp) VALUES (?, ?, ?, ?)",
                    (timer_id, message_sent, platform or "all", local_now)
                )
                conn.commit()
        except Exception as e:
            logger.error("[DatabaseManager] Error logging timer execution: %s", e)

    def log_reward_redemption(self, reward_name: str, username: str, platform: str = "kick") -> None:
        try:
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reward_redemptions (reward_name, username, platform, timestamp) VALUES (?, ?, ?, ?)",
                    (reward_name, username, platform or "kick", local_now)
                )
                conn.commit()
        except Exception as e:
            logger.error("[DatabaseManager] Error logging reward redemption: %s", e)

    def log_command_execution(self, trigger: str, username: str, platform: str = "kick") -> None:
        try:
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO command_execution_logs (command_trigger, username, platform, timestamp) VALUES (?, ?, ?, ?)",
                    (trigger, username, platform or "kick", local_now)
                )
                conn.commit()
        except Exception as e:
            logger.error("[DatabaseManager] Error logging command execution: %s", e)

    def add_song_to_queue(self, title: str, artist: str, url: str, requester: str, provider: str, platform: str = "kick", duration: str = "-") -> int:
        try:
            local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO music_queue (title, artist, url, requester, provider, platform, is_played, duration, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                    (title, artist, url, requester, provider, platform or "kick", duration, local_now)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error("[DatabaseManager] Error adding song to queue: %s", e)
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
            logger.error("[DatabaseManager] Error updating song status: %s", e)

    def load_pending_songs(self, provider: str) -> list[dict]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, title, artist, url, requester, provider, duration, platform FROM music_queue WHERE provider = ? AND is_played = 0 ORDER BY id ASC",
                    (provider,)
                )
                return [
                    {
                        "db_id": r[0],
                        "title": r[1],
                        "artist": r[2],
                        "url": r[3],
                        "requester": r[4],
                        "provider": r[5],
                        "duration": r[6],
                        "platform": r[7] if len(r) > 7 and r[7] else "kick"
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            logger.error("[DatabaseManager] Error loading pending songs: %s", e)
        return []

    def get_dashboard_analytics_summary(self) -> dict:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT command_trigger, COUNT(id) as cnt
                    FROM command_execution_logs
                    GROUP BY command_trigger
                    ORDER BY cnt DESC
                    LIMIT 5
                """)
                top_commands = [{"trigger": r[0], "count": r[1]} for r in cursor.fetchall()]
                
                cursor.execute("""
                    SELECT platform, COUNT(id) as cnt
                    FROM command_execution_logs
                    GROUP BY platform
                """)
                platform_cmds = {r[0]: r[1] for r in cursor.fetchall()}
                
                cursor.execute("""
                    SELECT platform, COUNT(id) as cnt
                    FROM reward_redemptions
                    GROUP BY platform
                """)
                platform_redemptions = {r[0]: r[1] for r in cursor.fetchall()}
                total_redemptions = sum(platform_redemptions.values())
                
                cursor.execute("""
                    SELECT platform, COUNT(id) as cnt
                    FROM spam_violations
                    GROUP BY platform
                """)
                platform_spam = {r[0]: r[1] for r in cursor.fetchall()}
                total_spam = sum(platform_spam.values())
                
                cursor.execute("SELECT COUNT(*) FROM chat_commands WHERE is_active = 1")
                active_commands = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM chat_timers WHERE is_active = 1")
                active_timers = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM obs_rewards")
                total_rewards = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM command_execution_logs")
                total_command_usages = cursor.fetchone()[0]

                return {
                    "top_commands": top_commands,
                    "platform_cmds": platform_cmds,
                    "platform_redemptions": platform_redemptions,
                    "total_redemptions": total_redemptions,
                    "platform_spam": platform_spam,
                    "total_spam": total_spam,
                    "active_commands": active_commands,
                    "active_timers": active_timers,
                    "total_rewards": total_rewards,
                    "total_command_usages": total_command_usages,
                }
        except Exception as e:
            logger.error("[DatabaseManager] Error fetching dashboard analytics: %s", e)
            return {
                "top_commands": [],
                "platform_cmds": {},
                "platform_redemptions": {},
                "total_redemptions": 0,
                "platform_spam": {},
                "total_spam": 0,
                "active_commands": 0,
                "active_timers": 0,
                "total_rewards": 0,
                "total_command_usages": 0,
            }

    def save_channel_profile(self, platform: str, profile_data: dict) -> None:
        if not platform or not profile_data:
            return
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO channel_profiles (
                        platform, username, bio, avatar_url, followers,
                        room_id, category, affiliate_status, vods_enabled,
                        created_at, raw_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(platform) DO UPDATE SET
                        username=excluded.username,
                        bio=excluded.bio,
                        avatar_url=excluded.avatar_url,
                        followers=excluded.followers,
                        room_id=excluded.room_id,
                        category=excluded.category,
                        affiliate_status=excluded.affiliate_status,
                        vods_enabled=excluded.vods_enabled,
                        created_at=excluded.created_at,
                        raw_json=excluded.raw_json,
                        updated_at=CURRENT_TIMESTAMP
                """, (
                    platform.lower().strip(),
                    profile_data.get("username", ""),
                    profile_data.get("bio", ""),
                    profile_data.get("avatar_url", ""),
                    int(profile_data.get("followers", 0) or 0),
                    str(profile_data.get("room_id") or profile_data.get("broadcaster_id") or ""),
                    profile_data.get("category") or profile_data.get("last_category") or "",
                    str(profile_data.get("broadcaster_type") or ("affiliate" if profile_data.get("is_affiliate") else "")),
                    1 if profile_data.get("vod_enabled") else 0,
                    profile_data.get("created_at", "-"),
                    json.dumps(profile_data)
                ))
                conn.commit()
        except Exception as e:
            logger.error("[DatabaseManager] Error saving channel profile for %s: %s", platform, e)

    def load_channel_profile(self, platform: str) -> dict | None:
        if not platform:
            return None
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT raw_json FROM channel_profiles WHERE platform = ?", (platform.lower().strip(),))
                row = cursor.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
        except Exception as e:
            logger.error("[DatabaseManager] Error loading channel profile for %s: %s", platform, e)
        return None

    def load_all_channel_profiles(self) -> dict[str, dict]:
        results = {}
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT platform, raw_json FROM channel_profiles")
                for plat, raw in cursor.fetchall():
                    if raw:
                        try:
                            results[plat] = json.loads(raw)
                        except Exception:
                            pass
        except Exception as e:
            logger.error("[DatabaseManager] Error loading all channel profiles: %s", e)
        return results

    def delete_channel_profile(self, platform: str) -> None:
        if not platform:
            return
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM channel_profiles WHERE platform = ?", (platform.lower().strip(),))
                conn.commit()
        except Exception as e:
            logger.error("[DatabaseManager] Error deleting channel profile for %s: %s", platform, e)

    def get_primary_identity(self) -> str:
        try:
            profiles = self.load_all_channel_profiles()
            for plat in ("kick", "twitch", "tiktok", "youtube"):
                if plat in profiles and profiles[plat]:
                    uname = profiles[plat].get("username") or profiles[plat].get("login") or ""
                    if uname and uname.strip():
                        return uname.strip().lstrip("@")

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM settings WHERE key IN ('tiktok_target_channel', 'youtube_target_channel')")
                settings_map = {k: v for k, v in cursor.fetchall()}

                tt_target = settings_map.get("tiktok_target_channel", "")
                if tt_target and tt_target.strip():
                    return tt_target.strip().lstrip("@")

                yt_target = settings_map.get("youtube_target_channel", "")
                if yt_target and yt_target.strip():
                    return yt_target.strip()
        except Exception as e:
            logger.error("[DatabaseManager] Error obteniendo identidad primaria: %s", e)
        return ""

    def cleanup(self) -> None:
        try:
            with self.get_connection() as conn:
                conn.execute("PRAGMA optimize")
                conn.commit()
            logger.info("Database PRAGMA optimize executed successfully on shutdown.")
        except Exception as e:
            logger.error("Error optimizing database on shutdown: %s", e)
