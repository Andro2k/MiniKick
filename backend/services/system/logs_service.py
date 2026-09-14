# backend\services\system\log_service.py

import os
import re
import logging
from collections import deque
from backend.database import SQLiteSystemLogStorage

logger = logging.getLogger("minikick.services.logs")

_LOG_FILE_LINE_RE = re.compile(r"^\[(.*?)\] \[(.*?)\] (.*)")

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
                    try:
                        self.storage.update_last_log(message, self._last_log_id)
                    except Exception as e:
                        logger.debug("[LogService] Error updating last log: %s", e)

        if not is_grouped:
            self._live_history.append((level, time_str, message))
            if self.storage:
                try:
                    self._last_log_id = self.storage.append_log(level, time_str, message)
                except Exception as e:
                    logger.debug("[LogService] Error appending log: %s", e)

        return is_grouped

    def clear_history(self):
        self._live_history.clear()
        self._last_log_id = None
        if self.storage:
            try:
                self.storage.clear_logs()
            except Exception as e:
                logger.error("[LogService] Error clearing log storage: %s", e)

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

    def get_crash_log_path(self) -> str:
        return os.path.join(self.log_dir, "minikick_crash.log")

    def load_crash_history(self) -> list[tuple[str, str, str]]:
        crash_path = self.get_crash_log_path()
        if not os.path.exists(crash_path):
            return []
        return self.parse_log_file(crash_path, fallback_level="CRASH")

    def parse_log_file(self, file_path: str, fallback_level: str) -> list[tuple[str, str, str]]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            parsed_history = []
            current_entry = None
            for line in content.strip().split("\n"):
                if not line.strip():
                    continue
                match = _LOG_FILE_LINE_RE.match(line)
                if match:
                    if current_entry:
                        parsed_history.append(current_entry)
                    current_entry = (match.group(2), match.group(1), match.group(3))
                else:
                    if current_entry:
                        current_entry = (current_entry[0], current_entry[1], f"{current_entry[2]}\n{line}")
                    else:
                        current_entry = (fallback_level, "-", line)
            if current_entry:
                parsed_history.append(current_entry)
            return parsed_history
        except Exception as e:
            logger.error("[LogService] Error parsing log file '%s': %s", file_path, e)
            return []
