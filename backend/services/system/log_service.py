# backend\services\system\log_service.py

import os
import re

class LogService:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.log_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), ".Minikick", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.max_logs = 1000
        self._live_history: list[tuple[str, str, str]] = []

    def append_record(self, time_str: str, level: str, message: str) -> bool:
        is_grouped = False
        if self._live_history:
            l_level, l_time, l_text = self._live_history[-1]
            if l_level == level and l_time == time_str:
                self._live_history[-1] = (l_level, l_time, f"{l_text}\n{message}")
                is_grouped = True
                
                if self.db_manager:
                    try:
                        with self.db_manager.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE system_logs SET message = message || '\n' || ? WHERE id = (SELECT max(id) FROM system_logs)", (message,))
                            conn.commit()
                    except Exception as e:
                        print("Error updating log in DB:", e)

        if not is_grouped:
            self._live_history.append((level, time_str, message))
            if len(self._live_history) > self.max_logs:
                self._live_history.pop(0)
                
            if self.db_manager:
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO system_logs (level, timestamp, message) VALUES (?, ?, ?)", (level, time_str, message))
                        conn.commit()
                except Exception as e:
                    print("Error inserting log into DB:", e)

        return is_grouped

    def clear_history(self):
        self._live_history.clear()
        if self.db_manager:
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM system_logs")
                    conn.commit()
            except Exception as e:
                print("Error clearing logs in DB:", e)

    def get_history(self) -> list[tuple[str, str, str]]:
        if self.db_manager:
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT level, timestamp, message FROM system_logs ORDER BY id ASC")
                    return [(r[0], r[1], r[2]) for r in cursor.fetchall()]
            except Exception as e:
                print("Error fetching logs from DB:", e)
        return self._live_history

    def get_filtered_history(self, filter_level: str, all_label: str, search_term: str) -> list[tuple[str, str, str]]:
        if self.db_manager:
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    query = "SELECT level, timestamp, message FROM system_logs WHERE 1=1"
                    params = []
                    
                    if filter_level != all_label:
                        query += " AND level = ?"
                        params.append(filter_level)
                        
                    if search_term.strip():
                        term = f"%{search_term.strip().lower()}%"
                        query += " AND (LOWER(level) LIKE ? OR LOWER(timestamp) LIKE ? OR LOWER(message) LIKE ?)"
                        params.extend([term, term, term])
                        
                    query += " ORDER BY id DESC LIMIT 300"
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    rows.reverse()
                    return [(r[0], r[1], r[2]) for r in rows]
            except Exception as e:
                print("Error fetching filtered logs from DB:", e)
        
        filtered = []
        for lvl, t_str, txt in self._live_history:
            is_all = (filter_level == all_label)
            if (is_all or lvl == filter_level):
                search_lower = search_term.strip().lower()
                if not search_lower or (search_lower in lvl.lower() or search_lower in t_str.lower() or search_lower in txt.lower()):
                    filtered.append((lvl, t_str, txt))
        return filtered

    def parse_log_file(self, file_path: str, fallback_level: str) -> list[tuple[str, str, str]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_history = []
        for line in content.strip().split("\n"):
            if not line.strip():
                continue
            match = re.match(r"\[(.*?)\] \[(.*?)\] (.*)", line, re.DOTALL)
            if match:
                parsed_history.append((match.group(2), match.group(1), match.group(3)))
            else:
                parsed_history.append((fallback_level, "-", line))
        return parsed_history