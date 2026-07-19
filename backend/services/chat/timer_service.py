# backend\services\chat\timer_service.py

import time

class TimerService:
    def __init__(self, timers_storage, api_client=None):
        self.storage = timers_storage
        self.api_client = api_client
        self.tracking_state: dict[int, dict] = {}

    def get_all_timers(self) -> list[dict]:
        return self.storage.load_all()

    def search_timers(self, query: str) -> list[dict]:
        return self.storage.search_timers(query)

    def get_active_timers(self) -> list[dict]:
        return [t for t in self.storage.load_all() if t.get("is_active", True)]

    def save_timer(self, name: str, messages: list[str], is_active: bool, interval_online: int, interval_offline: int, chat_lines: int, keywords: list[str], categories: list[str], timer_id: int = None):
        self.storage.save_timer(name, messages, is_active, interval_online, interval_offline, chat_lines, keywords, categories, timer_id)

    def delete_timer(self, timer_id: int):
        self.storage.delete_timer(timer_id)
        self.tracking_state.pop(timer_id, None)

    def increment_chat_lines(self):
        for timer_id in list(self.tracking_state.keys()):
            self.tracking_state[timer_id]["chat_lines"] += 1

    def check_timers(self, stream_status: dict) -> list[str]:
        messages_to_send = []
        now = time.time()

        timers = self.get_active_timers()

        for timer in timers:
            timer_id = timer["id"]
            if timer_id not in self.tracking_state:
                self.tracking_state[timer_id] = {
                    "last_posted_time": now,
                    "chat_lines": 0,
                    "message_index": 0
                }
                continue

            state = self.tracking_state[timer_id]
            min_lines = timer.get("chat_lines", 0)
            if min_lines is not None and min_lines > 0:
                if state["chat_lines"] < min_lines:
                    continue

            is_live = stream_status.get("is_live", False)
            if is_live:
                interval_min = timer.get("interval_online")
                if interval_min is None or interval_min <= 0:
                    continue
            else:
                interval_min = timer.get("interval_offline")
                if interval_min is None or interval_min <= 0:
                    continue

            interval_sec = interval_min * 60
            if now - state["last_posted_time"] < interval_sec:
                continue

            if is_live and timer.get("keywords"):
                title = stream_status.get("title", "").lower()
                matched = any(kw.lower() in title for kw in timer["keywords"])
                if not matched:
                    continue

            if is_live and timer.get("categories"):
                category = stream_status.get("category", "").lower()
                matched = any(cat.lower() == category for cat in timer["categories"])
                if not matched:
                    continue

            msgs = timer.get("messages", [])
            if msgs:
                msg = msgs[state["message_index"] % len(msgs)]
                messages_to_send.append(msg)
                if hasattr(self.storage, "db_manager") and self.storage.db_manager:
                    self.storage.db_manager.log_timer_execution(timer_id, msg)

                state["message_index"] = (state["message_index"] + 1) % len(msgs)
                state["last_posted_time"] = now
                state["chat_lines"] = 0

        return messages_to_send
