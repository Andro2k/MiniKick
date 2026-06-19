# frontend/controllers/chat_controller.py

import re

from PySide6.QtCore import QObject, Slot, Signal

class ChatController(QObject):
    tts_state_changed = Signal(bool)

    def __init__(self, view, service):
        super().__init__()
        self.view = view
        self.service = service
        self.muted_bots = []
        self._all_voices = []
        
        self._connect_signals()
        self._load_initial_data()

    def _connect_signals(self):
        self.view.volume_changed.connect(self.service.set_volume)
        self.view.provider_toggled.connect(self._handle_provider_change)
        self.view.voice_changed.connect(self._handle_voice_change)
        self.view.settings_modified.connect(self._handle_settings_save)
        self.view.bot_add_requested.connect(self._add_bot)
        self.view.bot_remove_requested.connect(self._remove_bot)
        self.view.language_filter_changed.connect(self._filter_voices_by_language)

    def _load_initial_data(self):
        settings = self.service.get_settings()
        provider = settings.get("provider", "local")
        self.service.set_provider(provider)
        saved_voice_id = self.service.get_saved_voice_id(provider)
        if saved_voice_id:
            self.service.set_voice(provider, saved_voice_id)

        self.view.set_initial_states(settings)
        self.service.set_volume(settings["volume"])
        
        bots_str = settings.get("ignored_users", "")
        self.muted_bots = [b.strip() for b in bots_str.split(",") if b.strip()]
        for bot in self.muted_bots:
            self.view.add_bot_tag(bot)

        self._load_voices(provider, is_initial=True)

    @Slot(str, str, list, str)
    def handle_incoming_message(self, user: str, message: str, badges: list, color: str):
        self.view.append_message(user, message, color)
        
        if hasattr(self, 'command_service') and self.command_service:
            self.command_service.process_incoming_message(user, message, badges)
            
        settings = self.service.get_settings()
        if not settings["enabled"]:
            return

        if user.lower() in [b.lower() for b in self.muted_bots]:
            return 

        final_message = message.strip()
        if settings["use_command"]:
            cmd = settings["command"]
            if not final_message.lower().startswith(cmd):
                return
            final_message = final_message[len(cmd):].strip()

        final_message = self._clean_message_for_tts(final_message)
        text_to_speak = f"{user} dice: {final_message}" if settings["read_name"] else final_message
        self.service.speak(text_to_speak)

    def _load_voices(self, provider: str, is_initial: bool = False):
        self._all_voices = self.service.get_available_voices(provider)
        saved_voice_id = self.service.get_saved_voice_id(provider)

        langs = []
        for v in self._all_voices:
            prefix = "-".join(v["id"].split("-")[:2]) if "-" in v["id"] else "Local"
            if prefix not in langs:
                langs.append(prefix)

        sel_prefix = "-".join(saved_voice_id.split("-")[:2]) if ("-" in saved_voice_id) else "Local"
        self.view.update_languages(langs, sel_prefix)
        self._filter_voices_by_language(sel_prefix, select_id=saved_voice_id, play_test=(not is_initial))

    @Slot(str)
    def _filter_voices_by_language(self, lang_prefix: str, select_id: str = None, play_test: bool = False):
        filtered = []
        for v in self._all_voices:
            prefix = "-".join(v["id"].split("-")[:2]) if "-" in v["id"] else "Local"
            if prefix == lang_prefix:
                filtered.append((v["id"], v["name"]))
        
        self.view.update_voices(filtered, select_id)

    @Slot(str)
    def _handle_voice_change(self, voice_id: str):
        provider = "web" if ("-" in voice_id) else "local"
        self.service.set_voice(provider, voice_id)
        self.service.speak(self.view.i18n.get("main.controllers.chat.voice_updated"))

    @Slot(bool)
    def _handle_provider_change(self, is_web: bool):
        provider = "web" if is_web else "local"
        self.service.set_provider(provider)
        self._load_voices(provider)

    @Slot(dict)
    def _handle_settings_save(self, partial_settings: dict):
        partial_settings["ignored_users"] = ",".join(self.muted_bots)
        self.service.save_settings(partial_settings)
        self.tts_state_changed.emit(partial_settings["enabled"])

    @Slot(str)
    def _add_bot(self, bot_name: str):
        clean_name = bot_name.strip().lower()
        if clean_name and clean_name not in [b.lower() for b in self.muted_bots]:
            self.muted_bots.append(clean_name)
            self.view.add_bot_tag(clean_name)
            self._save_bot_list()
        self.view.clear_bot_input()

    @Slot(str)
    def _remove_bot(self, bot_name: str):
        clean_name = bot_name.lower()
        if clean_name in [b.lower() for b in self.muted_bots]:
            idx = [b.lower() for b in self.muted_bots].index(clean_name)
            self.muted_bots.pop(idx)
            self._save_bot_list()

    def _save_bot_list(self):
        settings = self.service.get_settings()
        settings["ignored_users"] = ",".join(self.muted_bots)
        self.service.save_settings(settings)

    def _clean_message_for_tts(self, text: str) -> str:
        def replacer(match):
            url = match.group(0).lower()
            if "youtube.com" in url or "youtu.be" in url:
                return "un enlace de YouTube"
            elif "kick.com" in url:
                return "un enlace de Kick"
            elif "twitter.com" in url or "x.com" in url:
                return "un enlace de Twitter"
            elif "instagram.com" in url:
                return "un enlace de Instagram"
            elif "tiktok.com" in url:
                return "un enlace de TikTok"
            elif "discord.com" in url or "discord.gg" in url:
                return "un enlace de Discord"
            else:
                return "un enlace web"
        return re.sub(r"https?://\S+|www\.\S+", replacer, text)