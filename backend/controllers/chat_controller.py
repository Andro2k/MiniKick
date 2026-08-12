# backend\controllers\chat_controller.py

from collections import deque
import logging
from PySide6.QtCore import QObject, Slot, Signal
from backend.handlers import TTSVoiceHandler, ChatFilterHandler
from backend.services import MessagePipeline, ChatMessageDTO

logger = logging.getLogger("minikick.controllers.chat")

class ChatController(QObject):
    tts_state_changed = Signal(bool)
    spam_blocked = Signal()
    command_executed = Signal()
    message_received = Signal(str, str, str, list, str, str)
    music_plugin_triggered = Signal(str, str, str, str, str)
    widget_plugin_triggered = Signal(str, str, str, str)

    def __init__(self, view, service, command_service, spam_service, i18n, timer_service=None, toast_manager=None):
        super().__init__()
        self.view = view
        self.service = service
        self.command_service = command_service
        self.spam_service = spam_service
        self.i18n = i18n
        self.timer_service = timer_service
        self.toast = toast_manager
        self._message_buffer = deque(maxlen=200)

        self.filter_handler = ChatFilterHandler(i18n, service)
        self.voice_handler = TTSVoiceHandler(self, view, service, toast_manager, i18n)

        self._tts_enabled = True
        self._read_name_enabled = True
        self._use_command_enabled = False
        self._tts_settings_cache: dict = {}

        self._exact_plugin_handlers = {
            "[PLUGIN_CHAT_TTS]": self._handle_plugin_tts,
            "[PLUGIN_CHAT_SYSTTS]": self._handle_plugin_systts,
        }

        self.pipeline = MessagePipeline()
        self._build_pipeline()
        self.command_service.response_generated.connect(self._handle_bot_response)
        if self.view is not None:
            self._connect_signals()
            self._load_initial_data()

    def attach_view(self, view) -> None:
        first_attach = (self.view is None)
        self.view = view
        if self.voice_handler:
            self.voice_handler.view = view
        if self.view is not None:
            self._connect_signals()
            self._load_initial_data()
            if first_attach and self._message_buffer:
                for item in self._message_buffer:
                    self.view.append_message(item["user"], item["content"], item["color"], timestamp=item["timestamp"], role=item["role"], platform=item["platform"])

    @property
    def muted_bots(self) -> set[str]:
        return self.filter_handler.muted_bots

    @property
    def banned_words(self) -> set[str]:
        return self.filter_handler.banned_words

    def _build_pipeline(self) -> None:
        self.pipeline.register(self._step_spam)
        self.pipeline.register(self._step_ui_render)
        self.pipeline.register(self._step_commands)
        self.pipeline.register(self._step_tts)

    def _connect_signals(self) -> None:
        self.view.volume_changed.connect(self.service.set_volume)
        self.view.provider_toggled.connect(self.voice_handler.handle_provider_change)
        self.view.voice_changed.connect(self.voice_handler.handle_voice_change)
        self.view.voice_test_requested.connect(self.voice_handler.handle_voice_test)
        self.view.settings_changed.connect(self._handle_settings_save)
        self.view.bot_add_requested.connect(self._add_bot)
        self.view.bot_remove_requested.connect(self._remove_bot)
        self.view.word_add_requested.connect(self._add_word)
        self.view.word_remove_requested.connect(self._remove_word)
        self.view.language_filter_changed.connect(self.voice_handler.filter_voices_by_language)
        self.command_service.commands_changed.connect(self._sync_tts_command_from_db)

    def load_initial_data(self) -> None:
        self._load_initial_data()

    def _load_initial_data(self) -> None:
        settings = self.service.get_settings()
        provider = settings.get("provider", "local")
        self.service.set_provider(provider)
        
        saved_voice_id = self.service.get_saved_voice_id(provider)
        if saved_voice_id:
            self.service.set_voice(provider, saved_voice_id)
            
        self._tts_enabled = settings.get("enabled", True)
        self._read_name_enabled = settings.get("read_name", True)
        self._use_command_enabled = settings.get("use_command", False)
        self._tts_settings_cache = dict(settings)
        
        role_voices = {
            "broadcaster": settings.get("role_voice_broadcaster", ""),
            "moderator": settings.get("role_voice_moderator", ""),
            "vip": settings.get("role_voice_vip", ""),
            "subscriber": settings.get("role_voice_subscriber", "")
        }
        
        if self.view is not None:
            self.view.set_settings_ui(
                enabled=settings.get("enabled", True),
                read_name=settings.get("read_name", True),
                use_command=settings.get("use_command", False),
                command=settings.get("command", "!tts"),
                is_web_provider=(provider == "web"),
                volume=settings.get("volume", 100),
                role_voices=role_voices
            )
            self.filter_handler.initialize_from_settings(settings, self.view)
        self.service.set_volume(settings.get("volume", 100))

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

        if self.view is not None:
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
                    trigger=settings.get("command", "!tts"),
                    response="[PLUGIN_CHAT_TTS]",
                    is_active=settings.get("use_command", False),
                    cooldown=1,
                    aliases="",
                    is_regex=False,
                    permission="everyone"
                )
            finally:
                self.command_service.blockSignals(False)

        existing_systts = next((c for c in commands if c["response"] == "[PLUGIN_CHAT_SYSTTS]"), None)
        if not existing_systts:
            self.command_service.blockSignals(True)
            try:
                self.command_service.save_command(
                    trigger="!systts",
                    response="[PLUGIN_CHAT_SYSTTS]",
                    is_active=True,
                    cooldown=3,
                    aliases="!ttssys",
                    is_regex=False,
                    permission="moderator"
                )
            finally:
                self.command_service.blockSignals(False)

        self.voice_handler.load_voices(provider, is_initial=True)

    def sync_settings_cache(self) -> None:
        self._tts_settings_cache = self.service.get_settings()
        self._tts_enabled = self._tts_settings_cache.get("enabled", True)

    @Slot(object)
    def process_message(self, dto: ChatMessageDTO) -> None:
        self.pipeline.execute(dto)
        if not dto.is_cancelled and self.timer_service:
            self.timer_service.increment_chat_lines()

    def _step_spam(self, dto: ChatMessageDTO) -> None:
        emotes_tag = getattr(dto, "emotes_tag", "")
        platform = getattr(dto, "platform", "kick")
        if self.spam_service.is_spam(dto.user, dto.content, dto.badges, dto.msg_id, dto.sender_id, emotes_tag=emotes_tag, platform=platform):
            dto.is_cancelled = True
            self.spam_blocked.emit()

    def _step_commands(self, dto: ChatMessageDTO) -> None:
        platform = getattr(dto, "platform", "kick")
        handled, plugin_tag, cmd_info, prefix = self.command_service.process_incoming_message(dto.user, dto.content, dto.badges, platform=platform)
        if not handled:
            return

        is_regex = cmd_info.get("is_regex", False) if isinstance(cmd_info, dict) else False
        if not is_regex:
            dto.is_command = True
        self.command_executed.emit()

        exact_handler = self._exact_plugin_handlers.get(plugin_tag)
        if exact_handler:
            exact_handler(dto, prefix)
            return

        if plugin_tag.startswith("[PLUGIN_MUSIC_"):
            self.music_plugin_triggered.emit(plugin_tag, dto.user, dto.content, prefix, platform)
        elif plugin_tag.startswith("[PLUGIN_WIDGET_"):
            self.widget_plugin_triggered.emit(plugin_tag, dto.user, dto.content, prefix)

    def _handle_plugin_tts(self, dto: ChatMessageDTO, prefix: str) -> None:
        msg_content = dto.content[len(prefix):].strip()
        if not msg_content:
            return
        emotes_tag = getattr(dto, "emotes_tag", "")
        cleaned = self.filter_handler.clean_message_for_tts(msg_content, emotes_tag=emotes_tag)
        if cleaned:
            settings = self._tts_settings_cache
            text = self.i18n.get("chat.status.user_says").replace("{user}", dto.user).replace("{message}", cleaned) if settings.get("read_name", True) else cleaned
            voice_id = self.voice_handler.resolve_voice_for_badges(dto.badges, settings)
            self.service.speak(text, voice_id=voice_id)

    def _handle_plugin_systts(self, dto: ChatMessageDTO, prefix: str) -> None:
        msg_content = dto.content[len(prefix):].strip()
        platform = getattr(dto, "platform", "kick")
        self._handle_systts_command(dto.user, msg_content, platform=platform)

    def _handle_systts_command(self, user: str, arg: str, platform: str = "kick") -> None:
        arg_clean = arg.strip().lower()
        if arg_clean in ("on", "1", "enable", "activar", "encender"):
            new_state = True
        elif arg_clean in ("off", "0", "disable", "desactivar", "apagar"):
            new_state = False
        elif not arg_clean or arg_clean == "status":
            state_str = self.i18n.get("chat.status.enabled_upper") if self._tts_enabled else self.i18n.get("chat.status.disabled_upper")
            status_msg = self.i18n.get("chat.status.systts_status").replace("{user}", user).replace("{state}", state_str)
            self.command_service.send_response(status_msg, platform=platform)
            return
        else:
            usage_msg = self.i18n.get("chat.status.systts_usage").replace("{user}", user)
            self.command_service.send_response(usage_msg, platform=platform)
            return

        self._tts_enabled = new_state
        settings = self.service.get_settings()
        settings["enabled"] = new_state
        self.service.save_settings(settings)
        self.sync_settings_cache()

        self.tts_state_changed.emit(new_state)
        if self.view is not None and hasattr(self.view, "set_tts_enabled_state"):
            self.view.set_tts_enabled_state(new_state)

        key = "chat.status.systts_on" if new_state else "chat.status.systts_off"
        reply = self.i18n.get(key).replace("{user}", user)
        self.command_service.send_response(reply, platform=platform)

    def _resolve_user_role(self, badges: list, user: str) -> str:
        if "broadcaster" in badges:
            return self.i18n.get("chat.roles.name_broadcaster")
        elif "moderator" in badges:
            return self.i18n.get("chat.roles.name_moderator")
        elif "vip" in badges:
            return self.i18n.get("chat.roles.name_vip")
        elif "subscriber" in badges:
            return self.i18n.get("chat.roles.name_subscriber")
        elif self.filter_handler.is_bot(user, badges):
            return self.i18n.get("chat.roles.name_bot")
        return self.i18n.get("chat.roles.name_user")

    def _step_ui_render(self, dto: ChatMessageDTO) -> None:
        badges = list(dto.badges) if dto.badges else []
        if self.filter_handler.is_bot(dto.user) and "bot" not in badges:
            badges.append("bot")
        role_name = self._resolve_user_role(badges, dto.user)
        platform = getattr(dto, "platform", "kick")
        item = {
            "user": dto.user, "content": dto.content, "color": dto.color, "timestamp": dto.timestamp,
            "role": role_name, "platform": platform
        }
        self._message_buffer.append(item)
        if self.view is not None:
            self.view.append_message(dto.user, dto.content, dto.color, timestamp=dto.timestamp, role=role_name, platform=platform)
        emotes_tag = getattr(dto, "emotes_tag", "")
        self.message_received.emit(dto.user, dto.content, dto.color, badges, platform, emotes_tag)

    def _handle_bot_response(self, text: str, platform: str = "kick") -> None:
        if not text or platform != "twitch":
            return
        import datetime
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        bot_user = "MiniKick"
        if hasattr(self.command_service, "twitch_worker") and self.command_service.twitch_worker:
            tw_worker = self.command_service.twitch_worker
            bot_user = getattr(tw_worker, "bot_nick", "") or getattr(tw_worker, "channel_name", "")
        
        dto = ChatMessageDTO(
            user=bot_user, content=text, badges=["broadcaster", "bot"], color="#9146FF",
            msg_id="", sender_id=0, timestamp=now_str, platform="twitch", is_cancelled=False, is_command=False
        )
        self._step_ui_render(dto)

    def _step_tts(self, dto: ChatMessageDTO) -> None:
        if getattr(dto, "is_command", False):
            return
        settings = self._tts_settings_cache
        if not settings.get("enabled", True) or self.filter_handler.is_bot(dto.user):
            return

        msg = dto.content.strip()
        if settings.get("use_command", False):
            cmd = settings.get("command", "!tts")
            if not msg.lower().startswith(cmd):
                return
            msg = msg[len(cmd):].strip()

        if self.filter_handler.is_message_banned(msg):
            return

        emotes_tag = getattr(dto, "emotes_tag", "")
        cleaned = self.filter_handler.clean_message_for_tts(msg, emotes_tag=emotes_tag)
        if cleaned:
            text = self.i18n.get("chat.status.user_says").replace("{user}", dto.user).replace("{message}", cleaned) if settings.get("read_name", True) else cleaned
            voice_id = self.voice_handler.resolve_voice_for_badges(dto.badges, settings)
            self.service.speak(text, voice_id=voice_id)

    @Slot()
    def _handle_settings_save(self) -> None:
        settings = {
            "enabled": self.view.tts_enabled,
            "read_name": self.view.read_name_enabled,
            "use_command": self.view.use_command_enabled,
            "command": self.view.tts_command,
            "provider": "web" if self.view.is_web_provider else "local",
            "ignored_users": ",".join(self.filter_handler.muted_bots),
            "banned_words": ",".join(self.filter_handler.banned_words)
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
            target_trigger = settings["command"].strip()
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

            existing_systts = next((c for c in commands if c["response"] == "[PLUGIN_CHAT_SYSTTS]"), None)
            if not existing_systts:
                self.command_service.save_command(
                    trigger="!systts",
                    response="[PLUGIN_CHAT_SYSTTS]",
                    is_active=True,
                    cooldown=3,
                    aliases="!ttssys",
                    is_regex=False,
                    permission="moderator"
                )
        finally:
            self.command_service.blockSignals(False)

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.command_service.commands_changed.emit)

        new_tts_state = settings["enabled"]
        if hasattr(self, '_tts_enabled') and self._tts_enabled != new_tts_state:
            self._tts_enabled = new_tts_state
            if self.toast:
                status_title = self.view.i18n.get("chat.status.tts_title")
                status_msg = self.view.i18n.get("chat.status.tts_active") if new_tts_state else self.view.i18n.get("chat.status.tts_muted")
                state_color = "success" if new_tts_state else "warning"
                
                self.toast.show_toast(
                    title=status_title,
                    message=status_msg,
                    state=state_color
                )

        new_read_name_state = settings["read_name"]
        if hasattr(self, '_read_name_enabled') and self._read_name_enabled != new_read_name_state:
            self._read_name_enabled = new_read_name_state
            if self.toast:
                title = self.i18n.get("chat.status.read_name_title")
                msg = self.i18n.get("chat.status.read_name_active") if new_read_name_state else self.i18n.get("chat.status.read_name_inactive")
                color = "success" if new_read_name_state else "warning"
                self.toast.show_toast(title=title, message=msg, state=color)

        new_use_cmd_state = settings["use_command"]
        if hasattr(self, '_use_command_enabled') and self._use_command_enabled != new_use_cmd_state:
            self._use_command_enabled = new_use_cmd_state
            if self.toast:
                title = self.i18n.get("chat.status.use_command_title")
                msg = self.i18n.get("chat.status.use_command_active") if new_use_cmd_state else self.i18n.get("chat.status.use_command_inactive")
                color = "success" if new_use_cmd_state else "warning"
                self.toast.show_toast(title=title, message=msg, state=color)

    def _sync_tts_command_from_db(self) -> None:
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
            if self.view is not None:
                self.view.set_tts_command_configuration(use_command, command_trigger)

    @Slot(str)
    def _add_bot(self, bot_name: str) -> None:
        self.filter_handler.add_bot(bot_name, self.view)
        self.view.clear_bot_input()

    @Slot(str)
    def _remove_bot(self, bot_name: str) -> None:
        self.filter_handler.remove_bot(bot_name)

    @Slot(str)
    def _add_word(self, word: str) -> None:
        self.filter_handler.add_word(word, self.view)
        self.view.clear_word_input()

    @Slot(str)
    def _remove_word(self, word: str) -> None:
        self.filter_handler.remove_word(word)
