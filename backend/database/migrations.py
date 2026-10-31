# backend\database\migrations.py

import logging
import sqlite3
from typing import Callable

logger = logging.getLogger("minikick.database.migrations")

def _migration_001_add_missing_columns_and_constraints(conn: sqlite3.Connection) -> None:
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
            ("file_size_mb", "REAL DEFAULT 4.0"),
            ("loudness_db", "REAL DEFAULT NULL")
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
        ],
        "alert_configs": [
            ("layout", "TEXT DEFAULT 'above'"),
            ("style", "TEXT DEFAULT 'compact'"),
            ("text_color", "TEXT DEFAULT '#FFFFFF'"),
            ("highlight_color", "TEXT DEFAULT ''"),
            ("font_family", "TEXT DEFAULT 'Outfit'"),
            ("font_size", "INTEGER DEFAULT 24"),
            ("text_align", "TEXT DEFAULT 'center'"),
            ("animation_in", "TEXT DEFAULT 'fade_in'"),
            ("animation_in_duration", "REAL DEFAULT 1.0"),
            ("animation_out", "TEXT DEFAULT 'fade_out'"),
            ("animation_out_duration", "REAL DEFAULT 1.0"),
            ("bg_color", "TEXT DEFAULT '#121317'"),
            ("bg_opacity", "INTEGER DEFAULT 88"),
            ("border_radius", "INTEGER DEFAULT 20"),
            ("padding_px", "INTEGER DEFAULT 24"),
            ("spacing_px", "INTEGER DEFAULT 16"),
            ("box_shadow", "INTEGER DEFAULT 1"),
            ("font_weight", "TEXT DEFAULT 'bold'"),
            ("text_shadow", "INTEGER DEFAULT 1"),
            ("card_width", "INTEGER DEFAULT 560"),
            ("card_height", "INTEGER DEFAULT 0")
        ]
    }

    try:
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
                        raise

        cursor.execute("PRAGMA table_info(obs_rewards)")
        obs_cols = cursor.fetchall()
        if obs_cols:
            pk_cols = [r[1].lower() for r in obs_cols if r[5] > 0]
            if "platform" not in pk_cols:
                logger.info("Upgrading table obs_rewards: migrating to composite primary key (reward_name, platform)")
                cursor.execute("""
                    CREATE TABLE obs_rewards_new (
                        reward_name TEXT NOT NULL,
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
                        platform TEXT DEFAULT 'kick',
                        PRIMARY KEY (reward_name, platform)
                    )
                """)
                cursor.execute("""
                    INSERT OR IGNORE INTO obs_rewards_new (
                        reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos, thumbnail_bytes,
                        reward_id, cost, description, background_color, is_user_input_required, platform
                    )
                    SELECT reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos, thumbnail_bytes,
                           reward_id, cost, description, background_color, is_user_input_required,
                           COALESCE(platform, 'kick')
                    FROM obs_rewards
                """)
                cursor.execute("DROP TABLE obs_rewards")
                cursor.execute("ALTER TABLE obs_rewards_new RENAME TO obs_rewards")

        cursor.execute("PRAGMA foreign_key_list(reward_redemptions)")
        fk_rows = cursor.fetchall()
        has_obs_fk = any(len(r) > 2 and str(r[2]).lower() == "obs_rewards" for r in fk_rows)
        if has_obs_fk:
            logger.info("Upgrading table reward_redemptions: removing outdated foreign key referencing obs_rewards")
            cursor.execute("""
                CREATE TABLE reward_redemptions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reward_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    platform TEXT DEFAULT 'kick',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO reward_redemptions_new (id, reward_name, username, platform, timestamp)
                SELECT id, reward_name, username, COALESCE(platform, 'kick'), timestamp
                FROM reward_redemptions
            """)
            cursor.execute("DROP TABLE reward_redemptions")
            cursor.execute("ALTER TABLE reward_redemptions_new RENAME TO reward_redemptions")

    except Exception as e:
        logger.error("Error executing database schema upgrade: %s", e)
        raise

def _migration_002_drop_timer_execution_logs(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TRIGGER IF EXISTS prune_timer_logs")
    conn.execute("DROP INDEX IF EXISTS idx_timer_logs_timer")
    conn.execute("DROP INDEX IF EXISTS idx_timer_logs_platform")
    conn.execute("DROP TABLE IF EXISTS timer_execution_logs")

MIGRATIONS: list[tuple[int, Callable[[sqlite3.Connection], None]]] = [
    (1, _migration_001_add_missing_columns_and_constraints),
    (2, _migration_002_drop_timer_execution_logs),
]
