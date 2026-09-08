# backend\services\system\backup_service.py

import base64
import json
import logging
import os
from datetime import datetime, timezone
from backend.interfaces import SettingsStorage
from backend.config import APP_VERSION

logger = logging.getLogger("minikick.services.system.backup")

class BackupService:
    SENSITIVE_KEYS = {"overlay_session_token"}

    def __init__(self, settings_storage: SettingsStorage, rewards_storage, commands_storage,
                 spam_storage, timers_storage=None, schedule_storage=None,
                 alert_storage=None, widgets_storage=None):
        self.settings_storage = settings_storage
        self.rewards_storage = rewards_storage
        self.commands_storage = commands_storage
        self.spam_storage = spam_storage
        self.timers_storage = timers_storage
        self.schedule_storage = schedule_storage
        self.alert_storage = alert_storage
        self.widgets_storage = widgets_storage
        self.logger = logger

    @staticmethod
    def _sanitize_for_json(obj):
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("ascii")
        elif isinstance(obj, dict):
            return {k: BackupService._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [BackupService._sanitize_for_json(item) for item in obj]
        return obj

    def export_to_json(self, filepath: str) -> bool:
        if not filepath.lower().endswith('.json'):
            filepath += '.json'
        try:
            raw_settings = dict(self.settings_storage.get_all())
            for key in self.SENSITIVE_KEYS:
                raw_settings.pop(key, None)

            raw_rewards = self.rewards_storage.load_all() if self.rewards_storage else {}
            raw_commands = self.commands_storage.load_all() if self.commands_storage else []
            raw_spam = self.spam_storage.load_all() if self.spam_storage else {}

            data = {
                "_metadata": {
                    "app": "MiniKick",
                    "version": APP_VERSION,
                    "exported_at": datetime.now(timezone.utc).isoformat()
                },
                "settings": raw_settings,
                "rewards": raw_rewards,
                "commands": raw_commands,
                "spam_filters": raw_spam
            }
            if self.timers_storage:
                data["timers"] = self.timers_storage.load_all()
            if self.schedule_storage:
                data["schedules"] = self.schedule_storage.load_all()
            if self.widgets_storage:
                data["widgets"] = self.widgets_storage.load_all_widgets()
            if self.alert_storage:
                raw_alerts = self.alert_storage.load_all()
                data["alerts"] = [cfg.to_dict() for cfg in raw_alerts.values()]

            sanitized_data = self._sanitize_for_json(data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(sanitized_data, f, indent=4, ensure_ascii=False)
            self.logger.info("Successfully exported configuration to %s (sensitive keys excluded)", filepath)
            return True
        except Exception as e:
            self.logger.error("Error exporting configuration: %s", e)
            return False

    def import_from_json(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                self.logger.error("Invalid backup file format: Root is not a JSON object.")
                return False

            metadata = data.get("_metadata")
            if metadata and isinstance(metadata, dict):
                self.logger.info("Importing MiniKick backup v%s exported at %s", metadata.get("version", "unknown"), metadata.get("exported_at", "unknown"))

            if "settings" in data and isinstance(data["settings"], dict):
                imported_settings = dict(data["settings"])
                current_token = self.settings_storage.load_string("overlay_session_token", "")
                if current_token and "overlay_session_token" not in imported_settings:
                    imported_settings["overlay_session_token"] = current_token
                self.settings_storage.save_all(imported_settings)

            if "rewards" in data and isinstance(data["rewards"], dict) and self.rewards_storage:
                cleaned_rewards = {}
                for r_name, r_cfg in data["rewards"].items():
                    if not isinstance(r_cfg, dict):
                        continue
                    cfg_copy = dict(r_cfg)
                    tb = cfg_copy.get("thumbnail_bytes")
                    if isinstance(tb, str) and tb.strip():
                        try:
                            cfg_copy["thumbnail_bytes"] = base64.b64decode(tb)
                        except Exception:
                            cfg_copy["thumbnail_bytes"] = None
                    elif not isinstance(tb, bytes):
                        cfg_copy["thumbnail_bytes"] = None

                    media_path = cfg_copy.get("filepath", "")
                    if media_path and not os.path.exists(media_path):
                        self.logger.warning("[BackupService] Reward '%s' media path not found: %s", r_name, media_path)
                    cleaned_rewards[r_name] = cfg_copy
                self.rewards_storage.save_all(cleaned_rewards)

            if "commands" in data and isinstance(data["commands"], list) and self.commands_storage:
                for cmd in data["commands"]:
                    if not isinstance(cmd, dict):
                        continue
                    trigger = cmd.get("trigger")
                    response = cmd.get("response")
                    if not trigger or response is None:
                        continue
                    try:
                        self.commands_storage.save_command(
                            trigger=trigger,
                            response=response,
                            is_active=bool(cmd.get("is_active", True)),
                            cooldown=int(cmd.get("cooldown", 5)),
                            aliases=str(cmd.get("aliases", "")),
                            is_regex=bool(cmd.get("is_regex", False)),
                            permission=str(cmd.get("permission", "everyone")),
                            apply_kick=bool(cmd.get("apply_kick", True)),
                            apply_twitch=bool(cmd.get("apply_twitch", True)),
                            apply_youtube=bool(cmd.get("apply_youtube", True)),
                            apply_tiktok=bool(cmd.get("apply_tiktok", True))
                        )
                    except TypeError:
                        self.commands_storage.save_command(
                            trigger=trigger,
                            response=response,
                            is_active=bool(cmd.get("is_active", True)),
                            cooldown=int(cmd.get("cooldown", 5)),
                            aliases=str(cmd.get("aliases", "")),
                            is_regex=bool(cmd.get("is_regex", False)),
                            permission=str(cmd.get("permission", "everyone"))
                        )

            if "spam_filters" in data and isinstance(data["spam_filters"], dict) and self.spam_storage:
                for f_id, config in data["spam_filters"].items():
                    if isinstance(config, dict):
                        self.spam_storage.save_filter(f_id, config)

            if "timers" in data and isinstance(data["timers"], list) and self.timers_storage:
                for timer in data["timers"]:
                    if not isinstance(timer, dict):
                        continue
                    t_name = timer.get("name")
                    t_msgs = timer.get("messages")
                    if not t_name or not t_msgs:
                        continue
                    try:
                        self.timers_storage.save_timer(
                            name=t_name,
                            messages=t_msgs,
                            is_active=bool(timer.get("is_active", True)),
                            interval_online=timer.get("interval_online"),
                            interval_offline=timer.get("interval_offline"),
                            chat_lines=int(timer.get("chat_lines", 0)),
                            keywords=list(timer.get("keywords", [])),
                            categories=list(timer.get("categories", [])),
                            apply_kick=bool(timer.get("apply_kick", True)),
                            apply_twitch=bool(timer.get("apply_twitch", True))
                        )
                    except TypeError:
                        self.timers_storage.save_timer(
                            name=t_name,
                            messages=t_msgs,
                            is_active=bool(timer.get("is_active", True)),
                            interval_online=timer.get("interval_online"),
                            interval_offline=timer.get("interval_offline"),
                            chat_lines=int(timer.get("chat_lines", 0)),
                            keywords=list(timer.get("keywords", [])),
                            categories=list(timer.get("categories", []))
                        )

            if "schedules" in data and isinstance(data["schedules"], list) and self.schedule_storage:
                for item in data["schedules"]:
                    if isinstance(item, dict) and "name" in item:
                        self.schedule_storage.save(
                            name=item.get("name", ""),
                            date_str=item.get("date_str", ""),
                            time_str=item.get("time_str", ""),
                            target_platform=item.get("target_platform", "all"),
                            title=item.get("title", ""),
                            kick_category_id=item.get("kick_category_id"),
                            kick_category_name=item.get("kick_category_name", ""),
                            twitch_category_id=item.get("twitch_category_id"),
                            twitch_category_name=item.get("twitch_category_name", ""),
                            is_active=bool(item.get("is_active", True))
                        )

            if "widgets" in data and self.widgets_storage:
                widgets_dict = data["widgets"]
                if isinstance(widgets_dict, dict):
                    for w_id, w_data in widgets_dict.items():
                        if isinstance(w_data, dict):
                            self.widgets_storage.save_widget(
                                widget_id=str(w_data.get("widget_id", w_id)),
                                is_active=bool(w_data.get("is_active", True)),
                                command=str(w_data.get("command", "")),
                                cooldown=int(w_data.get("cooldown", 3)),
                                permission=str(w_data.get("permission", "everyone")),
                                config=dict(w_data.get("config", {}))
                            )
                elif isinstance(widgets_dict, list):
                    for w_data in widgets_dict:
                        if isinstance(w_data, dict) and "widget_id" in w_data:
                            self.widgets_storage.save_widget(
                                widget_id=str(w_data["widget_id"]),
                                is_active=bool(w_data.get("is_active", True)),
                                command=str(w_data.get("command", "")),
                                cooldown=int(w_data.get("cooldown", 3)),
                                permission=str(w_data.get("permission", "everyone")),
                                config=dict(w_data.get("config", {}))
                            )

            if "alerts" in data and self.alert_storage:
                from backend.models import AlertConfig
                alerts_data = data["alerts"]
                configs_to_save = []
                if isinstance(alerts_data, list):
                    for item in alerts_data:
                        if isinstance(item, dict):
                            configs_to_save.append(AlertConfig.from_dict(item))
                elif isinstance(alerts_data, dict):
                    for item in alerts_data.values():
                        if isinstance(item, dict):
                            configs_to_save.append(AlertConfig.from_dict(item))
                if configs_to_save:
                    self.alert_storage.save_all(configs_to_save)

            self.logger.info("Successfully imported configuration from %s", filepath)
            return True
        except Exception as e:
            self.logger.error("Error importing configuration: %s", e)
            return False
