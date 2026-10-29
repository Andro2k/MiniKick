# backend\interfaces\i_music_chat_context.py

from typing import Any, Protocol

from backend.interfaces.i_music_provider import IMusicProvider


class IMusicChatContext(Protocol):
    i18n: Any
    music_provider: IMusicProvider | None
    music_service_enabled: bool
    max_queue_size: int
    user_cooldown: int
    max_user_songs: int
    max_song_duration: int
    current_volume: int

    def send_chat_message(self, message: str, platform: str = "kick") -> None: ...

    def refresh_now_playing(self) -> None: ...

    def apply_chat_volume(self, volume: int) -> None: ...
