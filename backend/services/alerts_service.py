# backend/services/alerts_service.py

class AlertsService:
    def __init__(self, alerts_storage, overlay_server):
        self.storage = alerts_storage
        self.overlay = overlay_server

    def get_mappings(self) -> dict:
        """Carga el diccionario completo desde SQLite."""
        return self.storage.load_all()

    def save_mappings(self, mappings: dict):
        """Persiste el diccionario completo en SQLite."""
        self.storage.save_all(mappings)

    def trigger_preview(self, reward_name: str, config: dict):
        """Envía la orden de reproducción al servidor web del overlay."""
        self.overlay.trigger_alert(reward_name, config)