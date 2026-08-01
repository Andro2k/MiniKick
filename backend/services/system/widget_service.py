# backend\services\system\widget_service.py

import logging
from backend.database.widgets_storage import SQLiteWidgetsStorage

logger = logging.getLogger("minikick.services.widgets")

class WidgetService:
    DEFAULT_WIDGETS = {
        "shoutout": {
            "is_active": True,
            "command": "!so",
            "cooldown": 3,
            "permission": "moderator",
            "config": {
                "template": "Vayan a apoyar y seguir a @{target} en https://kick.com/{target} !"
            }
        },
        "death": {
            "is_active": True,
            "command": "!muertes",
            "cooldown": 3,
            "permission": "everyone",
            "config": {
                "count": 0
            }
        },
        "score": {
            "is_active": True,
            "command": "!score",
            "cooldown": 3,
            "permission": "everyone",
            "config": {
                "wins": 0,
                "losses": 0
            }
        }
    }

    def __init__(self, widgets_storage: SQLiteWidgetsStorage):
        self.storage = widgets_storage
        self._ensure_defaults()

    def _ensure_defaults(self):
        loaded = self.storage.load_all_widgets()
        for w_id, default_data in self.DEFAULT_WIDGETS.items():
            if w_id not in loaded:
                self.storage.save_widget(
                    widget_id=w_id,
                    is_active=default_data["is_active"],
                    command=default_data["command"],
                    cooldown=default_data["cooldown"],
                    permission=default_data["permission"],
                    config=default_data["config"]
                )

    def get_all_widgets(self) -> dict[str, dict]:
        widgets = self.storage.load_all_widgets()
        for w_id, default_data in self.DEFAULT_WIDGETS.items():
            if w_id not in widgets:
                widgets[w_id] = {
                    "widget_id": w_id,
                    "is_active": default_data["is_active"],
                    "command": default_data["command"],
                    "cooldown": default_data["cooldown"],
                    "permission": default_data["permission"],
                    "config": dict(default_data["config"])
                }
        return widgets

    def get_widget(self, widget_id: str) -> dict:
        w = self.storage.get_widget(widget_id)
        if not w and widget_id in self.DEFAULT_WIDGETS:
            default_data = self.DEFAULT_WIDGETS[widget_id]
            return {
                "widget_id": widget_id,
                "is_active": default_data["is_active"],
                "command": default_data["command"],
                "cooldown": default_data["cooldown"],
                "permission": default_data["permission"],
                "config": dict(default_data["config"])
            }
        return w or {}

    def save_widget(self, widget_id: str, is_active: bool, command: str, cooldown: int, permission: str, config: dict):
        self.storage.save_widget(widget_id, is_active, command, cooldown, permission, config)

    def format_shoutout(self, target_user: str) -> str:
        w = self.get_widget("shoutout")
        template = w.get("config", {}).get("template", self.DEFAULT_WIDGETS["shoutout"]["config"]["template"])
        clean_target = target_user.lstrip("@").strip()
        return template.replace("{target}", clean_target).replace("{user}", clean_target)

    def fetch_streamer_avatar(self, target_user: str) -> str:
        clean_target = target_user.lstrip("@").strip().lower()
        if not clean_target:
            return ""
        try:
            import requests
            url = f"https://kick.com/api/v1/channels/{clean_target}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("user", {}).get("profile_pic", "")
        except Exception as e:
            logger.warning("[WidgetService] Could not fetch avatar for %s: %s", clean_target, e)
        return ""

    def get_death_count(self) -> int:
        w = self.get_widget("death")
        return int(w.get("config", {}).get("count", 0))

    def update_death_count(self, delta: int = 0, set_val: int | None = None) -> int:
        w = self.get_widget("death")
        cfg = w.get("config", {})
        current = int(cfg.get("count", 0))
        new_val = set_val if set_val is not None else max(0, current + delta)
        cfg["count"] = new_val
        self.save_widget("death", w.get("is_active", True), w.get("command", "!muertes"), w.get("cooldown", 3), w.get("permission", "everyone"), cfg)
        return new_val

    def get_score(self) -> tuple[int, int]:
        w = self.get_widget("score")
        cfg = w.get("config", {})
        return int(cfg.get("wins", 0)), int(cfg.get("losses", 0))

    def update_score(self, delta_wins: int = 0, delta_losses: int = 0, reset: bool = False, set_wins: int | None = None, set_losses: int | None = None) -> tuple[int, int]:
        w = self.get_widget("score")
        cfg = w.get("config", {})
        if reset:
            wins, losses = 0, 0
        else:
            wins = set_wins if set_wins is not None else max(0, int(cfg.get("wins", 0)) + delta_wins)
            losses = set_losses if set_losses is not None else max(0, int(cfg.get("losses", 0)) + delta_losses)
        cfg["wins"] = wins
        cfg["losses"] = losses
        self.save_widget("score", w.get("is_active", True), w.get("command", "!score"), w.get("cooldown", 3), w.get("permission", "everyone"), cfg)
        return wins, losses
