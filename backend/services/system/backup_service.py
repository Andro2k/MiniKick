# backend\services\system\backup_service.py

import json
import logging
from backend.interfaces.settings_interfaces import SettingsStorage

class BackupService:
    def __init__(self, settings_storage: SettingsStorage, alerts_storage, commands_storage, spam_storage):
        self.settings_storage = settings_storage
        self.alerts_storage = alerts_storage
        self.commands_storage = commands_storage
        self.spam_storage = spam_storage
        self.logger = logging.getLogger(__name__)

    def export_to_json(self, filepath: str) -> bool:
        try:
            data = {
                "settings": self.settings_storage.get_all(),
                "alerts": self.alerts_storage.load_all(),
                "commands": self.commands_storage.load_all(),
                "spam_filters": self.spam_storage.load_all()
            }
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
            
            if "alerts" in data and isinstance(data["alerts"], dict):
                self.alerts_storage.save_all(data["alerts"])
            
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
                
            self.logger.info(f"Successfully imported configuration from {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False