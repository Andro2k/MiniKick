# backend\controllers\music_controller.py

import time
from PySide6.QtCore import QObject, Slot, QTimer, Signal

from backend.interfaces import IMusicProvider

class MusicController(QObject):
    song_changed = Signal(dict)

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

        self.max_user_songs = 2
        self.user_cooldown = 30
        self.max_queue_size = 30
        self.max_song_duration = 10

        self.polling_timer = QTimer(self)
        self.polling_timer.setInterval(5000)
        self.polling_timer.timeout.connect(self._poll_now_playing)
        self.command_service.commands_changed.connect(self._sync_switches_from_db)
        if self.view is not None:
            self._connect_signals()
            self._load_initial_state()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self._load_initial_state()

    def _connect_signals(self):
        self.view.command_toggled.connect(self.handle_command_toggle)
        self.view.volume_changed.connect(self.set_volume)
        self.view.remove_queue_item_requested.connect(self.handle_remove_queue_item)
        self.command_service.commands_changed.connect(self._sync_switches_from_db)
        self.view.play_pause_requested.connect(self.handle_play_pause)
        self.view.skip_requested.connect(self.handle_skip)
        self.view.youtube_auto_resume_toggled.connect(self.handle_youtube_auto_resume_toggle)
        self.view.service_toggled.connect(self.handle_service_toggle)
        self.view.move_queue_item_requested.connect(self.handle_move_queue_item)
        self.view.view_shown.connect(self._poll_now_playing)

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
        if not any(c for c in commands if c["response"] == "[PLUGIN_MUSIC_PAUSE]"):
            self.command_service.save_command(
                trigger="!pause",
                response="[PLUGIN_MUSIC_PAUSE]",
                is_active=True,
                cooldown=3,
                aliases="",
                is_regex=False,
                permission="moderator"
            )
        if not any(c for c in commands if c["response"] == "[PLUGIN_MUSIC_RESUME]"):
            self.command_service.save_command(
                trigger="!resume",
                response="[PLUGIN_MUSIC_RESUME]",
                is_active=True,
                cooldown=3,
                aliases="!play",
                is_regex=False,
                permission="moderator"
            )
        if not any(c for c in commands if c["response"] == "[PLUGIN_MUSIC_PLAYLIST]"):
            self.command_service.save_command(
                trigger="!playlist",
                response="[PLUGIN_MUSIC_PLAYLIST]",
                is_active=True,
                cooldown=5,
                aliases="!queue,!pl",
                is_regex=False,
                permission="everyone"
            )
        if not any(c for c in commands if c["response"] == "[PLUGIN_MUSIC_VOLUME]"):
            self.command_service.save_command(
                trigger="!vol",
                response="[PLUGIN_MUSIC_VOLUME]",
                is_active=True,
                cooldown=3,
                aliases="!volume",
                is_regex=False,
                permission="moderator"
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

            self.view.blockSignals(True)
            self.view.sw_auto_resume.setChecked(auto_resume)
            self.view.set_service_state(self.music_service_enabled)
            if hasattr(self.view, "set_rate_limit_values"):
                self.view.set_rate_limit_values(
                    self.max_user_songs,
                    self.user_cooldown,
                    self.max_queue_size,
                    self.max_song_duration
                )
            self.view.blockSignals(False)

        self._init_youtube_provider()

    @Slot(bool)
    def handle_service_toggle(self, enabled: bool):
        self.music_service_enabled = enabled
        if self.settings_storage:
            self.settings_storage.save_bool("music_service_enabled", enabled)
        
        status_title = self.i18n.get("music.stats.cmd_title")
        status_msg = self.i18n.get("music.stats.service_active") if enabled else self.i18n.get("music.stats.service_disabled")
        state_color = "success" if enabled else "warning"
        if self.toast:
            self.toast.show_toast(status_title, status_msg, state_color)

    def _init_youtube_provider(self):
        if not self.music_provider:
            db_mgr = self.settings_storage.db_manager if self.settings_storage else None
            self.music_provider = self.provider_factory["youtube"](db_mgr)
        self.music_provider.resolve_error_occurred.connect(self.handle_resolve_error)
        
        vol = 100
        if self.settings_storage:
            try:
                vol = int(self.settings_storage.load_string("music_volume", "100"))
            except ValueError:
                vol = 100
        self.music_provider.set_volume(vol)
        
        self.view.slider_vol.blockSignals(True)
        self.view.slider_vol.setValue(vol)
        self.view.slider_vol.blockSignals(False)
        self.view.lbl_vol_perc.setText(f"{vol}%")
        self.view.set_auth_state(connected=True, label_key="music.status.youtube_active")
        self.polling_timer.start()
        self._poll_now_playing()

    def set_volume(self, volume: int):
        if self.music_provider:
            self.music_provider.set_volume(volume)
        if self.settings_storage:
            self.settings_storage.save_string("music_volume", str(volume))

    def set_max_user_songs(self, val: int):
        self.max_user_songs = max(1, min(10, val))
        if self.settings_storage:
            self.settings_storage.save_string("youtube_max_user_songs", str(self.max_user_songs))

    def set_user_cooldown(self, val: int):
        self.user_cooldown = max(0, min(300, val))
        if self.settings_storage:
            self.settings_storage.save_string("youtube_user_cooldown", str(self.user_cooldown))

    def set_max_queue_size(self, val: int):
        self.max_queue_size = max(5, min(100, val))
        if self.settings_storage:
            self.settings_storage.save_string("youtube_max_queue_size", str(self.max_queue_size))

    def set_max_song_duration(self, val: int):
        self.max_song_duration = max(1, min(30, val))
        if self.settings_storage:
            self.settings_storage.save_string("youtube_max_song_duration", str(self.max_song_duration))

    @Slot()
    def _poll_now_playing(self):
        if not self.music_provider:
            return
        song = self.music_provider.get_current_song()
        if self.view.isVisible():
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
        if self.music_provider and hasattr(self.music_provider, "remove_from_queue"):
            success = self.music_provider.remove_from_queue(index)
            if success:
                self._poll_now_playing()
                msg = self.i18n.get("music.toast.removed_from_queue")
                self.toast.show_toast("YouTube", msg, "success")

    @Slot(int, int)
    def handle_move_queue_item(self, from_index: int, to_index: int):
        if self.music_provider and hasattr(self.music_provider, "move_in_queue"):
            success = self.music_provider.move_in_queue(from_index, to_index)
            if success:
                self._poll_now_playing()
                msg = self.i18n.get("music.toast.moved_in_queue")
                self.toast.show_toast("YouTube", msg, "info")

    @Slot(str, bool)
    def handle_command_toggle(self, trigger: str, is_active: bool):
        plugin_tags = {
            "!sr": "[PLUGIN_MUSIC_SR]",
            "!skip": "[PLUGIN_MUSIC_SKIP]",
            "!song": "[PLUGIN_MUSIC_SONG]",
            "!pause": "[PLUGIN_MUSIC_PAUSE]",
            "!resume": "[PLUGIN_MUSIC_RESUME]",
            "!playlist": "[PLUGIN_MUSIC_PLAYLIST]",
            "!vol": "[PLUGIN_MUSIC_VOLUME]"
        }
        all_cmds = self.command_service.get_all_commands()
        existing = next((c for c in all_cmds if c["trigger"] == trigger), None)

        cooldown = existing["cooldown"] if existing else 5
        aliases = existing["aliases"] if existing else ("!queue,!pl" if trigger == "!playlist" else ("!volume" if trigger == "!vol" else ""))
        is_regex = existing["is_regex"] if existing else False
        permission = existing["permission"] if existing else ("everyone" if trigger in ("!sr", "!song", "!playlist") else "moderator")

        self.command_service.save_command(
            trigger=trigger,
            response=plugin_tags.get(trigger, "[PLUGIN_MUSIC_SR]"),
            is_active=is_active,
            cooldown=cooldown,
            aliases=aliases,
            is_regex=is_regex,
            permission=permission
        )

        status_title = self.i18n.get("command.status.enabled") if is_active else self.i18n.get("command.status.disabled")
        status_msg = self.i18n.get("command.status.toggled_msg").replace("{trigger}", trigger)
        state_color = "success" if is_active else "warning"
        self.toast.show_toast(status_title, status_msg, state_color)

    def shutdown(self):
        self.polling_timer.stop()
        if self.music_provider and hasattr(self.music_provider, "shutdown"):
            self.music_provider.shutdown()

    def handle_resolve_error(self, title: str, error_msg: str, requester: str = ""):
        if self.toast:
            clean_msg = error_msg
            if "Sign in to confirm your age" in error_msg:
                clean_msg = self.i18n.get("music.youtube.age_restricted")
            elif "inappropriate for some users" in error_msg:
                clean_msg = self.i18n.get("music.youtube.inappropriate")
            elif "Sign in to confirm you’re not a bot" in error_msg or "confirm you're not a bot" in error_msg:
                clean_msg = self.i18n.get("music.youtube.bot_blocked")
            elif "INVALID_MEDIA" in error_msg or "Formato o medio inválido" in error_msg or "Invalid media" in error_msg:
                clean_msg = self.i18n.get("music.youtube.invalid_media")
            elif any(k in error_msg for k in ("DPAPI", "AppData", ":\\", ":/")) or "ERROR:" in error_msg:
                clean_msg = self.i18n.get("music.youtube.generic_error")
            else:
                display_err = error_msg.replace("PLAYER_ERROR: ", "")
                first_line = display_err.split('\n')[0]
                if len(first_line) > 80 or any(c in first_line for c in ('\\', '/', ':', 'AppData', 'http', 'ERROR')):
                    clean_msg = self.i18n.get("music.youtube.generic_error")
                else:
                    clean_msg = first_line

            title_toast = self.i18n.get("music.youtube.error_title")
            msg_toast = self.i18n.get("music.toast.error_playing").replace("{title}", title).replace("{error}", clean_msg)
                
            self.toast.show_toast(
                title_toast,
                msg_toast,
                "danger"
            )

            api_client = getattr(self.command_service, 'api_client', None)
            if api_client:
                if requester:
                    chat_text = self.i18n.get("music.toast.chat_error_playing").replace("{user}", requester).replace("{title}", title).replace("{error}", clean_msg)
                else:
                    chat_text = self.i18n.get("music.toast.chat_error_playing_no_user").replace("{title}", title).replace("{error}", clean_msg)
                api_client.post_chat_message(content=chat_text, msg_type="bot")

    @Slot()
    def handle_play_pause(self):
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
        if self.music_provider:
            self.music_provider.skip_current()
            self._poll_now_playing()

    @Slot(bool)
    def handle_youtube_auto_resume_toggle(self, enabled: bool):
        if self.settings_storage:
            self.settings_storage.save_bool("youtube_auto_resume", enabled)
            
        if self.music_provider:
            self.music_provider.auto_resume = enabled

    def _require_active_provider(self, api) -> bool:
        if self.music_provider:
            return True
        api.post_chat_message(self.i18n.get("music.chat.not_linked_youtube"))
        return False

    @Slot(str, str, str, str)
    def handle_music_plugin_command(self, tag: str, user: str, message: str, prefix_used: str):
        api = getattr(self.command_service, 'api_client', None)
        if not api:
            return
        
        if not getattr(self, "music_service_enabled", True):
            msg = self.i18n.get("music.stats.service_disabled_chat").replace("{user}", user)
            api.post_chat_message(msg)
            return

        provider = self.music_provider
        dispatch_table = {
            "[PLUGIN_MUSIC_SR]": self._handle_plugin_sr,
            "[PLUGIN_MUSIC_SKIP]": self._handle_plugin_skip,
            "[PLUGIN_MUSIC_SONG]": self._handle_plugin_song,
            "[PLUGIN_MUSIC_PAUSE]": self._handle_plugin_pause,
            "[PLUGIN_MUSIC_RESUME]": self._handle_plugin_resume,
            "[PLUGIN_MUSIC_PLAYLIST]": self._handle_plugin_playlist,
            "[PLUGIN_MUSIC_VOLUME]": self._handle_plugin_volume,
        }
        
        executor = dispatch_table.get(tag)
        if executor:
            executor(api, provider, user, message, prefix_used)

    def _handle_plugin_playlist(self, api, provider, user, message, prefix_used):
        if not provider or not hasattr(provider, "get_queue"):
            msg = self.i18n.get("music.chat.no_queue_available").replace("{user}", user)
            api.post_chat_message(msg)
            return

        queue_items = provider.get_queue()
        query = message[len(prefix_used):].strip() if prefix_used else ""

        if query:
            clean_query = query.lstrip("#").strip()
            if clean_query.isdigit():
                pos = int(clean_query)
                total = len(queue_items)
                if 1 <= pos <= total:
                    song = queue_items[pos - 1]
                    title = song.get("title", self.i18n.get("music.player.unknown_song"))
                    artist = song.get("artist", "")
                    artist_str = f" - {artist}" if artist else ""
                    requester = song.get("requester", "Streamer")
                    msg = self.i18n.get("music.chat.playlist_pos_info")\
                        .replace("{pos}", str(pos))\
                        .replace("{title}", title)\
                        .replace("{artist}", artist_str)\
                        .replace("{requester}", requester)
                    api.post_chat_message(msg)
                    return
                else:
                    msg = self.i18n.get("music.chat.playlist_invalid_pos")\
                        .replace("{user}", user)\
                        .replace("{pos}", str(pos))\
                        .replace("{total}", str(total))
                    api.post_chat_message(msg)
                    return

        user_lower = user.lower()
        user_positions = []
        for idx, song in enumerate(queue_items):
            req = song.get("requester", "")
            if req and req.lower() == user_lower:
                user_positions.append(f"#{idx + 1}")

        if not user_positions:
            msg = self.i18n.get("music.chat.playlist_empty_for_user").replace("{user}", user)
            api.post_chat_message(msg)
        else:
            MAX_PER_MSG = 8
            count = len(user_positions)
            chunks = [user_positions[i:i + MAX_PER_MSG] for i in range(0, count, MAX_PER_MSG)]
            
            first_chunk_str = ", ".join(chunks[0])
            first_msg = self.i18n.get("music.chat.playlist_user_songs")\
                .replace("{user}", user)\
                .replace("{count}", str(count))\
                .replace("{songs}", first_chunk_str)
            api.post_chat_message(first_msg)

            total_pages = len(chunks)
            for page_idx, chunk in enumerate(chunks[1:], start=2):
                remaining_str = ", ".join(chunk)
                extra_msg = self.i18n.get("music.chat.playlist_user_songs_more")\
                    .replace("{user}", user)\
                    .replace("{page}", str(page_idx))\
                    .replace("{total_pages}", str(total_pages))\
                    .replace("{songs}", remaining_str)
                api.post_chat_message(extra_msg)

    def _handle_plugin_sr(self, api, provider, user, message, prefix_used):
        query = message[len(prefix_used):].strip() if prefix_used else ""
        if not query:
            msg = self.i18n.get("music.chat.sr_usage").replace("{user}", user).replace("{trigger}", prefix_used)
            api.post_chat_message(msg)
            return

        if not self._require_active_provider(api):
            return

        user_lower = user.lower()
        now = time.time()

        queue_items = provider.get_queue() if provider and hasattr(provider, "get_queue") else []
        if len(queue_items) >= self.max_queue_size:
            msg = self.i18n.get("music.chat.queue_full").replace("{user}", user).replace("{max}", str(self.max_queue_size))
            api.post_chat_message(msg)
            return

        last_time = self._user_last_request_time.get(user_lower, 0.0)
        elapsed = now - last_time
        if elapsed < self.user_cooldown:
            remaining = int(self.user_cooldown - elapsed) + 1
            msg = self.i18n.get("music.chat.cooldown_active").replace("{user}", user).replace("{seconds}", str(remaining))
            api.post_chat_message(msg)
            return

        user_active_count = sum(1 for song in queue_items if (song.get("requester") or "").lower() == user_lower)
        current_song = provider.get_current_song() if provider else None
        if current_song and (current_song.get("requester") or "").lower() == user_lower:
            user_active_count += 1

        if user_active_count >= self.max_user_songs:
            msg = self.i18n.get("music.chat.user_limit_reached").replace("{user}", user).replace("{count}", str(user_active_count)).replace("{max}", str(self.max_user_songs))
            api.post_chat_message(msg)
            return

        self._user_last_request_time[user_lower] = now

        def on_complete(success, reply_msg):
            api.post_chat_message(reply_msg)
            
        success, immediate_reply = provider.add_to_queue(
            query,
            callback=on_complete,
            requester=user,
            max_duration_min=self.max_song_duration
        )
        if immediate_reply:
            api.post_chat_message(immediate_reply)

    def _handle_plugin_skip(self, api, provider, user, message, prefix_used):
        if self._require_active_provider(api):
            if provider.skip_current():
                api.post_chat_message(self.i18n.get("music.chat.skip_success"))
            else:
                api.post_chat_message(self.i18n.get("music.chat.skip_failed"))

    def _handle_plugin_song(self, api, provider, user, message, prefix_used):
        if self._require_active_provider(api):
            song = provider.get_current_song()
            if song:
                is_playing = song.get("is_playing", False)
                if is_playing:
                    msg = self.i18n.get("music.chat.song_now_playing").replace("{title}", song["title"]).replace("{artist}", song["artist"])
                    api.post_chat_message(msg)
                else:
                    msg = self.i18n.get("music.chat.song_paused_youtube")
                    api.post_chat_message(msg)
            else:
                msg = self.i18n.get("music.chat.song_empty_youtube")
                api.post_chat_message(msg)

    def _handle_plugin_pause(self, api, provider, user, message, prefix_used):
        if self._require_active_provider(api):
            if hasattr(provider, "pause_playback") and provider.pause_playback():
                api.post_chat_message(self.i18n.get("music.chat.pause_success"))
                self._poll_now_playing()
            else:
                api.post_chat_message(self.i18n.get("music.chat.pause_failed"))

    def _handle_plugin_resume(self, api, provider, user, message, prefix_used):
        if self._require_active_provider(api):
            if hasattr(provider, "resume_playback") and provider.resume_playback():
                api.post_chat_message(self.i18n.get("music.chat.resume_success"))
                self._poll_now_playing()
            else:
                api.post_chat_message(self.i18n.get("music.chat.resume_failed"))

    def _handle_plugin_volume(self, api, provider, user, message, prefix_used):
        query = message[len(prefix_used):].strip() if prefix_used else ""
        if not query:
            msg = self.i18n.get("music.chat.vol_usage").replace("{user}", user).replace("{trigger}", prefix_used)
            api.post_chat_message(msg)
            return

        try:
            vol_val = int(query)
            if not (0 <= vol_val <= 100):
                raise ValueError("Volume out of range")
        except ValueError:
            msg = self.i18n.get("music.chat.vol_usage").replace("{user}", user).replace("{trigger}", prefix_used)
            api.post_chat_message(msg)
            return

        self.set_volume(vol_val)
        if hasattr(self.view, "slider_vol"):
            self.view.blockSignals(True)
            self.view.slider_vol.setValue(vol_val)
            self.view.lbl_vol_perc.setText(f"{vol_val}%")
            self.view.blockSignals(False)

        msg = self.i18n.get("music.chat.vol_success").replace("{user}", user).replace("{volume}", str(vol_val))
        api.post_chat_message(msg)
