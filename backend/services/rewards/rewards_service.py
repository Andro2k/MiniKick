# backend\services\rewards\rewards_service.py
"""Servicio de recompensas del canal."""

import os
import logging
from .thumbnail_service import generate_media_thumbnail, AUDIO_EXTENSIONS
from backend.utils.db_background_utils import submit_db_write

logger = logging.getLogger("minikick.services.rewards")

class RewardsService:
    def __init__(self, rewards_storage, overlay_server):
        self.storage = rewards_storage
        self.overlay = overlay_server
        self._thumb_attempted: set[str] = set()

    @staticmethod
    def _is_thumbnail_candidate(filepath: str) -> bool:
        return bool(filepath) and os.path.splitext(filepath)[1].lower() not in AUDIO_EXTENSIONS

    def _fill_missing_thumbnail(self, config: dict, force: bool = False) -> bool:
        """Genera la miniatura si falta (None/vacía) y no se intentó ya en esta sesión."""
        filepath = config.get("filepath", "")
        if not self._is_thumbnail_candidate(filepath):
            return False
        if not force and (config.get("thumbnail_bytes") or filepath in self._thumb_attempted):
            return False
        self._thumb_attempted.add(filepath)
        thumb = generate_media_thumbnail(filepath)
        if not thumb:
            return False
        config["thumbnail_bytes"] = thumb
        return True

    def get_mappings(self) -> dict:
        mappings = self.storage.load_all()
        updated = False
        for config in mappings.values():
            if isinstance(config, dict) and self._fill_missing_thumbnail(config):
                updated = True
        if updated:
            self.storage.save_all(mappings)
        return mappings

    def reload_thumbnails(self) -> int:
        """Regenera todas las miniaturas desde los archivos actuales. Devuelve cuántas se generaron."""
        self._thumb_attempted.clear()
        mappings = self.storage.load_all()
        regenerated = sum(
            1 for config in mappings.values()
            if isinstance(config, dict) and self._fill_missing_thumbnail(config, force=True)
        )
        if regenerated:
            self.storage.save_all(mappings)
        logger.info("[RewardsService] Thumbnails regenerated: %d/%d", regenerated, len(mappings))
        return regenerated

    def save_mappings(self, mappings: dict):
        for config in mappings.values():
            if isinstance(config, dict):
                self._fill_missing_thumbnail(config)
        self.storage.save_all(mappings)
        logger.debug("[RewardsService] Saved %d reward mappings to storage.", len(mappings))

    def get_reward_config(self, reward_name: str, platform: str = "kick") -> dict | None:
        mappings = self.get_mappings()
        key = f"{platform.lower()}:{reward_name}"
        if key in mappings:
            return mappings[key]
        if reward_name in mappings:
            conf = mappings[reward_name]
            if isinstance(conf, dict) and conf.get("platform", "kick").lower() == platform.lower():
                return conf
        return None

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
                submit_db_write(self.storage.db_manager.log_reward_redemption, reward_name, username, platform=platform)
            except Exception as e:
                logger.error("[RewardsService] Error logging redemption for '%s': %s", reward_name, e)
