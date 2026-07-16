# backend\controllers\chat_controller.py

import re
from PySide6.QtCore import QObject, Slot, Signal
from backend.services.chat.pipeline import MessagePipeline, ChatMessageDTO

class ChatController(QObject):
    tts_state_changed = Signal(bool)
    spam_blocked = Signal()
    command_executed = Signal()
    message_received = Signal(str, str, str, list)
    music_plugin_triggered = Signal(str, str, str, str)
    _URL_REGEX = re.compile(r"https?://\S+|www\.\S+")
    _EMOTE_REGEX = re.compile(r"\[emote:[^\]]+\]")
    _SPACES_REGEX = re.compile(r"\s+")
    _ROLE_PRIORITIES = ("broadcaster", "moderator", "vip", "subscriber")
    _DEFAULT_BOTS = frozenset({"botrix", "nightbot", "streamelements", "moobot", "@minikick"})

    def __init__(self, view, service, command_service, spam_service, i18n, timer_service=None, toast_manager=None):
        super().__init__()
        self.view = view
        self.service = service
        self.command_service = command_service
        self.spam_service = spam_service
        self.i18n = i18n        
        self.timer_service = timer_service
        self.toast = toast_manager
        self.muted_bots: set[str] = set()
        self.banned_words: set[str] = set()
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
        self.view.word_add_requested.connect(self._add_word)
        self.view.word_remove_requested.connect(self._remove_word)
        self.view.language_filter_changed.connect(self._filter_voices_by_language)
        self.command_service.commands_changed.connect(self._sync_tts_command_from_db)

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
        
        role_voices = {
            "broadcaster": settings.get("role_voice_broadcaster", ""),
            "moderator": settings.get("role_voice_moderator", ""),
            "vip": settings.get("role_voice_vip", ""),
            "subscriber": settings.get("role_voice_subscriber", "")
        }
        
        self.view.set_settings_ui(
            enabled=settings.get("enabled", True),
            read_name=settings.get("read_name", True),
            use_command=settings.get("use_command", False),
            command=settings.get("command", "!tts"),
            is_web_provider=(provider == "web"),
            volume=settings.get("volume", 100),
            role_voices=role_voices
        )
        self.service.set_volume(settings["volume"])     
        
        bots_str = settings.get("ignored_users", "")
        self.muted_bots = {b.strip().lower() for b in bots_str.split(",") if b.strip()}
        
        self.view.clear_bots_list()
        for bot in self.muted_bots:
            self.view.add_bot_tag(bot)

        words_str = settings.get("banned_words", "")
        self.banned_words = {w.strip().lower() for w in words_str.split(",") if w.strip()}
        
        self.view.clear_words_list()
        for word in self.banned_words:
            self.view.add_word_tag(word)

        overlay_theme = self.service.storage.load_string("chat_overlay_theme", "glass")
        try:
            overlay_size = int(self.service.storage.load_string("chat_overlay_size", "14"))
        except ValueError:
            overlay_size = 14
        try:
            overlay_fade = int(self.service.storage.load_string("chat_overlay_fade", "15"))
        except ValueError:
            overlay_fade = 15
        overlay_show_bots = self.service.storage.load_bool("chat_overlay_show_bots", False)
        overlay_show_time = self.service.storage.load_bool("chat_overlay_show_time", False)

        self.view.set_overlay_settings_ui(
            theme=overlay_theme,
            size=overlay_size,
            fade=overlay_fade,
            show_bots=overlay_show_bots,
            show_time=overlay_show_time
        )

        commands = self.command_service.get_all_commands()
        existing = next((c for c in commands if c["response"] == "[PLUGIN_CHAT_TTS]"), None)
        if not existing:
            self.command_service.blockSignals(True)
            try:
                self.command_service.save_command(
                    trigger=settings.get("command", "!tts") or "!tts",
                    response="[PLUGIN_CHAT_TTS]",
                    is_active=settings.get("use_command", False),
                    cooldown=1,
                    aliases="",
                    is_regex=False,
                    permission="everyone"
                )
            finally:
                self.command_service.blockSignals(False)

        self._load_voices(provider, is_initial=True)

    def sync_settings_cache(self) -> None:
        self._tts_settings_cache = self.service.get_settings()
        self._tts_enabled = self._tts_settings_cache.get("enabled", True)

    @Slot(object)
    def process_message(self, dto: ChatMessageDTO):
        self.pipeline.execute(dto)
        if not dto.is_cancelled:
            if self.timer_service:
                self.timer_service.increment_chat_lines()

    def _step_spam(self, dto: ChatMessageDTO):
        if self.spam_service.is_spam(dto.user, dto.content, dto.badges, dto.msg_id, dto.sender_id):
            dto.is_cancelled = True
            self.spam_blocked.emit()

    def _step_commands(self, dto: ChatMessageDTO):
        handled, plugin_tag, _, prefix = self.command_service.process_incoming_message(dto.user, dto.content, dto.badges)
        if handled:
            dto.is_command = True
            self.command_executed.emit()
            if plugin_tag.startswith("[PLUGIN_SPOTIFY_"):
                self.music_plugin_triggered.emit(plugin_tag, dto.user, dto.content, prefix)
            elif plugin_tag == "[PLUGIN_CHAT_TTS]":
                msg_content = dto.content[len(prefix):].strip()
                if msg_content:
                    if self._is_message_banned(msg_content):
                        return
                    cleaned = self._clean_message_for_tts(msg_content)
                    if cleaned:
                        settings = self._tts_settings_cache
                        # Cambiar el texto por i18n
                        text = f"{dto.user} dice: {cleaned}" if settings["read_name"] else cleaned
                        voice_id = self._resolve_voice_for_badges(dto.badges, settings)
                        self.service.speak(text, voice_id=voice_id)

    def _step_ui_render(self, dto: ChatMessageDTO):
        self.view.append_message(dto.user, dto.content, dto.color, timestamp=dto.timestamp)
        badges = list(dto.badges) if dto.badges else []
        username_lower = dto.user.lower()
        if username_lower in self._DEFAULT_BOTS or username_lower.endswith("bot"):
            if "bot" not in badges:
                badges.append("bot")
        self.message_received.emit(dto.user, dto.content, dto.color or "#FAFAFA", badges)

    def _resolve_voice_for_badges(self, badges: list, settings: dict) -> str | None:
        available_ids = {v["id"] for v in self._all_voices}
        for badge in self._ROLE_PRIORITIES:
            if badge in badges:
                voice_id = settings.get(f"role_voice_{badge}", "")
                if voice_id in available_ids:
                    return voice_id
        return None

    def _is_message_banned(self, msg: str) -> bool:
        msg_lower = msg.lower()
        return any(re.search(r'\b' + re.escape(w) + r'\b', msg_lower) for w in self.banned_words)

    def _step_tts(self, dto: ChatMessageDTO):
        if getattr(dto, "is_command", False):
            return
        settings = self._tts_settings_cache
        if not settings.get("enabled", True) or dto.user.lower() in self.muted_bots:
            return

        msg = dto.content.strip()
        if settings["use_command"]:
            cmd = settings["command"]
            if not msg.lower().startswith(cmd):
                return
            msg = msg[len(cmd):].strip()

        if self._is_message_banned(msg):
            return

        cleaned = self._clean_message_for_tts(msg)
        # Cambiar el texto por i18n
        if cleaned:
            text = f"{dto.user} dice: {cleaned}" if settings["read_name"] else cleaned
            voice_id = self._resolve_voice_for_badges(dto.badges, settings)
            self.service.speak(text, voice_id=voice_id)

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

        from backend.workers.voice_worker import VoiceFetcherWorker
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
        
        if self.toast:
            self.toast.show_toast(
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
        settings = self.service.get_settings()
        role_voices = {
            "broadcaster": settings.get("role_voice_broadcaster", ""),
            "moderator": settings.get("role_voice_moderator", ""),
            "vip": settings.get("role_voice_vip", ""),
            "subscriber": settings.get("role_voice_subscriber", "")
        }

        all_voices_list = []
        for v in self._all_voices:
            v_id = v["id"]
            v_name = v["name"]
            if "-" in v_id:
                region = "-".join(v_id.split("-")[:2])
                display_name = f"[{region}] {v_name}"
            else:
                display_name = f"[Local] {v_name}"
            all_voices_list.append((v_id, display_name))
            
        self.view.update_voices(filtered, select_id, role_voices, all_voices_list)

    @Slot(str)
    def _handle_voice_change(self, voice_id: str):
        provider = "web" if ("-" in voice_id) else "local"
        self.service.set_voice(provider, voice_id)
        self.sync_settings_cache()
        self.service.speak(self.view.i18n.get("main.controllers.chat.voice_updated"))

    @Slot(bool)
    def _handle_provider_change(self, is_web: bool):
        provider = "web" if is_web else "local"
        self.service.set_provider(provider)
        self.sync_settings_cache()
        self._load_voices(provider)
        
        if self.toast:
            mode_name = "Neural IA (Nube Edge)" if is_web else "SAPI5 / OS (Local)"
            state_color = "info" if is_web else "success"

            self.toast.show_toast(
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
            "ignored_users": ",".join(self.muted_bots),
            "banned_words": ",".join(self.banned_words)
        }
        settings.update(self.view.get_role_voices())
        settings.update({
            "chat_overlay_theme": self.view.overlay_theme,
            "chat_overlay_size": str(self.view.overlay_size),
            "chat_overlay_fade": str(self.view.overlay_fade),
            "chat_overlay_show_bots": self.view.overlay_show_bots,
            "chat_overlay_show_time": self.view.overlay_show_time
        })
        self.service.save_settings(settings)
        self._tts_settings_cache = self.service.get_settings()
        self.tts_state_changed.emit(settings["enabled"])
        commands = self.command_service.get_all_commands()
        existing = next((c for c in commands if c["response"] == "[PLUGIN_CHAT_TTS]"), None)
        
        self.command_service.blockSignals(True)
        try:
            target_trigger = settings["command"].strip() or "!tts"
            if existing:
                if existing["trigger"] != target_trigger:
                    self.command_service.delete_command(existing["trigger"])
                self.command_service.save_command(
                    trigger=target_trigger,
                    response="[PLUGIN_CHAT_TTS]",
                    is_active=settings["use_command"],
                    cooldown=existing.get("cooldown", 1),
                    aliases=existing.get("aliases", ""),
                    is_regex=existing.get("is_regex", False),
                    permission=existing.get("permission", "everyone")
                )
            else:
                self.command_service.save_command(
                    trigger=target_trigger,
                    response="[PLUGIN_CHAT_TTS]",
                    is_active=settings["use_command"],
                    cooldown=1,
                    aliases="",
                    is_regex=False,
                    permission="everyone"
                )
        finally:
            self.command_service.blockSignals(False)
            self.command_service.commands_changed.emit()

        new_tts_state = settings["enabled"]
        if hasattr(self, '_tts_enabled') and self._tts_enabled != new_tts_state:
            self._tts_enabled = new_tts_state
            #  Cambiar los  textos por i18n
            if self.toast:
                status_title = self.view.i18n.get("chat.status.tts_title")
                status_msg = "Voz automática activada" if new_tts_state else "Chat silenciado"
                state_color = "success" if new_tts_state else "warning"
                
                self.toast.show_toast(
                    title=status_title,
                    message=status_msg,
                    state=state_color
                )

    def _sync_tts_command_from_db(self):
        commands = self.command_service.get_all_commands()
        tts_cmd = next((c for c in commands if c["response"] == "[PLUGIN_CHAT_TTS]"), None)
        
        settings = self.service.get_settings()
        
        if tts_cmd:
            use_command = tts_cmd["is_active"]
            command_trigger = tts_cmd["trigger"]
        else:
            use_command = False
            command_trigger = settings.get("command", "!tts")
            
        if settings.get("use_command", False) != use_command or settings.get("command", "") != command_trigger:
            settings["use_command"] = use_command
            settings["command"] = command_trigger
            self.service.save_settings(settings)
            self._tts_settings_cache = settings           
            self.view.blockSignals(True)
            self.view.chk_command.blockSignals(True)
            self.view.txt_command.blockSignals(True)           
            self.view.chk_command.setChecked(use_command)
            self.view.txt_command.setText(command_trigger)            
            self.view.chk_command.blockSignals(False)
            self.view.txt_command.blockSignals(False)
            self.view.blockSignals(False)

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

    @Slot(str)
    def _add_word(self, word: str):
        clean_word = word.strip().lower()
        if clean_word and clean_word not in self.banned_words:
            self.banned_words.add(clean_word)
            self.view.add_word_tag(clean_word)
            self._save_word_list()
        self.view.clear_word_input()

    @Slot(str)
    def _remove_word(self, word: str):
        clean_word = word.lower()
        if clean_word in self.banned_words:
            self.banned_words.remove(clean_word)
            self._save_word_list()

    def _save_word_list(self):
        settings = self.service.get_settings()
        settings["banned_words"] = ",".join(self.banned_words)
        self.service.save_settings(settings)

    def _clean_message_for_tts(self, text: str) -> str:
        # Cambiar el texto por i18n
        cleaned = self._URL_REGEX.sub("un enlace web", text)
        cleaned = self._EMOTE_REGEX.sub("", cleaned)
        return self._SPACES_REGEX.sub(" ", cleaned).strip()
