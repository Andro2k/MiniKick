# backend\services\backup_service.py

import json
import logging
from backend.interfaces.settings_interfaces import SettingsStorage

class BackupService:
    def __init__(self, settings_storage: SettingsStorage, alerts_storage):
        self.settings_storage = settings_storage
        self.alerts_storage = alerts_storage
        self.logger = logging.getLogger(__name__)

    def export_to_json(self, filepath: str) -> bool:
        try:
            data = {
                "settings": self.settings_storage.get_all(),
                "alerts": self.alerts_storage.load_all()
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Configuración exportada exitosamente a {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error al exportar configuración: {e}")
            return False

    def import_from_json(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "settings" in data and isinstance(data["settings"], dict):
                self.settings_storage.save_all(data["settings"])
            
            if "alerts" in data and isinstance(data["alerts"], dict):
                self.alerts_storage.save_all(data["alerts"])
                
            self.logger.info(f"Configuración importada exitosamente desde {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error al importar configuración: {e}")
            return False