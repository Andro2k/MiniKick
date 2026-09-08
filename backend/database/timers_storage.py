# backend\database\timers_storage.py

import json
import logging
from .manager import DatabaseManager

logger = logging.getLogger("minikick.database.timers_storage")

def _parse_json_list(raw_value: str | None) -> list:
    if not raw_value:
        return []
    try:
        data = json.loads(raw_value)
        return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, TypeError):
        return [k.strip() for k in raw_value.split(",") if k.strip()]

class SQLiteTimersStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories, apply_kick, apply_twitch, apply_youtube FROM chat_timers")
                return [
                    {
                        "id": r[0],
                        "name": r[1],
                        "messages": _parse_json_list(r[2]),
                        "is_active": bool(r[3]),
                        "interval_online": r[4],
                        "interval_offline": r[5],
                        "chat_lines": r[6],
                        "keywords": _parse_json_list(r[7]),
                        "categories": _parse_json_list(r[8]),
                        "apply_kick": bool(r[9]) if len(r) > 9 and r[9] is not None else True,
                        "apply_twitch": bool(r[10]) if len(r) > 10 and r[10] is not None else True,
                        "apply_youtube": bool(r[11]) if len(r) > 11 and r[11] is not None else True
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            logger.error("[TimersStorage] Error loading all timers: %s", e)
            return []

    def get_timer_by_id(self, timer_id: int) -> dict | None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories, apply_kick, apply_twitch, apply_youtube 
                    FROM chat_timers WHERE id = ?
                """, (timer_id,))
                r = cursor.fetchone()
                if not r:
                    return None
                return {
                    "id": r[0],
                    "name": r[1],
                    "messages": _parse_json_list(r[2]),
                    "is_active": bool(r[3]),
                    "interval_online": r[4],
                    "interval_offline": r[5],
                    "chat_lines": r[6],
                    "keywords": _parse_json_list(r[7]),
                    "categories": _parse_json_list(r[8]),
                    "apply_kick": bool(r[9]) if len(r) > 9 and r[9] is not None else True,
                    "apply_twitch": bool(r[10]) if len(r) > 10 and r[10] is not None else True,
                    "apply_youtube": bool(r[11]) if len(r) > 11 and r[11] is not None else True
                }
        except Exception as e:
            logger.error("[TimersStorage] Error fetching timer by id %s: %s", timer_id, e)
            return None

    def save_timer(self, name: str, messages: list[str], is_active: bool, interval_online: int, interval_offline: int, chat_lines: int, keywords: list[str], categories: list[str], apply_kick: bool = True, apply_twitch: bool = True, apply_youtube: bool = True, timer_id: int = None) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                messages_json = json.dumps(messages)
                keywords_json = json.dumps(keywords)
                categories_json = json.dumps(categories)
                ak = int(bool(apply_kick if apply_kick is not None else True))
                at = int(bool(apply_twitch if apply_twitch is not None else True))
                ay = int(bool(apply_youtube if apply_youtube is not None else True))
                if timer_id is not None:
                    cursor.execute("""
                        INSERT INTO chat_timers (id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories, apply_kick, apply_twitch, apply_youtube)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            name=excluded.name, messages=excluded.messages, is_active=excluded.is_active,
                            interval_online=excluded.interval_online, interval_offline=excluded.interval_offline,
                            chat_lines=excluded.chat_lines, keywords=excluded.keywords, categories=excluded.categories,
                            apply_kick=excluded.apply_kick, apply_twitch=excluded.apply_twitch, apply_youtube=excluded.apply_youtube
                    """, (timer_id, name, messages_json, int(is_active), interval_online, interval_offline, chat_lines, keywords_json, categories_json, ak, at, ay))
                else:
                    cursor.execute("""
                        INSERT INTO chat_timers (name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories, apply_kick, apply_twitch, apply_youtube)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(name) DO UPDATE SET
                            messages=excluded.messages, is_active=excluded.is_active,
                            interval_online=excluded.interval_online, interval_offline=excluded.interval_offline,
                            chat_lines=excluded.chat_lines, keywords=excluded.keywords, categories=excluded.categories,
                            apply_kick=excluded.apply_kick, apply_twitch=excluded.apply_twitch, apply_youtube=excluded.apply_youtube
                    """, (name, messages_json, int(is_active), interval_online, interval_offline, chat_lines, keywords_json, categories_json, ak, at, ay))
                conn.commit()
            logger.debug("[TimersStorage] Saved timer name='%s', active=%s, id=%s", name, is_active, timer_id)
        except Exception as e:
            logger.error("[TimersStorage] Error saving timer '%s': %s", name, e)

    def delete_timer(self, timer_id: int) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_timers WHERE id=?", (timer_id,))
                conn.commit()
            logger.debug("[TimersStorage] Deleted timer id=%s", timer_id)
        except Exception as e:
            logger.error("[TimersStorage] Error deleting timer id %s: %s", timer_id, e)

    def search_timers(self, query: str) -> list[dict]:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                pattern = f"%{query.strip().lower()}%"
                cursor.execute("""
                    SELECT id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories, apply_kick, apply_twitch, apply_youtube 
                    FROM chat_timers 
                    WHERE LOWER(name) LIKE ? OR LOWER(messages) LIKE ?
                """, (pattern, pattern))
                return [
                    {
                        "id": r[0],
                        "name": r[1],
                        "messages": _parse_json_list(r[2]),
                        "is_active": bool(r[3]),
                        "interval_online": r[4],
                        "interval_offline": r[5],
                        "chat_lines": r[6],
                        "keywords": _parse_json_list(r[7]),
                        "categories": _parse_json_list(r[8]),
                        "apply_kick": bool(r[9]) if len(r) > 9 and r[9] is not None else True,
                        "apply_twitch": bool(r[10]) if len(r) > 10 and r[10] is not None else True,
                        "apply_youtube": bool(r[11]) if len(r) > 11 and r[11] is not None else True
                    }
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            logger.error("[TimersStorage] Error searching timers with query '%s': %s", query, e)
            return []
