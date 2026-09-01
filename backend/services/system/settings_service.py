# backend\services\system\settings_service.py

import logging

logger = logging.getLogger("minikick.services.settings")

class SettingsService:
    def __init__(self, settings_storage, backup_service):
        self.storage = settings_storage
        self.backup = backup_service
        self.SETTING_MINIMIZE_TRAY = "minimize_to_tray"
        self.SETTING_LANGUAGE = "app_language"
        self.SETTING_FONT_SIZE = "app_font_size"

    def is_minimize_tray_enabled(self) -> bool:
        return self.storage.load_bool(self.SETTING_MINIMIZE_TRAY, False)

    def set_minimize_tray_enabled(self, enabled: bool):
        self.storage.save_bool(self.SETTING_MINIMIZE_TRAY, enabled)
        logger.debug("[SettingsService] Minimize to tray set to: %s", enabled)

    def export_settings(self, filepath: str) -> bool:
        logger.info("[SettingsService] Exporting settings backup to: %s", filepath)
        return self.backup.export_to_json(filepath)

    def import_settings(self, filepath: str) -> bool:
        logger.info("[SettingsService] Importing settings backup from: %s", filepath)
        return self.backup.import_from_json(filepath)
    
    def get_language(self) -> str:
        return self.storage.load_string(self.SETTING_LANGUAGE, "es")

    def set_language(self, lang_code: str):
        self.storage.save_string(self.SETTING_LANGUAGE, lang_code)
        logger.info("[SettingsService] Language changed to: %s", lang_code)

    def get_font_size(self) -> int:
        val = self.storage.load_string(self.SETTING_FONT_SIZE, "13")
        try:
            size = int(val)
            return size if size >= 8 else 13
        except ValueError:
            return 13

    def set_font_size(self, size: int):
        self.storage.save_string(self.SETTING_FONT_SIZE, str(size))
        logger.debug("[SettingsService] Font size updated to: %d", size)

    def get_music_audio_device(self) -> str:
        return self.storage.load_string("youtube_audio_device", "default")

    def set_music_audio_device(self, device_id: str):
        self.storage.save_string("youtube_audio_device", device_id)
        logger.debug("[SettingsService] Music audio output device set to: %s", device_id)

    def get_tts_audio_device(self) -> str:
        return self.storage.load_string("tts_audio_device", "default")

    def set_tts_audio_device(self, device_id: str):
        self.storage.save_string("tts_audio_device", device_id)
        logger.debug("[SettingsService] TTS audio output device set to: %s", device_id)
