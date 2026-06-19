# backend/interfaces/tts_interfaces.py

from abc import ABC, abstractmethod

class ITTSProvider(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        pass
        
    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> None:
        pass

    @abstractmethod
    def get_available_voices(self) -> list[dict]:
        pass