# backend\services\system\log_service.py

import os
import logging
from collections import deque
from backend.database import SQLiteSystemLogStorage
from backend.core.log_format import log_level_matches, parse_log_line
from .log_writer import BatchedLogWriter

logger = logging.getLogger("minikick.services.logs")

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
        self._writer = BatchedLogWriter(self.storage.append_logs) if self.storage else None

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
        self._live_history.append((level, time_str, message))
        if self._writer:
            self._writer.submit((level, time_str, message))
        return False

    def flush_pending(self) -> None:
        if self._writer:
            self._writer.flush()

    def close(self) -> None:
        if self._writer:
            self._writer.close()

    def clear_history(self):
        self._live_history.clear()
        self.flush_pending()
        if self.storage:
            try:
                self.storage.clear_logs()
            except Exception as e:
                logger.error("[LogService] Error clearing log storage: %s", e)

    def get_history(self) -> list[tuple[str, str, str]]:
        self.flush_pending()
        if self.storage:
            logs = self.storage.get_all_logs()
            if logs:
                return logs
        return list(self._live_history)

    def get_filtered_history(self, filter_level: str, all_label: str, search_term: str, date_filter: str = "") -> list[tuple[str, str, str]]:
        self.flush_pending()
        if self.storage:
            threshold = self._get_date_threshold(date_filter) if date_filter else ""
            logs = self.storage.get_filtered_logs(filter_level, all_label, search_term, threshold)
            if logs:
                return logs
        
        filtered = []
        threshold = self._get_date_threshold(date_filter) if date_filter else ""
        search_lower = search_term.strip().lower()
        for lvl, t_str, txt in self._live_history:
            if log_level_matches(lvl, filter_level, all_label):
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
                parsed_history: list[tuple[str, str, str]] = []
                current_entry = None
                for raw_line in f:
                    line = raw_line.rstrip("\r\n")
                    if not line.strip():
                        continue
                    parsed = parse_log_line(line)
                    if parsed is not None:
                        if current_entry:
                            parsed_history.append(current_entry)
                        current_entry = (
                            parsed.level,
                            parsed.time,
                            parsed.message,
                        )
                    elif current_entry:
                        current_entry = (
                            current_entry[0],
                            current_entry[1],
                            f"{current_entry[2]}\n{line}",
                        )
                    else:
                        current_entry = (fallback_level, "-", line)

                if current_entry:
                    parsed_history.append(current_entry)
                return parsed_history
        except OSError:
            logger.exception("[LogService] Could not read log file '%s'.", file_path)
            return []
        except UnicodeError:
            logger.exception("[LogService] Could not decode log file '%s'.", file_path)
            return []
