# backend\interfaces\music_interfaces.py

from abc import ABC, abstractmethod

class MusicPlayerProvider(ABC):
    @abstractmethod
    def get_current_song(self) -> dict | None:
        pass

    @abstractmethod
    def add_to_queue(self, query_or_uri: str) -> tuple[bool, str]:
        pass

    @abstractmethod
    def skip_current(self) -> bool:
        pass