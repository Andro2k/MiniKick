# backend\storage\commands_storage.py

from datetime import datetime
from backend.storage.manager import DatabaseManager

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
