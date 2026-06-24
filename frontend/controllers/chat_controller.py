# frontend/controllers/chat_controller.py

import re
from PySide6.QtCore import QObject, Slot, Signal
from frontend.workers.voice_worker import VoiceFetcherWorker

class ChatController(QObject):
    tts_state_changed = Signal(bool)

    def __init__(self, view, service, i18n):
        super().__init__()
        self.view = view
        self.service = service
        self.i18n = i18n
        self.muted_bots = []
        self._all_voices = []
        self._voice_worker = None
        self._tts_enabled = True    
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
        self._tts_enabled = settings.get("enabled", True)
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
            handled, plugin_tag, cmd_info, prefix_used = self.command_service.process_incoming_message(user, message, badges)
            
            if handled:
                if plugin_tag.startswith("[PLUGIN_SPOTIFY_"):
                    self._execute_resolved_music_plugin(plugin_tag, user, message, prefix_used)
                return

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
        loading_str = self.view.i18n.get("chat.status.loading_voices")
        self.view.update_voices([("loading", loading_str)], "loading")
        cached = self.service.tts._voices_cache.get(provider, [])
        if cached:
            self._on_voices_fetched(cached, provider, is_initial)
            return

        if self._voice_worker and self._voice_worker.isRunning():
            self._voice_worker.terminate()

        self._voice_worker = VoiceFetcherWorker(self.service.tts, provider, parent=self)
        self._voice_worker.voices_fetched.connect(
            lambda voices, prov: self._on_voices_fetched(voices, prov, is_initial)
        )
        self._voice_worker.error_occurred.connect(self._on_voices_error)
        self._voice_worker.start()

    @Slot(list, str, bool)
    def _on_voices_fetched(self, voices: list, provider: str, is_initial: bool):
        self._all_voices = voices
        saved_voice_id = self.service.get_saved_voice_id(provider)

        langs = []
        for v in self._all_voices:
            prefix = "-".join(v["id"].split("-")[:2]) if "-" in v["id"] else "Local"
            if prefix not in langs:
                langs.append(prefix)

        sel_prefix = "-".join(saved_voice_id.split("-")[:2]) if ("-" in saved_voice_id and saved_voice_id) else "Local"
        self.view.update_languages(langs, sel_prefix)
        self._filter_voices_by_language(sel_prefix, select_id=saved_voice_id, play_test=(not is_initial))

        if self._voice_worker:
            self._voice_worker.deleteLater()
            self._voice_worker = None

    @Slot(str, str)
    def _on_voices_error(self, error_msg: str, provider: str):
        fallback = [
            {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Sin conexión)"},
            {"id": "es-MX-JorgeNeural", "name": "Jorge (Sin conexión)"}
        ]
        self._on_voices_fetched(fallback, provider, is_initial=True)
        
        if hasattr(self.view.window(), 'toast'):
            self.view.window().toast.show_toast(
                title="Red TTS Inestable",
                message=f"Cargado modo offline: {error_msg}",
                state="warning"
            )

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

        if hasattr(self.view.window(), 'toast'):
            mode_name = "Neural IA (Nube Edge)" if is_web else "SAPI5 / OS (Local)"
            state_color = "info" if is_web else "success"

            self.view.window().toast.show_toast(
                title=self.view.i18n.get("chat.status.provider_title"),
                message=f"Modo activo: {mode_name}",
                state=state_color
            )

    @Slot(dict)
    def _handle_settings_save(self, partial_settings: dict):
        partial_settings["ignored_users"] = ",".join(self.muted_bots)
        self.service.save_settings(partial_settings)
        self.tts_state_changed.emit(partial_settings["enabled"])
        new_tts_state = partial_settings["enabled"]
        if hasattr(self, '_tts_enabled') and self._tts_enabled != new_tts_state:
            self._tts_enabled = new_tts_state
            
            if hasattr(self.view.window(), 'toast'):
                status_title = self.view.i18n.get("chat.status.tts_title")
                status_msg = "Voz automática ACTIVADA" if new_tts_state else "Chat SILENCIADO"
                state_color = "success" if new_tts_state else "warning"
                
                self.view.window().toast.show_toast(
                    title=status_title,
                    message=status_msg,
                    state=state_color
                )

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
            if "youtube.com" in url or "youtu.be" in url: return "un enlace de YouTube"
            elif "kick.com" in url: return "un enlace de Kick"
            elif "twitter.com" in url or "x.com" in url: return "un enlace de Twitter"
            elif "instagram.com" in url: return "un enlace de Instagram"
            elif "tiktok.com" in url: return "un enlace de TikTok"
            elif "discord.com" in url or "discord.gg" in url: return "un enlace de Discord"
            elif "spotify.com" in url: return "un enlace de Spotify"
            else: return "un enlace web"
        return re.sub(r"https?://\S+|www\.\S+", replacer, text)
    
    def _execute_resolved_music_plugin(self, tag: str, user: str, message: str, prefix_used: str):
        api = getattr(self.command_service, 'api_client', None)
        if not api: return

        music_ctrl = getattr(self.view.window(), 'music_controller', None)
        provider = music_ctrl.music_provider if music_ctrl else None

        if tag == "[PLUGIN_SPOTIFY_SR]":
            query = message[len(prefix_used):].strip() if prefix_used else ""
            if not query:
                msg = self.i18n.get("music.chat.sr_usage").replace("{user}", user).replace("{trigger}", prefix_used)
                api.post_chat_message(msg)
                return

            if provider:
                success, reply = provider.add_to_queue(query)
                api.post_chat_message(reply)
            else:
                api.post_chat_message(self.i18n.get("music.chat.not_linked"))

        elif tag == "[PLUGIN_SPOTIFY_SKIP]":
            if provider and provider.skip_current():
                api.post_chat_message(self.i18n.get("music.chat.skip_success"))
            else:
                api.post_chat_message(self.i18n.get("music.chat.skip_failed"))

        elif tag == "[PLUGIN_SPOTIFY_SONG]":
            if provider:
                song = provider.get_current_song()
                if song:
                    msg = self.i18n.get("music.chat.song_now_playing").replace("{title}", song["title"]).replace("{artist}", song["artist"])
                    api.post_chat_message(msg)
                else:
                    api.post_chat_message(self.i18n.get("music.chat.song_paused"))
            else:
                api.post_chat_message(self.i18n.get("music.chat.not_linked"))