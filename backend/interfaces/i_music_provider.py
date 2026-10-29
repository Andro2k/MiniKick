# backend\interfaces\i_music_provider.py

from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class IMusicProvider(Protocol):
    queue_updated: Any
    resolve_error_occurred: Any
    auto_resume: bool

    def add_to_queue(
        self,
        query_or_uri: str,
        callback: Callable[..., None] | None = None,
        requester: str | None = None,
        platform: str = "kick",
        max_duration_min: int = 10,
    ) -> tuple[bool, str]: ...

    def get_current_song(self) -> dict | None: ...

    def get_queue(self) -> list[dict]: ...

    def remove_from_queue(self, index: int) -> bool: ...

    def move_in_queue(self, from_index: int, to_index: int) -> bool: ...

    def skip_current(self) -> bool: ...

    def pause_playback(self) -> bool: ...

    def resume_playback(self) -> bool: ...

    def seek(self, position_ms: int) -> bool: ...

    def set_volume(self, volume: int) -> None: ...

    def set_ducking(self, ducked: bool) -> None: ...

    def shutdown(self) -> None: ...
