# backend\services\rewards\rewards_service.py

import os
import logging
from PySide6.QtCore import QUrl, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

logger = logging.getLogger("minikick.services.rewards")

class MediaTriggerService(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

    def play_file(self, file_path: str, volume: float = 1.0) -> None:
        if not file_path or not os.path.exists(file_path):
            logging.warning("[MediaTrigger] Media file not found or empty: %s", file_path)
            return
            
        self.audio_output.setVolume(volume)
        self.player.setSource(QUrl.fromLocalFile(os.path.abspath(file_path)))
        self.player.play()

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
