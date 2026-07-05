# backend\interfaces\music_interfaces.py

from abc import ABC, abstractmethod

class MusicPlayerProvider(ABC):
    @abstractmethod
    def get_current_song(self) -> dict | None:
        pass

    @abstractmethod
    def add_to_queue(self, query_or_uri: str, callback=None, requester: str = None) -> tuple[bool, str]:
        pass

    @abstractmethod
    def skip_current(self) -> bool:
        pass

    @abstractmethod
    def set_volume(self, volume: int) -> None:
        pass

    def get_queue(self) -> list[dict]:
        return []

    def remove_from_queue(self, index: int) -> bool:
        return False