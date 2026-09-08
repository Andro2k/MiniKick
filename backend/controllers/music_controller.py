# backend\controllers\music_controller.py

import logging
from PySide6.QtCore import QObject, Slot, QTimer, Signal
from backend.interfaces import IMusicProvider
from backend.handlers import MusicCommandHandler

logger = logging.getLogger("minikick.controllers.music")

_DEFAULT_MUSIC_COMMANDS: dict[str, tuple[str, int, str, bool, str]] = {
    "!sr": ("[PLUGIN_MUSIC_SR]", 5, "!songrequest", False, "everyone"),
    "!skip": ("[PLUGIN_MUSIC_SKIP]", 3, "!next", False, "moderator"),
    "!song": ("[PLUGIN_MUSIC_SONG]", 3, "!current,!np", False, "everyone"),
    "!pause": ("[PLUGIN_MUSIC_PAUSE]", 3, "", False, "moderator"),
    "!resume": ("[PLUGIN_MUSIC_RESUME]", 3, "!play", False, "moderator"),
    "!playlist": ("[PLUGIN_MUSIC_PLAYLIST]", 5, "!queue,!pl", False, "everyone"),
    "!vol": ("[PLUGIN_MUSIC_VOLUME]", 3, "!volume", False, "moderator"),
}

_MUSIC_PLUGIN_TAGS = {k: v[0] for k, v in _DEFAULT_MUSIC_COMMANDS.items()}

_ERROR_KEYWORD_MAP = (
    ("age", "music.youtube.age_restricted"),
    ("inappropriate", "music.youtube.inappropriate"),
    ("bot", "music.youtube.bot_blocked"),
    ("confirm", "music.youtube.bot_blocked"),
    ("invalid_media", "music.youtube.invalid_media"),
    ("invalid", "music.youtube.invalid_media"),
)

