# backend/handlers/music_command_handler.py

import logging
import time

logger = logging.getLogger("minikick.handlers.music_command")

class MusicCommandHandler:
    def __init__(self, controller):
        self.controller = controller

    @property
    def i18n(self):
        return self.controller.i18n

    def _require_active_provider(self, api, provider) -> bool:
        if provider:
            return True
        api.post_chat_message(self.i18n.get("music.chat.not_linked_youtube"))
        return False

    def handle_command(self, tag: str, user: str, message: str, prefix_used: str):
        api = getattr(self.controller.command_service, "api_client", None)
        if not api:
            return

        if not getattr(self.controller, "music_service_enabled", True):
            msg = self.i18n.get("music.stats.service_disabled_chat").replace("{user}", user)
            api.post_chat_message(msg)
            return

        provider = self.controller.music_provider
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
                    msg = (
                        self.i18n.get("music.chat.playlist_pos_info")
                        .replace("{pos}", str(pos))
                        .replace("{title}", title)
                        .replace("{artist}", artist_str)
                        .replace("{requester}", requester)
                    )
                    api.post_chat_message(msg)
                    return
                else:
                    msg = (
                        self.i18n.get("music.chat.playlist_invalid_pos")
                        .replace("{user}", user)
                        .replace("{pos}", str(pos))
                        .replace("{total}", str(total))
                    )
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
            first_msg = (
                self.i18n.get("music.chat.playlist_user_songs")
                .replace("{user}", user)
                .replace("{count}", str(count))
                .replace("{songs}", first_chunk_str)
            )
            api.post_chat_message(first_msg)

            total_pages = len(chunks)
            for page_idx, chunk in enumerate(chunks[1:], start=2):
                remaining_str = ", ".join(chunk)
                extra_msg = (
                    self.i18n.get("music.chat.playlist_user_songs_more")
                    .replace("{user}", user)
                    .replace("{page}", str(page_idx))
                    .replace("{total_pages}", str(total_pages))
                    .replace("{songs}", remaining_str)
                )
                api.post_chat_message(extra_msg)

    def _handle_plugin_sr(self, api, provider, user, message, prefix_used):
        query = message[len(prefix_used):].strip() if prefix_used else ""
        if not query:
            msg = self.i18n.get("music.chat.sr_usage").replace("{user}", user).replace("{trigger}", prefix_used)
            api.post_chat_message(msg)
            return

        if not self._require_active_provider(api, provider):
            return

        user_lower = user.lower()
        now = time.time()

        queue_items = provider.get_queue() if provider and hasattr(provider, "get_queue") else []
        if len(queue_items) >= self.controller.max_queue_size:
            msg = self.i18n.get("music.chat.queue_full").replace("{user}", user).replace("{max}", str(self.controller.max_queue_size))
            api.post_chat_message(msg)
            return

        last_time = self.controller._user_last_request_time.get(user_lower, 0.0)
        elapsed = now - last_time
        if elapsed < self.controller.user_cooldown:
            remaining = int(self.controller.user_cooldown - elapsed) + 1
            msg = self.i18n.get("music.chat.cooldown_active").replace("{user}", user).replace("{seconds}", str(remaining))
            api.post_chat_message(msg)
            return

        user_active_count = sum(1 for song in queue_items if (song.get("requester") or "").lower() == user_lower)
        current_song = provider.get_current_song() if provider else None
        if current_song and (current_song.get("requester") or "").lower() == user_lower:
            user_active_count += 1

        if user_active_count >= self.controller.max_user_songs:
            msg = (
                self.i18n.get("music.chat.user_limit_reached")
                .replace("{user}", user)
                .replace("{count}", str(user_active_count))
                .replace("{max}", str(self.controller.max_user_songs))
            )
            api.post_chat_message(msg)
            return

        self.controller._user_last_request_time[user_lower] = now

        def on_complete(success, reply_msg):
            api.post_chat_message(reply_msg)

        success, immediate_reply = provider.add_to_queue(
            query,
            callback=on_complete,
            requester=user,
            max_duration_min=self.controller.max_song_duration
        )
        if immediate_reply:
            api.post_chat_message(immediate_reply)

    def _handle_plugin_skip(self, api, provider, user, message, prefix_used):
        if self._require_active_provider(api, provider):
            if provider.skip_current():
                api.post_chat_message(self.i18n.get("music.chat.skip_success"))
            else:
                api.post_chat_message(self.i18n.get("music.chat.skip_failed"))

    def _handle_plugin_song(self, api, provider, user, message, prefix_used):
        if self._require_active_provider(api, provider):
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
        if self._require_active_provider(api, provider):
            if hasattr(provider, "pause_playback") and provider.pause_playback():
                api.post_chat_message(self.i18n.get("music.chat.pause_success"))
                self.controller._poll_now_playing()
            else:
                api.post_chat_message(self.i18n.get("music.chat.pause_failed"))

    def _handle_plugin_resume(self, api, provider, user, message, prefix_used):
        if self._require_active_provider(api, provider):
            if hasattr(provider, "resume_playback") and provider.resume_playback():
                api.post_chat_message(self.i18n.get("music.chat.resume_success"))
                self.controller._poll_now_playing()
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

        self.controller.set_volume(vol_val)
        if hasattr(self.controller.view, "slider_vol"):
            self.controller.view.blockSignals(True)
            self.controller.view.slider_vol.setValue(vol_val)
            self.controller.view.lbl_vol_perc.setText(f"{vol_val}%")
            self.controller.view.blockSignals(False)

        msg = self.i18n.get("music.chat.vol_success").replace("{user}", user).replace("{volume}", str(vol_val))
        api.post_chat_message(msg)
