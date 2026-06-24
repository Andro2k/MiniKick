# backend\services\chat\chat_service.py

class ChatService:
    def __init__(self, tts_manager, settings_storage):
        self.tts = tts_manager
        self.storage = settings_storage

    def get_settings(self) -> dict:
        return {
            "enabled": self.storage.load_bool("tts_enabled", True),
            "read_name": self.storage.load_bool("tts_read_name", True),
            "use_command": self.storage.load_bool("tts_use_command", False),
            "command": self.storage.load_string("tts_command", "!tts"),
            "provider": self.storage.load_string("tts_provider", "local"),
            "ignored_users": self.storage.load_string("tts_ignored_users", ""),
            "volume": int(self.storage.load_string("tts_volume", "100"))
        }

    def save_settings(self, settings: dict):
        self.storage.save_bool("tts_enabled", settings.get("enabled", True))
        self.storage.save_bool("tts_read_name", settings.get("read_name", True))
        self.storage.save_bool("tts_use_command", settings.get("use_command", False))
        self.storage.save_string("tts_command", settings.get("command", "!tts"))
        self.storage.save_string("tts_ignored_users", settings.get("ignored_users", ""))

    def set_volume(self, volume: int):
        self.storage.save_string("tts_volume", str(volume))
        self.tts.set_volume(volume / 100.0)

    def set_provider(self, provider: str):
        self.storage.save_string("tts_provider", provider)
        self.tts.set_provider(provider)

    def get_available_voices(self, provider: str) -> list[dict]:
        return self.tts.get_available_voices(provider)

    def get_saved_voice_id(self, provider: str) -> str:
        return self.storage.load_string(f"tts_voice_{provider}", "")

    def set_voice(self, provider: str, voice_id: str):
        self.storage.save_string(f"tts_voice_{provider}", voice_id)
        self.tts.set_voice(voice_id)

    def speak(self, text: str):
        self.tts.say(text)

    def stop_tts(self):
        self.tts.stop()