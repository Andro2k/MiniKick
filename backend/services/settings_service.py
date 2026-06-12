# backend/services/settings_service.py

class SettingsService:
    def __init__(self, settings_storage, backup_service):
        self.storage = settings_storage
        self.backup = backup_service
        self.SETTING_MINIMIZE_TRAY = "minimize_to_tray"

    def is_minimize_tray_enabled(self) -> bool:
        """Recupera el estado de la ejecución en segundo plano."""
        return self.storage.load_bool(self.SETTING_MINIMIZE_TRAY, False)

    def set_minimize_tray_enabled(self, enabled: bool):
        """Persiste el estado de la ejecución en segundo plano."""
        self.storage.save_bool(self.SETTING_MINIMIZE_TRAY, enabled)

    def export_settings(self, filepath: str) -> bool:
        """Exporta las configuraciones actuales a un archivo JSON."""
        return self.backup.export_to_json(filepath)

    def import_settings(self, filepath: str) -> bool:
        """Importa las configuraciones desde un archivo JSON externo."""
        return self.backup.import_from_json(filepath)