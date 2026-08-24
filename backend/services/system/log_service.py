# backend\services\system\log_service.py

import os
import re
from collections import deque
from backend.database.system_log_storage import SQLiteSystemLogStorage

class LogService:
    def __init__(self, log_storage: SQLiteSystemLogStorage = None, db_manager=None):
        if log_storage:
            self.storage = log_storage
        elif db_manager:
            self.storage = SQLiteSystemLogStorage(db_manager)
        else:
            self.storage = None

        self.log_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), ".Minikick", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.max_logs = 1000
        self._live_history: deque[tuple[str, str, str]] = deque(maxlen=self.max_logs)
        self._last_log_id = None

    def _get_date_threshold(self, date_filter: str) -> str:
        if not date_filter:
            return ""
        try:
            days = int(date_filter[:-1])
        except ValueError:
            return ""
        from datetime import datetime, timedelta
        dt = datetime.now() - timedelta(days=days)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def append_record(self, time_str: str, level: str, message: str) -> bool:
        is_grouped = False
        if self._live_history:
            l_level, l_time, l_text = self._live_history[-1]
            if l_level == level and l_time == time_str:
                self._live_history[-1] = (l_level, l_time, f"{l_text}\n{message}")
                is_grouped = True
                
                if self.storage:
                    self.storage.update_last_log(message, self._last_log_id)

        if not is_grouped:
            self._live_history.append((level, time_str, message))
            if self.storage:
                self._last_log_id = self.storage.append_log(level, time_str, message)

        return is_grouped

    def clear_history(self):
        self._live_history.clear()
        self._last_log_id = None
        if self.storage:
            self.storage.clear_logs()

    def get_history(self) -> list[tuple[str, str, str]]:
        if self.storage:
            logs = self.storage.get_all_logs()
            if logs:
                return logs
        return list(self._live_history)

    def get_filtered_history(self, filter_level: str, all_label: str, search_term: str, date_filter: str = "") -> list[tuple[str, str, str]]:
        if self.storage:
            threshold = self._get_date_threshold(date_filter) if date_filter else ""
            logs = self.storage.get_filtered_logs(filter_level, all_label, search_term, threshold)
            if logs:
                return logs
        
        filtered = []
        threshold = self._get_date_threshold(date_filter) if date_filter else ""
        search_lower = search_term.strip().lower()
        for lvl, t_str, txt in self._live_history:
            is_all = (filter_level == all_label)
            if (is_all or lvl == filter_level):
                if not threshold or t_str >= threshold:
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
