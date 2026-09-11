# backend\interfaces\music_provider.py

from typing import Protocol, runtime_checkable

@runtime_checkable
class IMusicProvider(Protocol):
    def is_authenticated(self) -> bool:
        ...

    def get_now_playing(self) -> dict | None:
        ...

    def search_song(self, query: str) -> dict | None:
        ...

    def add_to_queue(self, song: dict) -> bool:
        ...

    def play_pause(self) -> bool:
        ...

    def skip_song(self) -> bool:
        ...

    def set_volume(self, volume: int) -> None:
        ...
