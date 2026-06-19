# backend/services/alerts_service.py

class AlertsService:
    def __init__(self, alerts_storage, overlay_server):
        self.storage = alerts_storage
        self.overlay = overlay_server

    def get_mappings(self) -> dict:
        return self.storage.load_all()

    def save_mappings(self, mappings: dict):
        self.storage.save_all(mappings)

    def trigger_preview(self, reward_name: str, config: dict):
        self.overlay.trigger_alert(reward_name, config)