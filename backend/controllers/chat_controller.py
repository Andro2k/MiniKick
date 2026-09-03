# backend\controllers\chat_controller.py

from collections import deque
import datetime
import logging
from PySide6.QtCore import QObject, QTimer, Signal, Slot
from backend.handlers import TTSVoiceHandler, ChatFilterHandler
from backend.services import MessagePipeline, ChatMessageDTO

logger = logging.getLogger("minikick.controllers.chat")

_SYSTTS_ON_KEYWORDS = frozenset({"on", "1", "enable", "activar", "encender"})
_SYSTTS_OFF_KEYWORDS = frozenset({"off", "0", "disable", "desactivar", "apagar"})

def _find_command_by_response(commands: list[dict], response_tag: str) -> dict | None:
    for cmd in commands:
        if cmd.get("response") == response_tag:
            return cmd
    return None

class ChatController(QObject):
    tts_state_changed = Signal(bool)
    spam_blocked = Signal()
    command_executed = Signal()
    message_received = Signal(str, str, str, object, str, str)
    music_plugin_triggered = Signal(str, str, str, str, str)
    widget_plugin_triggered = Signal(str, str, str, str, str)

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

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(200)
        self._save_timer.timeout.connect(self._flush_settings_save)

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
        if hasattr(self.view, "speed_changed"):
            self.view.speed_changed.connect(self.service.set_speed)
        if hasattr(self.view, "provider_changed"):
            self.view.provider_changed.connect(self.voice_handler.handle_provider_change)
        if hasattr(self.view, "tts_settings_panel"):
            if hasattr(self.view.tts_settings_panel, "manage_piper_voices_requested"):
                self.view.tts_settings_panel.manage_piper_voices_requested.connect(self.voice_handler.open_piper_voices_dialog)
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
        provider = settings.get("provider", "piper")
        self.service.set_provider(provider)
            
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
        role_enabled = {
            "everyone": settings.get("role_enabled_everyone", True),
            "broadcaster": settings.get("role_enabled_broadcaster", True),
            "moderator": settings.get("role_enabled_moderator", True),
            "vip": settings.get("role_enabled_vip", True),
            "subscriber": settings.get("role_enabled_subscriber", True)
        }
        
        if self.view is not None:
            self.view.set_settings_ui(
                enabled=settings.get("enabled", True),
                read_name=settings.get("read_name", True),
                use_command=settings.get("use_command", False),
                command=settings.get("command", "!tts"),
                is_web_provider=(provider == "web"),
                volume=settings.get("volume", 100),
                role_voices=role_voices,
                role_enabled=role_enabled,
                provider=provider,
                speed=settings.get("speed", 100)
            )
            self.filter_handler.initialize_from_settings(settings, self.view)
        self.service.set_volume(settings.get("volume", 100))
        self.service.set_speed(settings.get("speed", 100))

        overlay_settings = self.service.get_overlay_settings()
        if self.view is not None:
            self.view.set_overlay_settings_ui(
                theme=overlay_settings["theme"],
                size=overlay_settings["size"],
                fade=overlay_settings["fade"],
                show_bots=overlay_settings["show_bots"],
                show_time=overlay_settings["show_time"]
            )

        commands = self.command_service.get_all_commands()
        existing = _find_command_by_response(commands, "[PLUGIN_CHAT_TTS]")
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

        existing_systts = _find_command_by_response(commands, "[PLUGIN_CHAT_SYSTTS]")
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
        platform = getattr(dto, "platform", "kick")
        if not dto.is_cancelled and self.timer_service and platform in ("kick", "twitch"):
            self.timer_service.increment_chat_lines()

    def _step_spam(self, dto: ChatMessageDTO) -> None:
        platform = getattr(dto, "platform", "kick")
        if platform not in ("kick", "twitch"):
            return
        emotes_tag = getattr(dto, "emotes_tag", "")
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
            self.widget_plugin_triggered.emit(plugin_tag, dto.user, dto.content, prefix, platform)

    def _handle_plugin_tts(self, dto: ChatMessageDTO, prefix: str) -> None:
        msg_content = dto.content[len(prefix):].strip()
        if not msg_content:
            return
        settings = self._tts_settings_cache
        if not self.voice_handler.is_role_enabled(dto.badges, settings):
            return
        emotes_tag = getattr(dto, "emotes_tag", "")
        cleaned = self.filter_handler.clean_message_for_tts(msg_content, emotes_tag=emotes_tag)
        if cleaned:
            text = self.i18n.get("chat.status.user_says").replace("{user}", dto.user).replace("{message}", cleaned) if settings.get("read_name", True) else cleaned
            voice_id = self.voice_handler.resolve_voice_for_badges(dto.badges, settings)
            self.service.speak(text, voice_id=voice_id)

    def _handle_plugin_systts(self, dto: ChatMessageDTO, prefix: str) -> None:
        msg_content = dto.content[len(prefix):].strip()
        platform = getattr(dto, "platform", "kick")
        self._handle_systts_command(dto.user, msg_content, platform=platform)

    def _handle_systts_command(self, user: str, arg: str, platform: str = "kick") -> None:
        arg_clean = arg.strip().lower()
        if arg_clean in _SYSTTS_ON_KEYWORDS:
            new_state = True
        elif arg_clean in _SYSTTS_OFF_KEYWORDS:
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
        self.service.set_tts_enabled(new_state)
        self._tts_settings_cache["enabled"] = new_state
        self.tts_state_changed.emit(new_state)

        if self.view is not None:
            self.view.blockSignals(True)
            self.view.tts_enabled = new_state
            self.view.blockSignals(False)

        resp_template = self.i18n.get("chat.status.systts_on") if new_state else self.i18n.get("chat.status.systts_off")
        resp_msg = resp_template.replace("{user}", user)
        self.command_service.send_response(resp_msg, platform=platform)

    def _resolve_user_role(self, badges: list, user: str) -> str:
        badge_set = set(badges) if badges else set()
        if "broadcaster" in badge_set:
            return self.i18n.get("chat.roles.name_broadcaster")
        if "moderator" in badge_set:
            return self.i18n.get("chat.roles.name_moderator")
        if "vip" in badge_set:
            return self.i18n.get("chat.roles.name_vip")
        if "subscriber" in badge_set:
            return self.i18n.get("chat.roles.name_subscriber")
        if self.filter_handler.is_bot(user, badges):
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

        if not self.voice_handler.is_role_enabled(dto.badges, settings):
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
        if self.view is None:
            return
        settings = {
            "enabled": self.view.tts_enabled,
            "read_name": self.view.read_name_enabled,
            "use_command": self.view.use_command_enabled,
            "command": self.view.tts_command,
            "provider": self.view.tts_provider if hasattr(self.view, "tts_provider") else ("web" if self.view.is_web_provider else "piper"),
            "volume": self.view.tts_volume,
            "speed": self.view.tts_speed if hasattr(self.view, "tts_speed") else 100,
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
        logger.info("[User Action] Saved Chat/TTS settings: enabled=%s, read_name=%s, use_cmd=%s, cmd='%s', provider='%s'",
                    settings.get("enabled"), settings.get("read_name"), settings.get("use_command"), settings.get("command"), settings.get("provider"))
        self._tts_settings_cache = dict(settings)
        self.tts_state_changed.emit(settings["enabled"])
        self._save_timer.start()

        new_tts_state = settings["enabled"]
        if self._tts_enabled != new_tts_state:
            self._tts_enabled = new_tts_state
            self._notify_setting_change("chat.status.tts_title", "chat.status.tts_active", "chat.status.tts_muted", new_tts_state, "tts_enabled")

        new_read_name_state = settings["read_name"]
        if self._read_name_enabled != new_read_name_state:
            self._read_name_enabled = new_read_name_state
            self._notify_setting_change("chat.status.read_name_title", "chat.status.read_name_active", "chat.status.read_name_inactive", new_read_name_state, "tts_read_name")

        new_use_cmd_state = settings["use_command"]
        if self._use_command_enabled != new_use_cmd_state:
            self._use_command_enabled = new_use_cmd_state
            self._notify_setting_change("chat.status.use_command_title", "chat.status.use_command_active", "chat.status.use_command_inactive", new_use_cmd_state, "tts_use_command")

    def _notify_setting_change(self, title_key: str, active_key: str, inactive_key: str, is_active: bool, tag: str) -> None:
        if not self.toast:
            return
        title = self.i18n.get(title_key)
        msg = self.i18n.get(active_key) if is_active else self.i18n.get(inactive_key)
        color = "success" if is_active else "warning"
        self.toast.show_toast(title=title, message=msg, state=color, tag=tag)

    def _flush_settings_save(self) -> None:
        if not self._tts_settings_cache:
            return
        settings = dict(self._tts_settings_cache)
        self.service.save_settings(settings)

        commands = self.command_service.get_all_commands()
        existing = _find_command_by_response(commands, "[PLUGIN_CHAT_TTS]")
        target_trigger = settings.get("command", "!tts").strip()
        target_use_cmd = settings.get("use_command", False)
        
        cmd_needs_update = False
        if existing:
            if existing.get("trigger") != target_trigger or existing.get("is_active") != target_use_cmd:
                cmd_needs_update = True
        else:
            cmd_needs_update = True

        if cmd_needs_update:
            self.command_service.blockSignals(True)
            try:
                if existing:
                    if existing["trigger"] != target_trigger:
                        self.command_service.delete_command(existing["trigger"])
                    self.command_service.save_command(
                        trigger=target_trigger,
                        response="[PLUGIN_CHAT_TTS]",
                        is_active=target_use_cmd,
                        cooldown=existing.get("cooldown", 1),
                        aliases=existing.get("aliases", ""),
                        is_regex=existing.get("is_regex", False),
                        permission=existing.get("permission", "everyone"),
                        apply_kick=existing.get("apply_kick", True),
                        apply_twitch=existing.get("apply_twitch", True),
                        apply_youtube=existing.get("apply_youtube", True),
                        apply_tiktok=existing.get("apply_tiktok", True)
                    )
                else:
                    self.command_service.save_command(
                        trigger=target_trigger,
                        response="[PLUGIN_CHAT_TTS]",
                        is_active=target_use_cmd,
                        cooldown=1,
                        aliases="",
                        is_regex=False,
                        permission="everyone",
                        apply_kick=True,
                        apply_twitch=True,
                        apply_youtube=True,
                        apply_tiktok=True
                    )

                existing_systts = _find_command_by_response(commands, "[PLUGIN_CHAT_SYSTTS]")
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

            QTimer.singleShot(0, self.command_service.commands_changed.emit)

    def _sync_tts_command_from_db(self) -> None:
        commands = self.command_service.get_all_commands()
        tts_cmd = _find_command_by_response(commands, "[PLUGIN_CHAT_TTS]")
        
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
        logger.info("[User Action] Added bot to muted list: '%s'", bot_name)
        self.filter_handler.add_bot(bot_name, self.view)
        self.view.clear_bot_input()

    @Slot(str)
    def _remove_bot(self, bot_name: str) -> None:
        logger.info("[User Action] Removed bot from muted list: '%s'", bot_name)
        self.filter_handler.remove_bot(bot_name)

    @Slot(str)
    def _add_word(self, word: str) -> None:
        logger.info("[User Action] Added banned word: '%s'", word)
        self.filter_handler.add_word(word, self.view)
        self.view.clear_word_input()

    @Slot(str)
    def _remove_word(self, word: str) -> None:
        logger.info("[User Action] Removed banned word: '%s'", word)
        self.filter_handler.remove_word(word)
