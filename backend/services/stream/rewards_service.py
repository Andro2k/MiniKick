# backend\services\stream\rewards_service.py

class RewardsService:
    def __init__(self, rewards_storage, overlay_server):
        self.storage = rewards_storage
        self.overlay = overlay_server

    def get_mappings(self) -> dict:
        return self.storage.load_all()

    def save_mappings(self, mappings: dict):
        self.storage.save_all(mappings)

    def trigger_preview(self, reward_name: str, config: dict):
        self.overlay.trigger_rewards(reward_name, config)

    def log_redemption(self, reward_name: str, username: str):
        if hasattr(self.storage, "db_manager") and self.storage.db_manager:
            self.storage.db_manager.log_reward_redemption(reward_name, username)