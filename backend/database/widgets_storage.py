# backend\database\widgets_storage.py

import json
import logging
from .database_manager import DatabaseManager

logger = logging.getLogger("minikick.database.widgets")

class SQLiteWidgetsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all_widgets(self) -> dict[str, dict]:
        result = {}
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT widget_id, is_active, command, cooldown, permission, config_json 
                    FROM widgets_config
                """)
                for row in cursor.fetchall():
                    widget_id, is_active, command, cooldown, permission, config_raw = row
                    try:
                        config_data = json.loads(config_raw) if config_raw else {}
                    except json.JSONDecodeError:
                        config_data = {}
                    result[widget_id] = {
                        "widget_id": widget_id,
                        "is_active": bool(is_active),
                        "command": command,
                        "cooldown": cooldown,
                        "permission": permission,
                        "config": config_data
                    }
        except Exception as e:
            logger.error("[WidgetsStorage] Error loading all widgets: %s", e)
        return result

    def get_widget(self, widget_id: str) -> dict | None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT widget_id, is_active, command, cooldown, permission, config_json 
                    FROM widgets_config WHERE widget_id = ?
                """, (widget_id,))
                row = cursor.fetchone()
                if row:
                    widget_id, is_active, command, cooldown, permission, config_raw = row
                    try:
                        config_data = json.loads(config_raw) if config_raw else {}
                    except json.JSONDecodeError:
                        config_data = {}
                    return {
                        "widget_id": widget_id,
                        "is_active": bool(is_active),
                        "command": command,
                        "cooldown": cooldown,
                        "permission": permission,
                        "config": config_data
                    }
        except Exception as e:
            logger.error("[WidgetsStorage] Error loading widget '%s': %s", widget_id, e)
        return None

    def save_widget(self, widget_id: str, is_active: bool, command: str, cooldown: int, permission: str, config: dict) -> None:
        try:
            config_raw = json.dumps(config, ensure_ascii=False)
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO widgets_config (widget_id, is_active, command, cooldown, permission, config_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(widget_id) DO UPDATE SET
                        is_active = excluded.is_active,
                        command = excluded.command,
                        cooldown = excluded.cooldown,
                        permission = excluded.permission,
                        config_json = excluded.config_json
                """, (widget_id, 1 if is_active else 0, command.strip(), cooldown, permission, config_raw))
                conn.commit()
        except Exception as e:
            logger.error("[WidgetsStorage] Error saving widget '%s': %s", widget_id, e)

    def load_daily_chatters(self, date_str: str) -> dict[str, dict]:
        result = {}
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, message_count, color, badges_json, platform
                    FROM daily_top_chatters
                    WHERE chatter_date = ?
                    ORDER BY message_count DESC
                """, (date_str,))
                for row in cursor.fetchall():
                    uname, count, color, badges_raw, plat = row
                    try:
                        badges_list = json.loads(badges_raw) if badges_raw else []
                    except Exception:
                        badges_list = []
                    lookup_key = uname.lower().lstrip('@')
                    result[lookup_key] = {
                        "user": uname,
                        "count": int(count),
                        "color": color or "#2ecd70",
                        "badges": badges_list,
                        "platform": plat or "kick"
                    }
        except Exception as e:
            logger.error("[WidgetsStorage] Error loading daily chatters for %s: %s", date_str, e)
        return result

    def save_daily_chatters_batch(self, date_str: str, chatters_map: dict[str, dict]) -> None:
        if not chatters_map:
            return
        import datetime
        now_iso = datetime.datetime.now().isoformat()
        records = []
        for item in chatters_map.values():
            uname = str(item.get("user", "")).lstrip('@').strip()
            if not uname:
                continue
            count = int(item.get("count", 0))
            color = str(item.get("color", "#2ecd70"))
            badges = item.get("badges", [])
            badges_json = json.dumps(badges, ensure_ascii=False) if isinstance(badges, list) else "[]"
            platform = str(item.get("platform", "kick"))
            records.append((date_str, uname, count, color, badges_json, platform, now_iso))

        if not records:
            return

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT INTO daily_top_chatters (
                        chatter_date, username, message_count, color, badges_json, platform, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(chatter_date, username) DO UPDATE SET
                        message_count = excluded.message_count,
                        color = excluded.color,
                        badges_json = excluded.badges_json,
                        platform = excluded.platform,
                        last_seen = excluded.last_seen
                """, records)
                conn.commit()
        except Exception as e:
            logger.error("[WidgetsStorage] Error saving daily chatters batch for %s: %s", date_str, e)

    def clear_daily_chatters(self, date_str: str) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM daily_top_chatters WHERE chatter_date = ?", (date_str,))
                conn.commit()
        except Exception as e:
            logger.error("[WidgetsStorage] Error clearing daily chatters for %s: %s", date_str, e)

    def prune_old_chatters(self, keep_days: int = 7) -> None:
        try:
            import datetime
            cutoff_date = (datetime.date.today() - datetime.timedelta(days=keep_days)).strftime("%Y-%m-%d")
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM daily_top_chatters WHERE chatter_date < ?", (cutoff_date,))
                conn.commit()
        except Exception as e:
            logger.error("[WidgetsStorage] Error pruning old daily chatters: %s", e)
