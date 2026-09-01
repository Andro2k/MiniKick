# backend\services\rewards\rewards_service.py

import os
import logging
from backend.services.rewards.thumbnail_service import generate_media_thumbnail

logger = logging.getLogger("minikick.services.rewards")

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
        logger.debug("[RewardsService] Saved %d reward mappings to storage.", len(mappings))

    def is_file_valid(self, config: dict | str) -> bool:
        if not config:
            return False
        filepath = config.get("filepath", "") if isinstance(config, dict) else (config if isinstance(config, str) else "")
        valid = bool(filepath) and os.path.exists(filepath) and os.path.isfile(filepath)
        if not valid and filepath:
            logger.warning("[RewardsService] Media file path does not exist: '%s'", filepath)
        return valid

    def trigger_preview(self, reward_name: str, config: dict) -> bool:
        if not self.is_file_valid(config):
            logger.warning("[RewardsService] Cannot trigger preview for '%s': invalid media file.", reward_name)
            return False
        self.overlay.trigger_rewards(reward_name, config)
        logger.debug("[RewardsService] Triggered preview for reward: '%s'", reward_name)
        return True

    def log_redemption(self, reward_name: str, username: str, platform: str = "kick"):
        if hasattr(self.storage, "db_manager") and self.storage.db_manager:
            try:
                self.storage.db_manager.log_reward_redemption(reward_name, username, platform=platform)
            except Exception as e:
                logger.error("[RewardsService] Error logging redemption for '%s': %s", reward_name, e)
