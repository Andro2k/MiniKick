# backend\services\rewards\rewards_service.py

from backend.services.rewards.thumbnail_service import generate_media_thumbnail

class RewardsService:
    def __init__(self, rewards_storage, overlay_server):
        self.storage = rewards_storage
        self.overlay = overlay_server

    def get_mappings(self) -> dict:
        mappings = self.storage.load_all()
        updated = False
        for reward, config in mappings.items():
            if isinstance(config, dict) and "thumbnail_bytes" not in config:
                filepath = config.get("filepath", "")
                if filepath:
                    config["thumbnail_bytes"] = generate_media_thumbnail(filepath)
                    updated = True
        if updated:
            self.storage.save_all(mappings)
        return mappings

    def save_mappings(self, mappings: dict):
        for reward, config in mappings.items():
            if isinstance(config, dict):
                filepath = config.get("filepath", "")
                if filepath and "thumbnail_bytes" not in config:
                    config["thumbnail_bytes"] = generate_media_thumbnail(filepath)
        self.storage.save_all(mappings)

    def trigger_preview(self, reward_name: str, config: dict):
        self.overlay.trigger_rewards(reward_name, config)

    def log_redemption(self, reward_name: str, username: str, platform: str = "kick"):
        if hasattr(self.storage, "db_manager") and self.storage.db_manager:
            self.storage.db_manager.log_reward_redemption(reward_name, username, platform=platform)
