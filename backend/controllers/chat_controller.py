# frontend\controllers\chat_controller.py

import re
from PySide6.QtCore import QObject, Slot, Signal
from frontend.workers.voice_worker import VoiceFetcherWorker
from backend.services.chat.pipeline import MessagePipeline, ChatMessageDTO

class ChatController(QObject):
    tts_state_changed = Signal(bool)
    _URL_REGEX = re.compile(r"https?://\S+|www\.\S+")
    _EMOTE_REGEX = re.compile(r"\[emote:[^\]]+\]")
    _SPACES_REGEX = re.compile(r"\s+")

    def __init__(self, view, service, command_service, spam_service, i18n):
        super().__init__()
        self.view = view
        self.service = service
        self.command_service = command_service
        self.spam_service = spam_service
        self.i18n = i18n        
        self.muted_bots: set[str] = set()
        self._all_voices: list[dict] = []
        self._voice_worker = None
        self._tts_enabled = True
        self._tts_settings_cache: dict = {}
        
        self.pipeline = MessagePipeline()
        self._build_pipeline()
        
        self._connect_signals()
        self._load_initial_data()

    def _build_pipeline(self):
        self.pipeline.register(self._step_spam)
        self.pipeline.register(self._step_commands)
        self.pipeline.register(self._step_ui_render)
        self.pipeline.register(self._step_tts)

    def _connect_signals(self):
        self.view.volume_changed.connect(self.service.set_volume)
        self.view.provider_toggled.connect(self._handle_provider_change)
        self.view.voice_changed.connect(self._handle_voice_change)
        self.view.settings_changed.connect(self._handle_settings_save)
        self.view.bot_add_requested.connect(self._add_bot)
        self.view.bot_remove_requested.connect(self._remove_bot)
        self.view.language_filter_changed.connect(self._filter_voices_by_language)

    def load_initial_data(self):
        self._load_initial_data()

    def _load_initial_data(self):
        settings = self.service.get_settings()
        provider = settings.get("provider", "local")
        self.service.set_provider(provider)
        
        saved_voice_id = self.service.get_saved_voice_id(provider)
        if saved_voice_id:
            self.service.set_voice(provider, saved_voice_id)
            
        self._tts_enabled = settings.get("enabled", True)
        self._tts_settings_cache = dict(settings)
        
        self.view.set_settings_ui(
            enabled=settings.get("enabled", True),
            read_name=settings.get("read_name", True),
            use_command=settings.get("use_command", False),
            command=settings.get("command", "!tts"),
            is_web_provider=(provider == "web"),
            volume=settings.get("volume", 100)
        )
        self.service.set_volume(settings["volume"])     
        
        bots_str = settings.get("ignored_users", "")
        self.muted_bots = {b.strip().lower() for b in bots_str.split(",") if b.strip()}
        
        self.view.clear_bots_list()
        for bot in self.muted_bots:
            self.view.add_bot_tag(bot)

        self._load_voices(provider, is_initial=True)

    def sync_settings_cache(self) -> None:
        self._tts_settings_cache = self.service.get_settings()
        self._tts_enabled = self._tts_settings_cache.get("enabled", True)

    @Slot(object)
    def process_message(self, dto: ChatMessageDTO):
        self.pipeline.execute(dto)

    def _step_spam(self, dto: ChatMessageDTO):
        if self.spam_service.is_spam(dto.user, dto.content, dto.badges, dto.msg_id, dto.sender_id):
            dto.is_cancelled = True

    def _step_commands(self, dto: ChatMessageDTO):
        handled, plugin_tag, _, prefix = self.command_service.process_incoming_message(dto.user, dto.content, dto.badges)
        if handled:
            dto.is_cancelled = True
            if plugin_tag.startswith("[PLUGIN_SPOTIFY_"):
                self._execute_resolved_music_plugin(plugin_tag, dto.user, dto.content, prefix)

    def _step_ui_render(self, dto: ChatMessageDTO):
        self.view.append_message(dto.user, dto.content, dto.color)

    def _step_tts(self, dto: ChatMessageDTO):
        settings = self._tts_settings_cache
        if not settings.get("enabled", True) or dto.user.lower() in self.muted_bots:
            return

        msg = dto.content.strip()
        if settings["use_command"]:
            cmd = settings["command"]
            if not msg.lower().startswith(cmd):
                return
            msg = msg[len(cmd):].strip()

        cleaned = self._clean_message_for_tts(msg)
        if cleaned:
            text = f"{dto.user} dice: {cleaned}" if settings["read_name"] else cleaned
            self.service.speak(text)

    def _load_voices(self, provider: str, is_initial: bool = False):
        loading_str = self.view.i18n.get("chat.status.loading_voices")
        self.view.update_voices([("loading", loading_str)], "loading")
        
        cached = self.service.tts._voices_cache.get(provider, [])
        if cached:
            self._on_voices_fetched(cached, provider, is_initial)
            return

        if self._voice_worker:
            if self._voice_worker.isRunning():
                try:
                    self._voice_worker.voices_fetched.disconnect()
                    self._voice_worker.error_occurred.disconnect()
                except Exception:
                    pass
                self._voice_worker.terminate()
                self._voice_worker.wait(500)
            self._voice_worker.deleteLater()
            self._voice_worker = None

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

        langs = list(dict.fromkeys(
            "-".join(v["id"].split("-")[:2]) if "-" in v["id"] else "Local"
            for v in self._all_voices
        ))

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
        filtered = [
            (v["id"], v["name"]) for v in self._all_voices
            if ("-".join(v["id"].split("-")[:2]) if "-" in v["id"] else "Local") == lang_prefix
        ]
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

    @Slot()
    def _handle_settings_save(self):
        settings = {
            "enabled": self.view.tts_enabled,
            "read_name": self.view.read_name_enabled,
            "use_command": self.view.use_command_enabled,
            "command": self.view.tts_command,
            "provider": "web" if self.view.is_web_provider else "local",
            "ignored_users": ",".join(self.muted_bots)
        }
        self.service.save_settings(settings)
        self._tts_settings_cache = self.service.get_settings()
        self.tts_state_changed.emit(settings["enabled"])
        new_tts_state = settings["enabled"]
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
        if clean_name and clean_name not in self.muted_bots:
            self.muted_bots.add(clean_name)
            self.view.add_bot_tag(clean_name)
            self._save_bot_list()
        self.view.clear_bot_input()

    @Slot(str)
    def _remove_bot(self, bot_name: str):
        clean_name = bot_name.lower()
        if clean_name in self.muted_bots:
            self.muted_bots.remove(clean_name)
            self._save_bot_list()

    def _save_bot_list(self):
        settings = self.service.get_settings()
        settings["ignored_users"] = ",".join(self.muted_bots)
        self.service.save_settings(settings)

    def _clean_message_for_tts(self, text: str) -> str:
        def replacer(match):
            url = match.group(0).lower()
            keywords = {
                "youtube.com": "un enlace de YouTube", "youtu.be": "un enlace de YouTube",
                "kick.com": "un enlace de Kick",
                "twitter.com": "un enlace de Twitter", "x.com": "un enlace de Twitter",
                "instagram.com": "un enlace de Instagram",
                "tiktok.com": "un enlace de TikTok",
                "discord.com": "un enlace de Discord", "discord.gg": "un enlace de Discord",
                "spotify.com": "un enlace de Spotify"
            }
            for kw, replacement in keywords.items():
                if kw in url:
                    return replacement
            return "un enlace web"
        
        cleaned = self._URL_REGEX.sub(replacer, text)
        cleaned = self._EMOTE_REGEX.sub("", cleaned)
        return self._SPACES_REGEX.sub(" ", cleaned).strip()
    
    def _execute_resolved_music_plugin(self, tag: str, user: str, message: str, prefix_used: str):
        api = getattr(self.command_service, 'api_client', None)
        if not api: 
            return
        music_ctrl = getattr(self.view.window(), 'music_controller', None)
        provider = music_ctrl.music_provider if music_ctrl else None
        dispatch_table = {
            "[PLUGIN_SPOTIFY_SR]": self._handle_plugin_sr,
            "[PLUGIN_SPOTIFY_SKIP]": self._handle_plugin_skip,
            "[PLUGIN_SPOTIFY_SONG]": self._handle_plugin_song,
        }
        
        executor = dispatch_table.get(tag)
        if executor:
            executor(api, provider, user, message, prefix_used)

    def _handle_plugin_sr(self, api, provider, user, message, prefix_used):
        query = message[len(prefix_used):].strip() if prefix_used else ""
        if not query:
            msg = self.i18n.get("music.chat.sr_usage").replace("{user}", user).replace("{trigger}", prefix_used)
            api.post_chat_message(msg)
            return
        if provider:
            def on_complete(success, reply_msg):
                api.post_chat_message(reply_msg)
                
            success, immediate_reply = provider.add_to_queue(query, callback=on_complete)
            if immediate_reply:
                api.post_chat_message(immediate_reply)
        else:
            api.post_chat_message(self.i18n.get("music.chat.not_linked"))

    def _handle_plugin_skip(self, api, provider, user, message, prefix_used):
        if provider and provider.skip_current():
            api.post_chat_message(self.i18n.get("music.chat.skip_success"))
        else:
            api.post_chat_message(self.i18n.get("music.chat.skip_failed"))

    def _handle_plugin_song(self, api, provider, user, message, prefix_used):
        if provider:
            song = provider.get_current_song()
            if song:
                msg = self.i18n.get("music.chat.song_now_playing").replace("{title}", song["title"]).replace("{artist}", song["artist"])
                api.post_chat_message(msg)
            else:
                api.post_chat_message(self.i18n.get("music.chat.song_paused"))
        else:
            api.post_chat_message(self.i18n.get("music.chat.not_linked"))