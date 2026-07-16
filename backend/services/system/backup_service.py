# backend\services\system\backup_service.py

import json
import logging
from backend.interfaces.settings_interfaces import SettingsStorage

class BackupService:
    def __init__(self, settings_storage: SettingsStorage, rewards_storage, commands_storage, spam_storage, timers_storage=None):
        self.settings_storage = settings_storage
        self.rewards_storage = rewards_storage
        self.commands_storage = commands_storage
        self.spam_storage = spam_storage
        self.timers_storage = timers_storage
        self.logger = logging.getLogger(__name__)

    def export_to_json(self, filepath: str) -> bool:
        if not filepath.lower().endswith('.json'):
            filepath += '.json'
        try:
            data = {
                "settings": self.settings_storage.get_all(),
                "rewards": self.rewards_storage.load_all(),
                "commands": self.commands_storage.load_all(),
                "spam_filters": self.spam_storage.load_all()
            }
            if self.timers_storage:
                data["timers"] = self.timers_storage.load_all()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Successfully exported configuration to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False

    def import_from_json(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "settings" in data and isinstance(data["settings"], dict):
                self.settings_storage.save_all(data["settings"])
            
            if "rewards" in data and isinstance(data["rewards"], dict):
                self.rewards_storage.save_all(data["rewards"])
            
            if "commands" in data and isinstance(data["commands"], list):
                for cmd in data["commands"]:
                    self.commands_storage.save_command(
                        trigger=cmd["trigger"],
                        response=cmd["response"],
                        is_active=cmd.get("is_active", True),
                        cooldown=cmd.get("cooldown", 5),
                        aliases=cmd.get("aliases", ""),
                        is_regex=cmd.get("is_regex", False),
                        permission=cmd.get("permission", "everyone")
                    )
            if "spam_filters" in data and isinstance(data["spam_filters"], dict):
                for f_id, config in data["spam_filters"].items():
                    self.spam_storage.save_filter(f_id, config)
                    
            if "timers" in data and isinstance(data["timers"], list) and self.timers_storage:
                for timer in data["timers"]:
                    self.timers_storage.save_timer(
                        name=timer["name"],
                        messages=timer["messages"],
                        is_active=timer.get("is_active", True),
                        interval_online=timer.get("interval_online"),
                        interval_offline=timer.get("interval_offline"),
                        chat_lines=timer.get("chat_lines", 0),
                        keywords=timer.get("keywords", []),
                        categories=timer.get("categories", [])
                    )
                
            self.logger.info(f"Successfully imported configuration from {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
