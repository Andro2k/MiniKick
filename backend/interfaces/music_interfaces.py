# backend\interfaces\music_interfaces.py

from typing import Protocol

class MusicPlayerProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def get_current_song(self) -> dict | None: ...

    def add_to_queue(self, query_or_uri: str, callback=None, requester: str = None) -> tuple[bool, str]: ...

    def skip_current(self) -> bool: ...

    def set_volume(self, volume: int) -> None: ...

    def get_queue(self) -> list[dict]:
        return []

    def remove_from_queue(self, index: int) -> bool:
        return False

    def pause_playback(self) -> bool:
        return False

    def resume_playback(self) -> bool:
        return False