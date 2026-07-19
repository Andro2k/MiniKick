# backend\storage\timers_storage.py

import json
from backend.database.manager import DatabaseManager

class SQLiteTimersStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories FROM chat_timers")
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

    def get_timer_by_id(self, timer_id: int) -> dict | None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories 
                FROM chat_timers WHERE id = ?
            """, (timer_id,))
            r = cursor.fetchone()
            if not r:
                return None
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

            return {
                "id": r[0],
                "name": r[1],
                "messages": messages,
                "is_active": bool(r[3]),
                "interval_online": r[4],
                "interval_offline": r[5],
                "chat_lines": r[6],
                "keywords": keywords,
                "categories": categories
            }

    def save_timer(self, name: str, messages: list[str], is_active: bool, interval_online: int, interval_offline: int, chat_lines: int, keywords: list[str], categories: list[str], timer_id: int = None) -> None:
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