class MusicController(QObject):
    song_changed = Signal(object)
    media_keys_state_changed = Signal(bool)

    def __init__(self, view, command_service, toast_manager, i18n, settings_storage=None, music_storage=None, provider_factory=None, music_provider: IMusicProvider | None = None):
        super().__init__()
        self.view = view
        self.command_service = command_service
        self.toast = toast_manager
        self.i18n = i18n
        self.settings_storage = settings_storage
        self.music_storage = music_storage
        self.provider_factory = provider_factory
        if not self.provider_factory:
            from backend.providers import YouTubeMusicProvider
            self.provider_factory = {
                "youtube": lambda db: YouTubeMusicProvider(self.i18n, music_storage=self.music_storage, db_manager=db)
            }
        self.music_provider = music_provider
        self.provider_type = "youtube"
        self._last_song: dict | None = None
        self.music_service_enabled = True
        self._user_last_request_time: dict[str, float] = {}
        self._provider_connected = False

        self.max_user_songs = 2
        self.user_cooldown = 30
        self.max_queue_size = 30
        self.max_song_duration = 10

        self.command_handler = MusicCommandHandler(self)

        self.polling_timer = QTimer(self)
        self.polling_timer.setInterval(5000)
        self.polling_timer.timeout.connect(self._poll_now_playing)

        self._init_youtube_provider()
        self._load_initial_state()

        if self.view is not None:
            self._connect_signals()

    def load_initial_data(self):
        self._load_initial_state()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self._load_initial_state()
            self._sync_view_state()

    def _connect_signals(self):
        if self.view is None:
            return
        if getattr(self, "_signals_connected", False):
            return
        self._signals_connected = True
        self.view.command_toggled.connect(self.handle_command_toggle)
        self.view.volume_changed.connect(self.set_volume)
        self.view.remove_queue_item_requested.connect(self.handle_remove_queue_item)
        self.command_service.commands_changed.connect(self._sync_switches_from_db)
        self.view.play_pause_requested.connect(self.handle_play_pause)
        self.view.skip_requested.connect(self.handle_skip)
        self.view.youtube_auto_resume_toggled.connect(self.handle_youtube_auto_resume_toggle)
        if hasattr(self.view, "media_keys_toggled"):
            self.view.media_keys_toggled.connect(self.handle_media_keys_toggle)
        self.view.service_toggled.connect(self.handle_service_toggle)
        self.view.move_queue_item_requested.connect(self.handle_move_queue_item)
        self.view.view_shown.connect(self._poll_now_playing)
        self.view.view_shown.connect(self._sync_switches_from_db)

        if hasattr(self.view, "max_user_songs_changed"):
            self.view.max_user_songs_changed.connect(self.set_max_user_songs)
        if hasattr(self.view, "user_cooldown_changed"):
            self.view.user_cooldown_changed.connect(self.set_user_cooldown)
        if hasattr(self.view, "max_queue_size_changed"):
            self.view.max_queue_size_changed.connect(self.set_max_queue_size)
        if hasattr(self.view, "max_song_duration_changed"):
            self.view.max_song_duration_changed.connect(self.set_max_song_duration)

    def _sync_switches_from_db(self):
        if self.view is None:
            return
        saved_cmds = {c["trigger"]: c["is_active"] for c in self.command_service.get_all_commands()}
        if hasattr(self.view, "set_command_switches_states"):
            self.view.set_command_switches_states(saved_cmds)
        else:
            self.view.blockSignals(True)
            self.view.sw_sr.setChecked(saved_cmds.get("!sr", False))
            self.view.sw_skip.setChecked(saved_cmds.get("!skip", False))
            self.view.sw_song.setChecked(saved_cmds.get("!song", False))
            self.view.sw_pause.setChecked(saved_cmds.get("!pause", False))
            self.view.sw_resume.setChecked(saved_cmds.get("!resume", False))
            if hasattr(self.view, "sw_playlist"):
                self.view.sw_playlist.setChecked(saved_cmds.get("!playlist", False))
            if hasattr(self.view, "sw_volume"):
                self.view.sw_volume.setChecked(saved_cmds.get("!vol", False))
            self.view.blockSignals(False)

    def _load_initial_state(self):
        commands = self.command_service.get_all_commands()
        existing_responses = {c.get("response") for c in commands if isinstance(c, dict)}

        for trigger, (response, cooldown, aliases, is_regex, permission) in _DEFAULT_MUSIC_COMMANDS.items():
            if response not in existing_responses:
                self.command_service.save_command(
                    trigger=trigger,
                    response=response,
                    is_active=True,
                    cooldown=cooldown,
                    aliases=aliases,
                    is_regex=is_regex,
                    permission=permission
                )

        self._sync_switches_from_db()

        if self.settings_storage:
            auto_resume = self.settings_storage.load_bool("youtube_auto_resume", True)
            self.music_service_enabled = self.settings_storage.load_bool("music_service_enabled", True)

            try:
                self.max_user_songs = int(self.settings_storage.load_string("youtube_max_user_songs", "2"))
                self.user_cooldown = int(self.settings_storage.load_string("youtube_user_cooldown", "30"))
                self.max_queue_size = int(self.settings_storage.load_string("youtube_max_queue_size", "30"))
                self.max_song_duration = int(self.settings_storage.load_string("youtube_max_song_duration", "10"))
            except Exception:
                pass

            if self.view is not None:
                self.view.blockSignals(True)
                self.view.sw_auto_resume.setChecked(auto_resume)
                if hasattr(self.view, "sw_media_keys"):
                    media_keys = self.settings_storage.load_bool("music_global_media_keys", True)
                    self.view.sw_media_keys.setChecked(media_keys)
                self.view.set_service_state(self.music_service_enabled)
                if hasattr(self.view, "set_rate_limit_values"):
                    self.view.set_rate_limit_values(
                        self.max_user_songs,
                        self.user_cooldown,
                        self.max_queue_size,
                        self.max_song_duration
                    )
                self.view.blockSignals(False)

    def _init_youtube_provider(self):
        if not self.music_provider:
            db_mgr = self.settings_storage.db_manager if self.settings_storage else None
            self.music_provider = self.provider_factory["youtube"](db_mgr)
        if not self._provider_connected:
            self.music_provider.resolve_error_occurred.connect(self.handle_resolve_error)
            if hasattr(self.music_provider, "queue_updated"):
                self.music_provider.queue_updated.connect(self._poll_now_playing)
            self._provider_connected = True

        vol = 100
        if self.settings_storage:
            try:
                vol = int(self.settings_storage.load_string("music_volume", "100"))
            except ValueError:
                vol = 100
        self.music_provider.set_volume(vol)

        if not self.polling_timer.isActive():
            self.polling_timer.start()

        self._sync_view_state()

    def _sync_view_state(self):
        if self.view is None:
            return

        vol = 100
        if self.settings_storage:
            try:
                vol = int(self.settings_storage.load_string("music_volume", "100"))
            except ValueError:
                vol = 100

        self.view.slider_vol.blockSignals(True)
        self.view.slider_vol.setValue(vol)
        self.view.slider_vol.blockSignals(False)
        self.view.lbl_vol_perc.setText(f"{vol}%")
        self.view.set_auth_state(connected=True, label_key="music.status.youtube_active")
        self._poll_now_playing()

    def set_volume(self, volume: int):
        logger.info("[User Action] Changed music player volume: %d%%", volume)
        if self.music_provider:
            self.music_provider.set_volume(volume)
        if self.settings_storage:
            self.settings_storage.save_string("music_volume", str(volume))

    def set_max_user_songs(self, val: int):
        self.max_user_songs = max(1, min(10, val))
        logger.info("[User Action] Changed music max user songs setting: %d", self.max_user_songs)
        if self.settings_storage:
            self.settings_storage.save_string("youtube_max_user_songs", str(self.max_user_songs))

    def set_user_cooldown(self, val: int):
        self.user_cooldown = max(0, min(300, val))
        logger.info("[User Action] Changed music user cooldown setting: %ds", self.user_cooldown)
        if self.settings_storage:
            self.settings_storage.save_string("youtube_user_cooldown", str(self.user_cooldown))

    def set_max_queue_size(self, val: int):
        self.max_queue_size = max(5, min(100, val))
        logger.info("[User Action] Changed music max queue size setting: %d", self.max_queue_size)
        if self.settings_storage:
            self.settings_storage.save_string("youtube_max_queue_size", str(self.max_queue_size))

    def set_max_song_duration(self, val: int):
        self.max_song_duration = max(1, min(30, val))
        logger.info("[User Action] Changed music max song duration setting: %d min", self.max_song_duration)
        if self.settings_storage:
            self.settings_storage.save_string("youtube_max_song_duration", str(self.max_song_duration))

    @Slot()
    def _poll_now_playing(self):
        if not self.music_provider:
            return
        song = self.music_provider.get_current_song()
        if self.view is not None:
            self.view.update_current_song(song)
            if hasattr(self.music_provider, "get_queue"):
                queue_items = self.music_provider.get_queue()
                self.view.update_queue(queue_items)
            else:
                self.view.update_queue([])

        self._maybe_emit_song_change(song)

    def _maybe_emit_song_change(self, song: dict | None):
        current_key = (
            (song.get("title"), song.get("artist"), song.get("is_playing"))
            if song else None
        )
        last_key = (
            (self._last_song.get("title"), self._last_song.get("artist"), self._last_song.get("is_playing"))
            if self._last_song else None
        )
        last_prog = self._last_song.get("progress", 0) if self._last_song else 0
        curr_prog = song.get("progress", 0) if song else 0
        progress_drift = abs(curr_prog - last_prog)

        if current_key != last_key or progress_drift > 5000:
            self._last_song = song
            self.song_changed.emit(song or {})

    @Slot(int)
    def handle_remove_queue_item(self, index: int):
        logger.info("[User Action] Removed song from queue at index %d", index)
        if self.music_provider and hasattr(self.music_provider, "remove_from_queue"):
            success = self.music_provider.remove_from_queue(index)
            if success:
                self._poll_now_playing()
                msg = self.i18n.get("music.toast.removed_from_queue")
                if self.toast:
                    self.toast.show_toast(self.i18n.get("music.header.title"), msg, "success")

    @Slot(int, int)
    def handle_move_queue_item(self, from_index: int, to_index: int):
        logger.info("[User Action] Reordered queue item from index %d to %d", from_index, to_index)
        if self.music_provider and hasattr(self.music_provider, "move_in_queue"):
            success = self.music_provider.move_in_queue(from_index, to_index)
            if success:
                self._poll_now_playing()
                msg = self.i18n.get("music.toast.moved_in_queue")
                if self.toast:
                    self.toast.show_toast(self.i18n.get("music.header.title"), msg, "info")

    @Slot(str, bool)
    def handle_command_toggle(self, trigger: str, is_active: bool):
        logger.info("[User Action] Toggled music command: trigger='%s', is_active=%s", trigger, is_active)
        all_cmds = self.command_service.get_all_commands()
        existing = next((c for c in all_cmds if c["trigger"] == trigger), None)

        tag = _MUSIC_PLUGIN_TAGS.get(trigger)
        if not tag:
            logger.warning("[MusicController] Unknown music command trigger '%s', ignoring toggle", trigger)
            return
        if existing:
            self.command_service.save_command(
                trigger=trigger,
                response=tag,
                is_active=is_active,
                cooldown=existing.get("cooldown", 5),
                aliases=existing.get("aliases", ""),
                is_regex=False,
                permission=existing.get("permission", "everyone"),
                apply_kick=existing.get("apply_kick", True),
                apply_twitch=existing.get("apply_twitch", True),
                apply_youtube=existing.get("apply_youtube", True),
                apply_tiktok=existing.get("apply_tiktok", True)
            )
        else:
            def_meta = _DEFAULT_MUSIC_COMMANDS.get(trigger, (tag, 5, "", False, "everyone"))
            _, def_cd, def_aliases, def_rx, def_perm = def_meta
            self.command_service.save_command(
                trigger=trigger,
                response=tag,
                is_active=is_active,
                cooldown=def_cd,
                aliases=def_aliases,
                is_regex=def_rx,
                permission=def_perm,
                apply_kick=True,
                apply_twitch=True,
                apply_youtube=True,
                apply_tiktok=True
            )

        status_text = self.i18n.get("music.status.enabled") if is_active else self.i18n.get("music.status.disabled")
        status_msg = (self.i18n.get("music.toast.command_toggled")).replace("{trigger}", trigger).replace("{status}", status_text.lower())
        status_title = self.i18n.get("music.status.updated")
        state_color = "success" if is_active else "info"

        if self.toast:
            self.toast.show_toast(status_title, status_msg, state_color)

    def shutdown(self):
        self.polling_timer.stop()
        if self.music_provider and hasattr(self.music_provider, "shutdown"):
            self.music_provider.shutdown()

    def handle_resolve_error(self, title: str, error_msg: str, requester: str = "", platform: str = "kick"):
        clean_msg = self.i18n.get("music.youtube.generic_error")
        err_lower = error_msg.lower()
        for keyword, i18n_key in _ERROR_KEYWORD_MAP:
            if keyword in err_lower:
                clean_msg = self.i18n.get(i18n_key)
                break

        title_toast = self.i18n.get("music.youtube.error_title")
        msg_toast = self.i18n.get("music.toast.error_playing").replace("{title}", title).replace("{error}", clean_msg)

        if self.toast:
            self.toast.show_toast(title_toast, msg_toast, "danger")

        if self.command_service:
            if requester:
                chat_text = self.i18n.get("music.toast.chat_error_playing").replace("{user}", requester).replace("{title}", title).replace("{error}", clean_msg)
            else:
                chat_text = self.i18n.get("music.toast.chat_error_playing_no_user").replace("{title}", title).replace("{error}", clean_msg)
            self.command_service.send_response(chat_text, platform=platform)

    @Slot()
    def handle_play_pause(self):
        logger.info("[User Action] Toggled play/pause")
        if not self.music_provider:
            return

        current = self.music_provider.get_current_song()
        if current and current.get("is_playing", False):
            self.music_provider.pause_playback()
        else:
            self.music_provider.resume_playback()
        self._poll_now_playing()

    @Slot()
    def handle_skip(self):
        logger.info("[User Action] Skipped current song")
        if self.music_provider:
            self.music_provider.skip_current()
            self._poll_now_playing()

    @Slot(bool)
    def handle_youtube_auto_resume_toggle(self, enabled: bool):
        logger.info("[User Action] Toggled YouTube auto-resume: %s", enabled)
        if self.settings_storage:
            self.settings_storage.save_bool("youtube_auto_resume", enabled)

        if self.music_provider:
            self.music_provider.auto_resume = enabled

    @Slot(bool)
    def handle_media_keys_toggle(self, enabled: bool):
        logger.info("[User Action] Toggled global media keys: %s", enabled)
        if self.settings_storage:
            self.settings_storage.save_bool("music_global_media_keys", enabled)
        self.media_keys_state_changed.emit(enabled)

    @Slot(bool)
    def handle_service_toggle(self, enabled: bool):
        logger.info("[User Action] Toggled music service enabled: %s", enabled)
        self.music_service_enabled = enabled
        if self.settings_storage:
            self.settings_storage.save_bool("music_service_enabled", enabled)

        status_title = self.i18n.get("music.stats.cmd_title")
        status_msg = self.i18n.get("music.stats.service_active") if enabled else self.i18n.get("music.stats.service_disabled")
        state_color = "success" if enabled else "warning"
        if self.toast:
            self.toast.show_toast(status_title, status_msg, state_color)

    @Slot(str, str, str, str, str)
    def handle_music_plugin_command(self, tag: str, user: str, message: str, prefix_used: str, platform: str = "kick"):
        self.command_handler.handle_command(tag, user, message, prefix_used, platform=platform)
