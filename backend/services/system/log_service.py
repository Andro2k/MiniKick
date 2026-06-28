# backend\services\system\log_service.py

import os

class LogService:
    def __init__(self):
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

        if not is_grouped:
            self._live_history.append((level, time_str, message))
            if len(self._live_history) > self.max_logs:
                self._live_history.pop(0)
        return is_grouped

    def clear_history(self):
        self._live_history.clear()

    def get_history(self) -> list[tuple[str, str, str]]:
        return self._live_history