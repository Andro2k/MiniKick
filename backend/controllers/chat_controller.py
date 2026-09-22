# backend\controllers\chat_controller.py

from collections import deque
import datetime
import logging
from PySide6.QtCore import QObject, QTimer, Signal, Slot
from backend.handlers import TTSVoiceHandler, ChatFilterHandler
from backend.services import MessagePipeline, ChatMessageDTO
from backend.services.chat.giphy_service import GiphyService

logger = logging.getLogger("minikick.controllers.chat")

_SYSTTS_ON_KEYWORDS = frozenset({"on", "1", "enable", "activar", "encender"})
_SYSTTS_OFF_KEYWORDS = frozenset({"off", "0", "disable", "desactivar", "apagar"})

_MUTE_REMOVE_KEYWORDS = frozenset({"unmute", "desilenciar", "quitar", "remove", "del", "-"})
_MUTE_REMOVE_ALIASES = frozenset({"!unmutetts", "!desilenciartts", "!ttsunmute"})
_MUTE_ADD_KEYWORDS = frozenset({"add", "mute", "silenciar", "+"})

_BLOCK_REMOVE_KEYWORDS = frozenset({"unblock", "descensurar", "desbloquear", "quitar", "remove", "del", "-"})
_BLOCK_REMOVE_ALIASES = frozenset({"!unblockword", "!descensurartts", "!ttsunblock"})
_BLOCK_ADD_KEYWORDS = frozenset({"add", "block", "censurar", "bloquear", "+"})

def _build_command_response_map(commands: list[dict]) -> dict[str, dict]:
    return {cmd.get("response", ""): cmd for cmd in commands if "response" in cmd}

def _find_command_by_response(commands: list[dict], response_tag: str) -> dict | None:
    for cmd in commands:
        if cmd.get("response") == response_tag:
            return cmd
    return None

def _parse_mute_args(prefix: str, content: str) -> tuple[bool, str]:
    raw_args = content[len(prefix):].strip()
    tokens = raw_args.split() if raw_args else []
    prefix_lower = prefix.strip().lower()

    if prefix_lower in _MUTE_REMOVE_ALIASES:
        return True, (tokens[0].lstrip("@-+") if tokens else "")

    if not tokens:
        return False, ""

    first_token = tokens[0]
    first_token_lower = first_token.lower().lstrip("-+")

    if first_token.lower() in _MUTE_REMOVE_KEYWORDS or (first_token.startswith("-") and first_token_lower):
        if first_token.startswith("-") and first_token_lower:
            return True, first_token_lower.lstrip("@")
        return True, (tokens[1].lstrip("@") if len(tokens) > 1 else "")

    if first_token.lower() in _MUTE_ADD_KEYWORDS or (first_token.startswith("+") and first_token_lower):
        if first_token.startswith("+") and first_token_lower:
            return False, first_token_lower.lstrip("@")
        return False, (tokens[1].lstrip("@") if len(tokens) > 1 else "")

    return False, first_token.lstrip("@")

def _parse_block_args(prefix: str, content: str) -> tuple[bool, str]:
    raw_args = content[len(prefix):].strip()
    tokens = raw_args.split() if raw_args else []
    prefix_lower = prefix.strip().lower()

    if prefix_lower in _BLOCK_REMOVE_ALIASES:
        return True, raw_args.strip().lower()

    if not tokens:
        return False, ""

    first_token = tokens[0]
    first_token_lower = first_token.lower().lstrip("-+")

    if first_token.lower() in _BLOCK_REMOVE_KEYWORDS or (first_token.startswith("-") and first_token_lower):
        if first_token.startswith("-") and first_token_lower:
            return True, " ".join([first_token_lower] + tokens[1:]).strip().lower()
        return True, (" ".join(tokens[1:]).strip().lower() if len(tokens) > 1 else "")

    if first_token.lower() in _BLOCK_ADD_KEYWORDS or (first_token.startswith("+") and first_token_lower):
        if first_token.startswith("+") and first_token_lower:
            return False, " ".join([first_token_lower] + tokens[1:]).strip().lower()
        return False, (" ".join(tokens[1:]).strip().lower() if len(tokens) > 1 else "")

    return False, raw_args.strip().lower()

