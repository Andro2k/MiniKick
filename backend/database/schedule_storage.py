# backend\database\schedule_storage.py

import logging
from backend.database.manager import DatabaseManager
logger = logging.getLogger("minikick.schedule_storage")

class SQLiteScheduleStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, date_str, time_str, target_platform, title,
                       kick_category_id, kick_category_name,
                       twitch_category_id, twitch_category_name,
                       is_active, last_executed_date
                FROM stream_schedules
                ORDER BY id ASC
            """)
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "date_str": r[2] or "",
                    "time_str": r[3] or "",
                    "target_platform": r[4] or "all",
                    "title": r[5] or "",
                    "kick_category_id": r[6],
                    "kick_category_name": r[7] or "",
                    "twitch_category_id": r[8] or "",
                    "twitch_category_name": r[9] or "",
                    "is_active": bool(r[10]),
                    "last_executed_date": r[11] or ""
                }
                for r in rows
            ]

    def get_by_id(self, schedule_id: int) -> dict | None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, date_str, time_str, target_platform, title,
                       kick_category_id, kick_category_name,
                       twitch_category_id, twitch_category_name,
                       is_active, last_executed_date
                FROM stream_schedules
                WHERE id = ?
            """, (schedule_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "id": r[0],
                "name": r[1],
                "date_str": r[2] or "",
                "time_str": r[3] or "",
                "target_platform": r[4] or "all",
                "title": r[5] or "",
                "kick_category_id": r[6],
                "kick_category_name": r[7] or "",
                "twitch_category_id": r[8] or "",
                "twitch_category_name": r[9] or "",
                "is_active": bool(r[10]),
                "last_executed_date": r[11] or ""
            }

    def save(self, name: str, date_str: str, time_str: str, target_platform: str,
             title: str, kick_category_id: int | None, kick_category_name: str,
             twitch_category_id: str | None, twitch_category_name: str,
             is_active: bool = True, schedule_id: int | None = None) -> int:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            if schedule_id is not None and schedule_id > 0:
                cursor.execute("""
                    UPDATE stream_schedules
                    SET name = ?, date_str = ?, time_str = ?, target_platform = ?,
                        title = ?, kick_category_id = ?, kick_category_name = ?,
                        twitch_category_id = ?, twitch_category_name = ?,
                        is_active = ?
                    WHERE id = ?
                """, (
                    name, date_str, time_str, target_platform,
                    title, kick_category_id, kick_category_name,
                    str(twitch_category_id or ""), twitch_category_name,
                    1 if is_active else 0, schedule_id
                ))
                return schedule_id
            else:
                cursor.execute("""
                    INSERT INTO stream_schedules (
                        name, date_str, time_str, target_platform, title,
                        kick_category_id, kick_category_name,
                        twitch_category_id, twitch_category_name,
                        is_active, last_executed_date, days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '')
                """, (
                    name, date_str, time_str, target_platform,
                    title, kick_category_id, kick_category_name,
                    str(twitch_category_id or ""), twitch_category_name,
                    1 if is_active else 0
                ))
                return cursor.lastrowid

    def delete(self, schedule_id: int) -> bool:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stream_schedules WHERE id = ?", (schedule_id,))
            return cursor.rowcount > 0

    def toggle_active(self, schedule_id: int, is_active: bool) -> bool:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE stream_schedules SET is_active = ? WHERE id = ?", (1 if is_active else 0, schedule_id))
            return cursor.rowcount > 0

    def update_last_executed(self, schedule_id: int, date_str: str) -> bool:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE stream_schedules SET last_executed_date = ? WHERE id = ?", (date_str, schedule_id))
            return cursor.rowcount > 0
