# backend\services\chat\chat_service.py

class ChatService:
    def __init__(self, tts_manager, settings_storage):
        self.tts = tts_manager
        self.storage = settings_storage

    def get_settings(self) -> dict:
        provider = self.storage.load_string("tts_provider", "local")
        return {
            "enabled": self.storage.load_bool("tts_enabled", True),
            "read_name": self.storage.load_bool("tts_read_name", True),
            "use_command": self.storage.load_bool("tts_use_command", False),
            "command": self.storage.load_string("tts_command", "!tts"),
            "provider": provider,
            "ignored_users": self.storage.load_string("tts_ignored_users", ""),
            "volume": int(self.storage.load_string("tts_volume", "100")),
            "banned_words": self.storage.load_string("tts_banned_words", ""),
            "role_voice_broadcaster": self.storage.load_string(f"tts_voice_{provider}_broadcaster", ""),
            "role_voice_moderator": self.storage.load_string(f"tts_voice_{provider}_moderator", ""),
            "role_voice_vip": self.storage.load_string(f"tts_voice_{provider}_vip", ""),
            "role_voice_subscriber": self.storage.load_string(f"tts_voice_{provider}_subscriber", "")
        }

    def save_settings(self, settings: dict):
        self.storage.save_bool("tts_enabled", settings.get("enabled", True))
        self.storage.save_bool("tts_read_name", settings.get("read_name", True))
        self.storage.save_bool("tts_use_command", settings.get("use_command", False))
        self.storage.save_string("tts_command", settings.get("command", "!tts"))
        self.storage.save_string("tts_ignored_users", settings.get("ignored_users", ""))
        self.storage.save_string("tts_banned_words", settings.get("banned_words", ""))
        
        provider = settings.get("provider", "local")
        if "role_voice_broadcaster" in settings:
            self.storage.save_string(f"tts_voice_{provider}_broadcaster", settings["role_voice_broadcaster"])
        if "role_voice_moderator" in settings:
            self.storage.save_string(f"tts_voice_{provider}_moderator", settings["role_voice_moderator"])
        if "role_voice_vip" in settings:
            self.storage.save_string(f"tts_voice_{provider}_vip", settings["role_voice_vip"])
        if "role_voice_subscriber" in settings:
            self.storage.save_string(f"tts_voice_{provider}_subscriber", settings["role_voice_subscriber"])
        if "chat_overlay_theme" in settings:
            self.storage.save_string("chat_overlay_theme", settings["chat_overlay_theme"])
        if "chat_overlay_size" in settings:
            self.storage.save_string("chat_overlay_size", settings["chat_overlay_size"])
        if "chat_overlay_fade" in settings:
            self.storage.save_string("chat_overlay_fade", settings["chat_overlay_fade"])
        if "chat_overlay_show_bots" in settings:
            self.storage.save_bool("chat_overlay_show_bots", settings["chat_overlay_show_bots"])
        if "chat_overlay_show_time" in settings:
            self.storage.save_bool("chat_overlay_show_time", settings["chat_overlay_show_time"])

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

    def speak(self, text: str, voice_id: str = None):
        self.tts.say(text, voice_id=voice_id)

    def stop_tts(self):
        self.tts.stop()