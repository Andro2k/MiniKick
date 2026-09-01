# backend\database\commands_storage.py

import logging
from datetime import datetime
from backend.database.manager import DatabaseManager

logger = logging.getLogger("minikick.database.commands_storage")

class SQLiteCommandsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT trigger, response, is_active, cooldown, aliases, is_regex, permission, apply_kick, apply_twitch, apply_youtube, apply_tiktok FROM chat_commands")
                return [
                    {
                        "trigger": r[0],
                        "response": r[1],
                        "is_active": bool(r[2]),
                        "cooldown": r[3],
                        "aliases": r[4],
                        "is_regex": bool(r[5]),
                        "permission": r[6],
                        "apply_kick": bool(r[7]) if len(r) > 7 and r[7] is not None else True,
                        "apply_twitch": bool(r[8]) if len(r) > 8 and r[8] is not None else True,
                        "apply_youtube": bool(r[9]) if len(r) > 9 and r[9] is not None else True,
                        "apply_tiktok": bool(r[10]) if len(r) > 10 and r[10] is not None else True
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            logger.error("[CommandsStorage] Error loading all commands: %s", e)
            return []

    def get_command_by_trigger(self, trigger: str) -> dict | None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT trigger, response, is_active, cooldown, aliases, is_regex, permission, apply_kick, apply_twitch, apply_youtube, apply_tiktok FROM chat_commands WHERE trigger=?", (trigger,))
                r = cursor.fetchone()
                if not r:
                    return None
                return {
                    "trigger": r[0],
                    "response": r[1],
                    "is_active": bool(r[2]),
                    "cooldown": r[3],
                    "aliases": r[4],
                    "is_regex": bool(r[5]),
                    "permission": r[6],
                    "apply_kick": bool(r[7]) if len(r) > 7 and r[7] is not None else True,
                    "apply_twitch": bool(r[8]) if len(r) > 8 and r[8] is not None else True,
                    "apply_youtube": bool(r[9]) if len(r) > 9 and r[9] is not None else True,
                    "apply_tiktok": bool(r[10]) if len(r) > 10 and r[10] is not None else True
                }
        except Exception as e:
            logger.error("[CommandsStorage] Error fetching command by trigger '%s': %s", trigger, e)
            return None

    def save_command(self, trigger: str, response: str, is_active: bool, cooldown: int, aliases: str, is_regex: bool, permission: str = "everyone", apply_kick: bool = True, apply_twitch: bool = True, apply_youtube: bool = True, apply_tiktok: bool = True) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_commands (trigger, response, is_active, cooldown, aliases, is_regex, permission, apply_kick, apply_twitch, apply_youtube, apply_tiktok) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(trigger) DO UPDATE SET 
                        response=excluded.response, is_active=excluded.is_active, cooldown=excluded.cooldown,
                        aliases=excluded.aliases, is_regex=excluded.is_regex, permission=excluded.permission,
                        apply_kick=excluded.apply_kick, apply_twitch=excluded.apply_twitch, apply_youtube=excluded.apply_youtube,
                        apply_tiktok=excluded.apply_tiktok
                """, (trigger, response, int(is_active), cooldown, aliases, int(is_regex), permission, int(apply_kick), int(apply_twitch), int(apply_youtube), int(apply_tiktok)))
                conn.commit()
            logger.debug("[CommandsStorage] Saved command trigger='%s', active=%s", trigger, is_active)
        except Exception as e:
            logger.error("[CommandsStorage] Error saving command '%s': %s", trigger, e)

    def delete_command(self, trigger: str) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_commands WHERE trigger=?", (trigger,))
                conn.commit()
            logger.debug("[CommandsStorage] Deleted command trigger='%s'", trigger)
        except Exception as e:
            logger.error("[CommandsStorage] Error deleting command '%s': %s", trigger, e)

    def search_commands(self, query: str) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                pattern = f"%{query.strip().lower()}%"
                cursor.execute("""
                    SELECT trigger, response, is_active, cooldown, aliases, is_regex, permission, apply_kick, apply_twitch, apply_youtube, apply_tiktok 
                    FROM chat_commands 
                    WHERE LOWER(trigger) LIKE ? OR LOWER(response) LIKE ? OR LOWER(aliases) LIKE ?
                """, (pattern, pattern, pattern))
                return [
                    {
                        "trigger": r[0],
                        "response": r[1],
                        "is_active": bool(r[2]),
                        "cooldown": r[3],
                        "aliases": r[4],
                        "is_regex": bool(r[5]),
                        "permission": r[6],
                        "apply_kick": bool(r[7]) if len(r) > 7 and r[7] is not None else True,
                        "apply_twitch": bool(r[8]) if len(r) > 8 and r[8] is not None else True,
                        "apply_youtube": bool(r[9]) if len(r) > 9 and r[9] is not None else True,
                        "apply_tiktok": bool(r[10]) if len(r) > 10 and r[10] is not None else True
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            logger.error("[CommandsStorage] Error searching commands with query '%s': %s", query, e)
            return []

    def log_command_execution(self, trigger: str, username: str, platform: str = "kick") -> None:
        local_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO command_execution_logs (command_trigger, username, platform, timestamp) VALUES (?, ?, ?, ?)", (trigger, username, platform or "kick", local_now))
                conn.commit()
        except Exception as e:
            logger.error("[CommandsStorage] Error logging command execution '%s' by '%s': %s", trigger, username, e)

    def get_command_analytics(self, platform: str | None = None) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                if platform:
                    cursor.execute("""
                        SELECT 
                            c.trigger,
                            c.response,
                            c.is_active,
                            COUNT(l.id) AS usage_count,
                            MAX(l.timestamp) AS last_used
                        FROM chat_commands c
                        LEFT JOIN command_execution_logs l ON c.trigger = l.command_trigger AND l.platform = ?
                        GROUP BY c.trigger
                        ORDER BY usage_count DESC
                    """, (platform,))
                else:
                    cursor.execute("SELECT trigger, response, is_active, usage_count, last_used FROM command_analytics ORDER BY usage_count DESC")
                return [{"trigger": r[0], "response": r[1], "is_active": bool(r[2]), "usage_count": r[3], "last_used": r[4]} for r in cursor.fetchall()]
        except Exception as e:
            logger.error("[CommandsStorage] Error fetching command analytics (platform=%s): %s", platform, e)
            return []

    def get_active_features_summary(self) -> dict:
        try:
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
        except Exception as e:
            logger.error("[CommandsStorage] Error fetching active features summary: %s", e)
        return {
            "total_commands": 0,
            "active_commands": 0,
            "total_timers": 0,
            "active_timers": 0,
            "total_command_usages": 0
        }
