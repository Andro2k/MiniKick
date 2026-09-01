# backend\services\chat\chat_service.py

import logging

logger = logging.getLogger("minikick.services.chat")

class ChatService:
    def __init__(self, tts_manager, settings_storage):
        self.tts = tts_manager
        self.storage = settings_storage
        self._init_tts_params()

    def _init_tts_params(self):
        try:
            ls = float(self.storage.load_string("piper_length_scale", "1.0"))
            ns = float(self.storage.load_string("piper_noise_scale", "0.667"))
            nws = float(self.storage.load_string("piper_noise_w_scale", "0.8"))
            if hasattr(self.tts, "set_piper_synthesis_params"):
                self.tts.set_piper_synthesis_params(ls, ns, nws)
        except Exception as e:
            logger.debug("[ChatService] Notice initializing TTS params: %s", e)

    def get_settings(self) -> dict:
        provider = self.storage.load_string("tts_provider", "piper")
        try:
            ls = float(self.storage.load_string("piper_length_scale", "1.0"))
            ns = float(self.storage.load_string("piper_noise_scale", "0.667"))
            nws = float(self.storage.load_string("piper_noise_w_scale", "0.8"))
        except Exception:
            ls, ns, nws = 1.0, 0.667, 0.8
        return {
            "enabled": self.storage.load_bool("tts_enabled", True),
            "read_name": self.storage.load_bool("tts_read_name", True),
            "use_command": self.storage.load_bool("tts_use_command", False),
            "command": self.storage.load_string("tts_command", "!tts"),
            "provider": provider,
            "piper_length_scale": ls,
            "piper_noise_scale": ns,
            "piper_noise_w_scale": nws,
            "ignored_users": self.storage.load_string("tts_ignored_users", ""),
            "volume": int(self.storage.load_string("tts_volume", "100")),
            "speed": int(self.storage.load_string("tts_speed", "100")),
            "banned_words": self.storage.load_string("tts_banned_words", ""),
            "role_voice_broadcaster": self.storage.load_string(f"tts_voice_{provider}_broadcaster", ""),
            "role_voice_moderator": self.storage.load_string(f"tts_voice_{provider}_moderator", ""),
            "role_voice_vip": self.storage.load_string(f"tts_voice_{provider}_vip", ""),
            "role_voice_subscriber": self.storage.load_string(f"tts_voice_{provider}_subscriber", ""),
            "role_enabled_everyone": self.storage.load_bool("tts_role_enabled_everyone", True),
            "role_enabled_broadcaster": self.storage.load_bool("tts_role_enabled_broadcaster", True),
            "role_enabled_moderator": self.storage.load_bool("tts_role_enabled_moderator", True),
            "role_enabled_vip": self.storage.load_bool("tts_role_enabled_vip", True),
            "role_enabled_subscriber": self.storage.load_bool("tts_role_enabled_subscriber", True)
        }

    def save_settings(self, settings: dict):
        self.storage.save_bool("tts_enabled", settings.get("enabled", True))
        self.storage.save_bool("tts_read_name", settings.get("read_name", True))
        self.storage.save_bool("tts_use_command", settings.get("use_command", False))
        self.storage.save_string("tts_command", settings.get("command", "!tts"))
        self.storage.save_string("tts_ignored_users", settings.get("ignored_users", ""))
        self.storage.save_string("tts_banned_words", settings.get("banned_words", ""))
        
        provider = settings.get("provider", "piper")
        if "role_voice_broadcaster" in settings:
            self.storage.save_string(f"tts_voice_{provider}_broadcaster", settings["role_voice_broadcaster"])
        if "role_voice_moderator" in settings:
            self.storage.save_string(f"tts_voice_{provider}_moderator", settings["role_voice_moderator"])
        if "role_voice_vip" in settings:
            self.storage.save_string(f"tts_voice_{provider}_vip", settings["role_voice_vip"])
        if "role_voice_subscriber" in settings:
            self.storage.save_string(f"tts_voice_{provider}_subscriber", settings["role_voice_subscriber"])
        if "role_enabled_everyone" in settings:
            self.storage.save_bool("tts_role_enabled_everyone", settings["role_enabled_everyone"])
        if "role_enabled_broadcaster" in settings:
            self.storage.save_bool("tts_role_enabled_broadcaster", settings["role_enabled_broadcaster"])
        if "role_enabled_moderator" in settings:
            self.storage.save_bool("tts_role_enabled_moderator", settings["role_enabled_moderator"])
        if "role_enabled_vip" in settings:
            self.storage.save_bool("tts_role_enabled_vip", settings["role_enabled_vip"])
        if "role_enabled_subscriber" in settings:
            self.storage.save_bool("tts_role_enabled_subscriber", settings["role_enabled_subscriber"])
        if "chat_overlay_theme" in settings:
            self.storage.save_string("chat_overlay_theme", settings["chat_overlay_theme"])
        if "chat_overlay_size" in settings:
            self.storage.save_string("chat_overlay_size", settings["chat_overlay_size"])
        if "chat_overlay_fade" in settings:
            self.storage.save_string("chat_overlay_fade", settings["chat_overlay_fade"])
        if "chat_overlay_show_time" in settings:
            self.storage.save_bool("chat_overlay_show_time", settings["chat_overlay_show_time"])
        if "piper_length_scale" in settings:
            self.storage.save_string("piper_length_scale", str(settings["piper_length_scale"]))
        if "piper_noise_scale" in settings:
            self.storage.save_string("piper_noise_scale", str(settings["piper_noise_scale"]))
        if "piper_noise_w_scale" in settings:
            self.storage.save_string("piper_noise_w_scale", str(settings["piper_noise_w_scale"]))
        if "piper_length_scale" in settings or "piper_noise_scale" in settings or "piper_noise_w_scale" in settings:
            ls = float(settings.get("piper_length_scale", self.storage.load_string("piper_length_scale", "1.0")))
            ns = float(settings.get("piper_noise_scale", self.storage.load_string("piper_noise_scale", "0.667")))
            nws = float(settings.get("piper_noise_w_scale", self.storage.load_string("piper_noise_w_scale", "0.8")))
            if hasattr(self.tts, "set_piper_synthesis_params"):
                self.tts.set_piper_synthesis_params(ls, ns, nws)
        logger.debug("[ChatService] Chat and TTS settings updated.")

    def set_piper_synthesis_params(self, length_scale: float, noise_scale: float, noise_w_scale: float):
        self.storage.save_string("piper_length_scale", f"{length_scale:.2f}")
        self.storage.save_string("piper_noise_scale", f"{noise_scale:.2f}")
        self.storage.save_string("piper_noise_w_scale", f"{noise_w_scale:.2f}")
        if hasattr(self.tts, "set_piper_synthesis_params"):
            self.tts.set_piper_synthesis_params(length_scale, noise_scale, noise_w_scale)

    def set_volume(self, volume: int):
        self.storage.save_string("tts_volume", str(volume))
        self.tts.set_volume(volume / 100.0)

    def set_speed(self, speed: int):
        self.storage.save_string("tts_speed", str(speed))
        self.tts.set_speed(speed / 100.0)

    def set_provider(self, provider: str):
        self.storage.save_string("tts_provider", provider)
        self.tts.set_provider(provider)
        saved_voice = self.get_saved_voice_id(provider)
        if saved_voice:
            self.tts.set_voice(saved_voice)
            if provider == "piper":
                self.tts.warm_up("piper", saved_voice)
        logger.info("[ChatService] TTS provider set to: %s", provider)

    def get_available_voices(self, provider: str) -> list[dict]:
        return self.tts.get_available_voices(provider)

    def get_saved_voice_id(self, provider: str) -> str:
        return self.storage.load_string(f"tts_voice_{provider}", "")

    def set_voice(self, provider: str, voice_id: str):
        self.storage.save_string(f"tts_voice_{provider}", voice_id)
        self.tts.set_voice(voice_id)
        if provider == "piper":
            self.tts.warm_up("piper", voice_id)
        logger.debug("[ChatService] Set voice for %s: %s", provider, voice_id)

    def speak(self, text: str, voice_id: str = None):
        self.tts.say(text, voice_id=voice_id)

    def stop_tts(self):
        self.tts.stop()