_DEFAULT_MOD_COMMANDS: dict[str, dict] = {
    "[PLUGIN_CHAT_TTS_MUTE]": {
        "trigger": "!ttsmute",
        "response": "[PLUGIN_CHAT_TTS_MUTE]",
        "cooldown": 2,
        "aliases": "!mutetts,!silenciartts,!unmutetts,!desilenciartts",
        "is_regex": False,
        "permission": "moderator",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
    "[PLUGIN_CHAT_TTS_BLOCK]": {
        "trigger": "!ttsblock",
        "response": "[PLUGIN_CHAT_TTS_BLOCK]",
        "cooldown": 2,
        "aliases": "!blockword,!censurartts,!unblockword,!descensurartts",
        "is_regex": False,
        "permission": "moderator",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
    "[PLUGIN_CHAT_GIF]": {
        "trigger": "!gif",
        "response": "[PLUGIN_CHAT_GIF]",
        "cooldown": 2,
        "aliases": "!giphy",
        "is_regex": False,
        "permission": "everyone",
        "apply_kick": True,
        "apply_twitch": True,
        "apply_youtube": True,
        "apply_tiktok": True,
    },
}

class ChatController(QObject):
    tts_state_changed = Signal(bool)
    spam_blocked = Signal()
    command_executed = Signal()
    message_received = Signal(str, str, str, object, str, str, str)
    music_plugin_triggered = Signal(str, str, str, str, str)
    widget_plugin_triggered = Signal(str, str, str, str, str)
    chat_overlay_config_changed = Signal(dict)

    def __init__(self, view, service, command_service, spam_service, i18n, timer_service=None, toast_manager=None, giphy_service=None):
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
        self.giphy_service = giphy_service or GiphyService()

        self._tts_enabled = True
        self._read_name_enabled = True
        self._use_command_enabled = False
        self._mod_mute_command_enabled = True
        self._mod_block_command_enabled = True
        self._tts_settings_cache: dict = {}
        self.sync_settings_cache()
        self._view_connected: bool = False

        self._exact_plugin_handlers = {
            "[PLUGIN_CHAT_TTS]": self._handle_plugin_tts,
            "[PLUGIN_CHAT_SYSTTS]": self._handle_plugin_systts,
            "[PLUGIN_CHAT_TTS_MUTE]": self._handle_plugin_ttsmute,
            "[PLUGIN_CHAT_TTS_BLOCK]": self._handle_plugin_ttsblock,
            "[PLUGIN_CHAT_GIF]": self._handle_plugin_gif,
        }

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(200)
        self._save_timer.timeout.connect(self._flush_settings_save)

        self.pipeline = MessagePipeline()
        self._build_pipeline()
        self.command_service.response_generated.connect(self._handle_bot_response)
        
        self._init_backend_state()
        if self.view is not None:
            self._connect_signals()
            self._populate_view()

    def attach_view(self, view) -> None:
        first_attach = (self.view is None)
        self.view = view
        if self.voice_handler:
            self.voice_handler.view = view
        if self.view is not None:
            self._connect_signals()
            self._populate_view()
            if first_attach and self._message_buffer:
                for item in self._message_buffer:
                    self.view.append_message(item["user"], item["content"], item["color"], timestamp=item["timestamp"], role=item["role"], platform=item["platform"])

    def cleanup(self) -> None:
        if hasattr(self, "voice_handler") and self.voice_handler:
            self.voice_handler.cleanup()

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
        if not self.view or self._view_connected:
            return
        self._view_connected = True
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
        if hasattr(self.view, "view_shown"):
            self.view.view_shown.connect(self._sync_tts_command_from_db)

    def load_initial_data(self) -> None:
        self._init_backend_state()
        if self.view is not None:
            self._populate_view()

    def _load_initial_data(self) -> None:
        self.load_initial_data()

    def _init_backend_state(self) -> None:
        self.sync_settings_cache()
        settings = self._tts_settings_cache
        provider = settings.get("provider", "piper")
        self.service.set_provider(provider)
        self.filter_handler.initialize_from_settings(settings, self.view)
        self.service.set_volume(settings.get("volume", 100))
        self.service.set_speed(settings.get("speed", 100))
        self._register_system_commands()
        self.voice_handler.load_voices(provider, is_initial=True)

    def _populate_view(self) -> None:
        if self.view is None:
            return
        settings = self._tts_settings_cache
        provider = settings.get("provider", "piper")
        
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
        platform_enabled = {
            "kick": settings.get("platform_kick", True),
            "twitch": settings.get("platform_twitch", True),
            "youtube": settings.get("platform_youtube", True),
            "tiktok": settings.get("platform_tiktok", True),
        }
        
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
            speed=settings.get("speed", 100),
            platform_enabled=platform_enabled,
            mod_mute_command_enabled=settings.get("mod_mute_command_enabled", True),
            mod_block_command_enabled=settings.get("mod_block_command_enabled", True)
        )
        self.filter_handler.initialize_from_settings(settings, self.view)

        overlay_settings = self.service.get_overlay_settings()
        self.view.set_overlay_settings_ui(
            vertical_config=overlay_settings.get("vertical"),
            horizontal_config=overlay_settings.get("horizontal"),
            common_config=overlay_settings.get("common"),
            orientation=overlay_settings.get("orientation", "vertical"),
            theme=overlay_settings.get("vertical", {}).get("theme", "glass"),
            size=overlay_settings.get("vertical", {}).get("size", 14),
            fade=overlay_settings.get("vertical", {}).get("fade", 15),
            flow=overlay_settings.get("vertical", {}).get("flow", "bottom-to-top"),
            anim_in=overlay_settings.get("vertical", {}).get("anim_in", "fade"),
            show_bots=overlay_settings.get("common", {}).get("show_bots", False),
            show_time=overlay_settings.get("common", {}).get("show_time", False),
            big_emotes=overlay_settings.get("common", {}).get("big_emotes", True),
            edge_fade=overlay_settings.get("common", {}).get("edge_fade", True),
            show_gifs=overlay_settings.get("common", {}).get("show_gifs", True),
            hide_commands=overlay_settings.get("common", {}).get("hide_commands", False),
            show_badges=overlay_settings.get("common", {}).get("show_badges", True),
            show_platform=overlay_settings.get("common", {}).get("show_platform", True)
        )

        if self.voice_handler._all_voices:
            self.voice_handler._on_voices_fetched(self.voice_handler._all_voices, provider, is_initial=True)

    def _upsert_system_command(self, cmd_map: dict[str, dict], tag: str, default_cfg: dict, active_override: bool | None = None) -> None:
        existing = cmd_map.get(tag)
        is_active = active_override if active_override is not None else default_cfg.get("is_active", True)
        
        self.command_service.blockSignals(True)
        try:
            if not existing:
                self.command_service.save_command(
                    trigger=default_cfg["trigger"],
                    response=tag,
                    is_active=is_active,
                    cooldown=default_cfg.get("cooldown", 2),
                    aliases=default_cfg.get("aliases", ""),
                    is_regex=default_cfg.get("is_regex", False),
                    permission=default_cfg.get("permission", "everyone"),
                    apply_kick=default_cfg.get("apply_kick", True),
                    apply_twitch=default_cfg.get("apply_twitch", True),
                    apply_youtube=default_cfg.get("apply_youtube", True),
                    apply_tiktok=default_cfg.get("apply_tiktok", True),
                )
            else:
                def_aliases = [a.strip() for a in default_cfg.get("aliases", "").split(",") if a.strip()]
                curr_aliases = [a.strip() for a in existing.get("aliases", "").split(",") if a.strip()]
                if def_aliases and any(na not in curr_aliases for na in def_aliases):
                    merged_aliases = list(dict.fromkeys(curr_aliases + def_aliases))
                    self.command_service.save_command(
                        trigger=existing["trigger"],
                        response=existing["response"],
                        is_active=existing.get("is_active", True),
                        cooldown=existing.get("cooldown", default_cfg.get("cooldown", 2)),
                        aliases=",".join(merged_aliases),
                        is_regex=existing.get("is_regex", False),
                        permission=existing.get("permission", default_cfg.get("permission", "everyone")),
                        apply_kick=existing.get("apply_kick", True),
                        apply_twitch=existing.get("apply_twitch", True),
                        apply_youtube=existing.get("apply_youtube", True),
                        apply_tiktok=existing.get("apply_tiktok", True),
                    )
        finally:
            self.command_service.blockSignals(False)

    def _register_system_commands(self) -> None:
        settings = self._tts_settings_cache
        commands = self.command_service.get_all_commands()
        cmd_map = _build_command_response_map(commands)

        tts_cfg = {
            "trigger": settings.get("command", "!tts"),
            "cooldown": 1,
            "aliases": "",
            "is_regex": False,
            "permission": "everyone"
        }
        self._upsert_system_command(cmd_map, "[PLUGIN_CHAT_TTS]", tts_cfg, active_override=settings.get("use_command", False))

        systts_cfg = {
            "trigger": "!systts",
            "cooldown": 3,
            "aliases": "!ttssys",
            "is_regex": False,
            "permission": "moderator"
        }
        self._upsert_system_command(cmd_map, "[PLUGIN_CHAT_SYSTTS]", systts_cfg, active_override=True)

        self._upsert_system_command(cmd_map, "[PLUGIN_CHAT_TTS_MUTE]", _DEFAULT_MOD_COMMANDS["[PLUGIN_CHAT_TTS_MUTE]"], active_override=settings.get("mod_mute_command_enabled", True))
        self._upsert_system_command(cmd_map, "[PLUGIN_CHAT_TTS_BLOCK]", _DEFAULT_MOD_COMMANDS["[PLUGIN_CHAT_TTS_BLOCK]"], active_override=settings.get("mod_block_command_enabled", True))
        self._upsert_system_command(cmd_map, "[PLUGIN_CHAT_GIF]", _DEFAULT_MOD_COMMANDS["[PLUGIN_CHAT_GIF]"], active_override=True)

        for legacy_tag in ("[PLUGIN_CHAT_TTS_UNMUTE]", "[PLUGIN_CHAT_TTS_UNBLOCK]"):
            legacy_cmd = cmd_map.get(legacy_tag)
            if legacy_cmd:
                try:
                    self.command_service.delete_command(legacy_cmd["trigger"])
                except Exception as ex:
                    logger.warning("[ChatController] Could not remove legacy command %s: %s", legacy_tag, ex)

    def sync_settings_cache(self) -> None:
        self._tts_settings_cache = self.service.get_settings()
        self._tts_enabled = self._tts_settings_cache.get("enabled", True)
        self._read_name_enabled = self._tts_settings_cache.get("read_name", True)
        self._use_command_enabled = self._tts_settings_cache.get("use_command", False)
        self._mod_mute_command_enabled = self._tts_settings_cache.get("mod_mute_command_enabled", True)
        self._mod_block_command_enabled = self._tts_settings_cache.get("mod_block_command_enabled", True)

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
        settings = self._tts_settings_cache
        if not self._tts_enabled or not settings.get("enabled", True):
            return
        platform = getattr(dto, "platform", "kick")
        if not settings.get(f"platform_{platform}", True):
            return
        if self.filter_handler.is_bot(dto.user):
            return

        msg_content = dto.content[len(prefix):].strip()
        if not msg_content:
            return
        if not self.voice_handler.is_role_enabled(dto.badges, settings):
            return
        if self.filter_handler.is_message_banned(msg_content):
            return

        emotes_tag = getattr(dto, "emotes_tag", "")
        gif_url = getattr(dto, "gif_url", "")
        cleaned = self.filter_handler.clean_message_for_tts(msg_content, emotes_tag=emotes_tag, gif_url=gif_url)
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

    def _handle_plugin_ttsmute(self, dto: ChatMessageDTO, prefix: str) -> None:
        platform = getattr(dto, "platform", "kick")
        if not self._mod_mute_command_enabled:
            msg = self.i18n.get("chat.mod_commands.mute_disabled_msg").replace("{user}", dto.user)
            self.command_service.send_response(msg, platform=platform)
            return

        is_remove, target = _parse_mute_args(prefix, dto.content)

        if not target:
            usage_key = "chat.commands.ttsunmute_usage" if is_remove else "chat.commands.ttsmute_usage"
            msg = self.i18n.get(usage_key).replace("{user}", dto.user)
            self.command_service.send_response(msg, platform=platform)
            return

        target_lower = target.lower()

        if is_remove:
            if target_lower not in self.filter_handler.muted_bots:
                msg = self.i18n.get("chat.commands.ttsunmute_not_found").replace("{user}", dto.user).replace("{target}", target)
                self.command_service.send_response(msg, platform=platform)
                return

            self.filter_handler.remove_bot(target)
            if self.view is not None:
                self.view.remove_bot_tag(target)
            msg = self.i18n.get("chat.commands.ttsunmute_success").replace("{user}", dto.user).replace("{target}", target)
            self.command_service.send_response(msg, platform=platform)
        else:
            if target_lower in self.filter_handler.muted_bots:
                msg = self.i18n.get("chat.commands.ttsmute_already").replace("{user}", dto.user).replace("{target}", target)
                self.command_service.send_response(msg, platform=platform)
                return

            self.filter_handler.add_bot(target, self.view)
            msg = self.i18n.get("chat.commands.ttsmute_success").replace("{user}", dto.user).replace("{target}", target)
            self.command_service.send_response(msg, platform=platform)

    def _handle_plugin_ttsunmute(self, dto: ChatMessageDTO, prefix: str = "!ttsunmute") -> None:
        self._handle_plugin_ttsmute(dto, prefix=prefix)

    def _handle_plugin_ttsblock(self, dto: ChatMessageDTO, prefix: str) -> None:
        platform = getattr(dto, "platform", "kick")
        if not self._mod_block_command_enabled:
            msg = self.i18n.get("chat.mod_commands.block_disabled_msg").replace("{user}", dto.user)
            self.command_service.send_response(msg, platform=platform)
            return

        is_remove, word = _parse_block_args(prefix, dto.content)

        if not word:
            usage_key = "chat.commands.ttsunblock_usage" if is_remove else "chat.commands.ttsblock_usage"
            msg = self.i18n.get(usage_key).replace("{user}", dto.user)
            self.command_service.send_response(msg, platform=platform)
            return

        if is_remove:
            if word not in self.filter_handler.banned_words:
                msg = self.i18n.get("chat.commands.ttsunblock_not_found").replace("{user}", dto.user).replace("{word}", word)
                self.command_service.send_response(msg, platform=platform)
                return

            self.filter_handler.remove_word(word)
            if self.view is not None:
                self.view.remove_word_tag(word)
            msg = self.i18n.get("chat.commands.ttsunblock_success").replace("{user}", dto.user).replace("{word}", word)
            self.command_service.send_response(msg, platform=platform)
        else:
            if word in self.filter_handler.banned_words:
                msg = self.i18n.get("chat.commands.ttsblock_already").replace("{user}", dto.user).replace("{word}", word)
                self.command_service.send_response(msg, platform=platform)
                return

            self.filter_handler.add_word(word, self.view)
            msg = self.i18n.get("chat.commands.ttsblock_success").replace("{user}", dto.user).replace("{word}", word)
            self.command_service.send_response(msg, platform=platform)

    def _handle_plugin_ttsunblock(self, dto: ChatMessageDTO, prefix: str = "!ttsunblock") -> None:
        self._handle_plugin_ttsblock(dto, prefix=prefix)

    def _handle_plugin_gif(self, dto: ChatMessageDTO, prefix: str) -> None:
        raw_arg = dto.content[len(prefix):].strip()
        if not raw_arg:
            return
        platform = getattr(dto, "platform", "kick")
        giphy_key = self._tts_settings_cache.get("giphy_api_key", "")
        resolved_url = self.giphy_service.resolve_gif(raw_arg, api_key_override=giphy_key)
        if resolved_url:
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            msg_dto = ChatMessageDTO(
                user=dto.user,
                content="",
                badges=list(dto.badges) if dto.badges else [],
                color=dto.color,
                msg_id=dto.msg_id or "",
                sender_id=dto.sender_id or 0,
                timestamp=dto.timestamp or now_str,
                platform=platform,
                gif_url=resolved_url,
                is_command=False
            )
            self._step_ui_render(msg_dto)
        else:
            if not raw_arg.startswith("http://") and not raw_arg.startswith("https://") and not self.giphy_service.has_active_key(giphy_key):
                warn_msg = self.i18n.get("chat.status.giphy_key_required").replace("{user}", dto.user)
                self.command_service.send_response(warn_msg, platform=platform)

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
        logger.info("[Chat] [%s] [%s] %s: %s", platform.upper(), dto.timestamp, dto.user, dto.content)
        if self.view is not None:
            self.view.append_message(dto.user, dto.content, dto.color, timestamp=dto.timestamp, role=role_name, platform=platform)
        gif_url = getattr(dto, "gif_url", "")
        if not gif_url and dto.content and ("http://" in dto.content or "https://" in dto.content):
            resolved = self.giphy_service.resolve_gif(dto.content.strip())
            if resolved:
                gif_url = resolved
                dto.gif_url = resolved

        emotes_tag = getattr(dto, "emotes_tag", "")
        self.message_received.emit(dto.user, dto.content, dto.color, badges, platform, emotes_tag, gif_url)

    def _handle_bot_response(self, text: str, platform: str = "kick") -> None:
        if not text or platform != "twitch":
            return
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        bot_user = "MiniKick"
        tw_worker = getattr(self.command_service, "twitch_worker", None)
        if tw_worker:
            bot_user = getattr(tw_worker, "bot_nick", "") or getattr(tw_worker, "channel_name", "") or "MiniKick"
        
        dto = ChatMessageDTO(
            user=bot_user, content=text, badges=["broadcaster", "bot"], color="#9146FF",
            msg_id="", sender_id=0, timestamp=now_str, platform="twitch", is_cancelled=False, is_command=False
        )
        self._step_ui_render(dto)

    def _step_tts(self, dto: ChatMessageDTO) -> None:
        if getattr(dto, "is_command", False):
            return
        settings = self._tts_settings_cache
        if not settings.get("enabled", True):
            return
        platform = getattr(dto, "platform", "kick")
        if not settings.get(f"platform_{platform}", True):
            logger.debug("[TTS] Skipped '%s' from %s: Platform '%s' TTS is disabled", dto.content[:30], dto.user, platform)
            return
        if self.filter_handler.is_bot(dto.user):
            logger.debug("[TTS] Skipped '%s' from %s: User is marked as bot/ignored", dto.content[:30], dto.user)
            return

        if not self.voice_handler.is_role_enabled(dto.badges, settings):
            logger.debug("[TTS] Skipped '%s' from %s: Role not enabled for badges %s", dto.content[:30], dto.user, dto.badges)
            return

        if settings.get("use_command", False):
            logger.debug("[TTS] Skipped '%s' from %s: 'use_command' is active (waiting for %s)", dto.content[:30], dto.user, settings.get("command", "!tts"))
            return

        msg = dto.content.strip()
        if not msg:
            return
        if self.filter_handler.is_message_banned(msg):
            logger.debug("[TTS] Skipped '%s' from %s: Message contains banned word", msg[:30], dto.user)
            return

        emotes_tag = getattr(dto, "emotes_tag", "")
        gif_url = getattr(dto, "gif_url", "")
        cleaned = self.filter_handler.clean_message_for_tts(msg, emotes_tag=emotes_tag, gif_url=gif_url)
        if not cleaned:
            logger.debug("[TTS] Skipped '%s' from %s: Cleaned message is empty (only emotes/symbols/gifs)", msg[:30], dto.user)
            return

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
            "banned_words": ",".join(self.filter_handler.banned_words),
            "mod_mute_command_enabled": self.view.mod_mute_command_enabled if hasattr(self.view, "mod_mute_command_enabled") else True,
            "mod_block_command_enabled": self.view.mod_block_command_enabled if hasattr(self.view, "mod_block_command_enabled") else True,
        }
        settings.update(self.view.get_role_voices())
        v_cfg = getattr(self.view, "vertical_config", {})
        h_cfg = getattr(self.view, "horizontal_config", {})
        cur_orientation = getattr(self.view, "overlay_orientation", "vertical")

        settings.update({
            "chat_overlay_orientation": cur_orientation,
            "chat_overlay_vertical_theme": v_cfg.get("theme", "glass"),
            "chat_overlay_vertical_size": str(v_cfg.get("size", 14)),
            "chat_overlay_vertical_fade": str(v_cfg.get("fade", 15)),
            "chat_overlay_vertical_flow": v_cfg.get("flow", "bottom-to-top"),
            "chat_overlay_vertical_anim_in": v_cfg.get("anim_in", "fade"),
            "chat_overlay_horizontal_theme": h_cfg.get("theme", "glass"),
            "chat_overlay_horizontal_size": str(h_cfg.get("size", 14)),
            "chat_overlay_horizontal_fade": str(h_cfg.get("fade", 15)),
            "chat_overlay_horizontal_flow": h_cfg.get("flow", "right-to-left"),
            "chat_overlay_horizontal_anim_in": h_cfg.get("anim_in", "fade"),
            "chat_overlay_theme": self.view.overlay_theme,
            "chat_overlay_size": str(self.view.overlay_size),
            "chat_overlay_fade": str(self.view.overlay_fade),
            "chat_overlay_flow": self.view.overlay_flow,
            "chat_overlay_anim_in": getattr(self.view, "overlay_anim_in", "fade"),
            "chat_overlay_show_bots": self.view.overlay_show_bots,
            "chat_overlay_show_time": self.view.overlay_show_time,
            "chat_overlay_big_emotes": getattr(self.view, "overlay_big_emotes", True),
            "chat_overlay_edge_fade": getattr(self.view, "overlay_edge_fade", True),
            "chat_overlay_show_gifs": getattr(self.view, "overlay_show_gifs", True),
            "chat_overlay_hide_commands": getattr(self.view, "overlay_hide_commands", False),
            "chat_overlay_show_badges": getattr(self.view, "overlay_show_badges", True),
            "chat_overlay_show_platform": getattr(self.view, "overlay_show_platform", True)
        })

        self._tts_settings_cache = dict(settings)
        self._mod_mute_command_enabled = settings["mod_mute_command_enabled"]
        self._mod_block_command_enabled = settings["mod_block_command_enabled"]
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

    def get_active_overlay_config(self) -> dict:
        settings = self._tts_settings_cache
        if not settings or "chat_overlay_orientation" not in settings:
            if hasattr(self.service, "get_overlay_settings"):
                return self.service.get_overlay_settings()
            settings = settings or {}
        cur_orientation = settings.get("chat_overlay_orientation", "vertical")
        v_cfg = {
            "theme": settings.get("chat_overlay_vertical_theme", settings.get("chat_overlay_theme", "glass")),
            "size": str(settings.get("chat_overlay_vertical_size", settings.get("chat_overlay_size", "14"))),
            "fade": str(settings.get("chat_overlay_vertical_fade", settings.get("chat_overlay_fade", "15"))),
            "flow": settings.get("chat_overlay_vertical_flow", "bottom-to-top"),
            "anim_in": settings.get("chat_overlay_vertical_anim_in", settings.get("chat_overlay_anim_in", "fade")),
        }
        h_cfg = {
            "theme": settings.get("chat_overlay_horizontal_theme", settings.get("chat_overlay_theme", "glass")),
            "size": str(settings.get("chat_overlay_horizontal_size", settings.get("chat_overlay_size", "14"))),
            "fade": str(settings.get("chat_overlay_horizontal_fade", settings.get("chat_overlay_fade", "15"))),
            "flow": settings.get("chat_overlay_horizontal_flow", "right-to-left"),
            "anim_in": settings.get("chat_overlay_horizontal_anim_in", settings.get("chat_overlay_anim_in", "fade")),
        }
        common = {
            "show_bots": bool(settings.get("chat_overlay_show_bots", False)),
            "show_time": bool(settings.get("chat_overlay_show_time", False)),
            "show_gifs": bool(settings.get("chat_overlay_show_gifs", True)),
            "big_emotes": bool(settings.get("chat_overlay_big_emotes", True)),
            "edge_fade": bool(settings.get("chat_overlay_edge_fade", True)),
            "hide_commands": bool(settings.get("chat_overlay_hide_commands", False)),
            "show_badges": bool(settings.get("chat_overlay_show_badges", True)),
            "show_platform": bool(settings.get("chat_overlay_show_platform", True)),
        }
        active_sub = v_cfg if cur_orientation == "vertical" else h_cfg
        return {
            "orientation": cur_orientation,
            "vertical": v_cfg,
            "horizontal": h_cfg,
            "common": common,
            "theme": active_sub["theme"],
            "size": active_sub["size"],
            "fade": active_sub["fade"],
            "flow": active_sub["flow"],
            "anim_in": active_sub["anim_in"],
            "show_bots": common["show_bots"],
            "show_time": common["show_time"],
            "show_gifs": common["show_gifs"],
            "big_emotes": common["big_emotes"],
            "edge_fade": common["edge_fade"],
            "hide_commands": common["hide_commands"],
            "show_badges": common["show_badges"],
            "show_platform": common["show_platform"],
        }

    def _flush_settings_save(self) -> None:
        if not self._tts_settings_cache:
            return
        settings = dict(self._tts_settings_cache)
        logger.info("[User Action] Saved Chat/TTS settings: enabled=%s, read_name=%s, use_cmd=%s, cmd='%s', provider='%s'",
                    settings.get("enabled"), settings.get("read_name"), settings.get("use_command"), settings.get("command"), settings.get("provider"))
        self.service.save_settings(settings)
        self.chat_overlay_config_changed.emit(self.get_active_overlay_config())

        commands = self.command_service.get_all_commands()
        cmd_map = _build_command_response_map(commands)
        existing = cmd_map.get("[PLUGIN_CHAT_TTS]")
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

                existing_systts = cmd_map.get("[PLUGIN_CHAT_SYSTTS]")
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

        target_mod_mute = settings.get("mod_mute_command_enabled", True)
        target_mod_block = settings.get("mod_block_command_enabled", True)
        target_show_gifs = settings.get("chat_overlay_show_gifs", True)
        self._sync_command_active_state(cmd_map, "[PLUGIN_CHAT_TTS_MUTE]", target_mod_mute)
        self._sync_command_active_state(cmd_map, "[PLUGIN_CHAT_TTS_BLOCK]", target_mod_block)
        self._sync_command_active_state(cmd_map, "[PLUGIN_CHAT_GIF]", target_show_gifs)

    def _sync_command_active_state(self, cmd_map_or_commands: list[dict] | dict[str, dict], plugin_tag: str, is_active: bool) -> None:
        cmd_map = cmd_map_or_commands if isinstance(cmd_map_or_commands, dict) else _build_command_response_map(cmd_map_or_commands)
        cmd = cmd_map.get(plugin_tag)
        if cmd:
            if cmd.get("is_active") != is_active:
                self.command_service.blockSignals(True)
                try:
                    self.command_service.save_command(
                        trigger=cmd["trigger"],
                        response=cmd["response"],
                        is_active=is_active,
                        cooldown=cmd.get("cooldown", 2),
                        aliases=cmd.get("aliases", ""),
                        is_regex=cmd.get("is_regex", False),
                        permission=cmd.get("permission", "everyone"),
                        apply_kick=cmd.get("apply_kick", True),
                        apply_twitch=cmd.get("apply_twitch", True),
                        apply_youtube=cmd.get("apply_youtube", True),
                        apply_tiktok=cmd.get("apply_tiktok", True)
                    )
                finally:
                    self.command_service.blockSignals(False)

                QTimer.singleShot(0, self.command_service.commands_changed.emit)
        elif is_active:
            def_cmd = _DEFAULT_MOD_COMMANDS.get(plugin_tag)
            if def_cmd:
                self.command_service.blockSignals(True)
                try:
                    self.command_service.save_command(
                        trigger=def_cmd["trigger"],
                        response=def_cmd["response"],
                        is_active=True,
                        cooldown=def_cmd["cooldown"],
                        aliases=def_cmd["aliases"],
                        is_regex=def_cmd["is_regex"],
                        permission=def_cmd["permission"],
                        apply_kick=def_cmd["apply_kick"],
                        apply_twitch=def_cmd["apply_twitch"],
                        apply_youtube=def_cmd["apply_youtube"],
                        apply_tiktok=def_cmd["apply_tiktok"]
                    )
                finally:
                    self.command_service.blockSignals(False)

                QTimer.singleShot(0, self.command_service.commands_changed.emit)

    def _sync_tts_command_from_db(self) -> None:
        commands = self.command_service.get_all_commands()
        cmd_map = _build_command_response_map(commands)
        tts_cmd = cmd_map.get("[PLUGIN_CHAT_TTS]")
        
        settings = self.service.get_settings()
        
        if tts_cmd:
            use_command = tts_cmd["is_active"]
            command_trigger = tts_cmd["trigger"]
        else:
            use_command = False
            command_trigger = settings.get("command", "!tts")
            
        settings_modified = False
        if settings.get("use_command", False) != use_command or settings.get("command", "") != command_trigger:
            settings["use_command"] = use_command
            settings["command"] = command_trigger
            settings_modified = True
            if self.view is not None:
                self.view.set_tts_command_configuration(use_command, command_trigger)

        mute_cmd = cmd_map.get("[PLUGIN_CHAT_TTS_MUTE]")
        block_cmd = cmd_map.get("[PLUGIN_CHAT_TTS_BLOCK]")
        gif_cmd = cmd_map.get("[PLUGIN_CHAT_GIF]")

        mute_active = bool(mute_cmd and mute_cmd.get("is_active", False))
        block_active = bool(block_cmd and block_cmd.get("is_active", False))
        gif_active = bool(gif_cmd and gif_cmd.get("is_active", False))

        if settings.get("mod_mute_command_enabled", True) != mute_active:
            settings["mod_mute_command_enabled"] = mute_active
            settings_modified = True

        if settings.get("mod_block_command_enabled", True) != block_active:
            settings["mod_block_command_enabled"] = block_active
            settings_modified = True

        if settings.get("chat_overlay_show_gifs", True) != gif_active:
            settings["chat_overlay_show_gifs"] = gif_active
            settings_modified = True

        self._mod_mute_command_enabled = mute_active
        self._mod_block_command_enabled = block_active

        if settings_modified:
            self.service.save_settings(settings)
            self._tts_settings_cache = settings

        if self.view is not None:
            if hasattr(self.view, "set_mod_command_toggles"):
                self.view.set_mod_command_toggles(mute_active, block_active)
            elif hasattr(self.view, "bot_panel") and hasattr(self.view.bot_panel, "set_command_toggles"):
                self.view.bot_panel.set_command_toggles(mute_active, block_active)
            if hasattr(self.view, "overlay_show_gifs"):
                self.view.overlay_show_gifs = gif_active

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
