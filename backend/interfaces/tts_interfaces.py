# backend/interfaces/tts_interfaces.py

from abc import ABC, abstractmethod

class ITTSProvider(ABC):
    """Contrato único para cualquier motor de Text-to-Speech."""
    
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
        """Debe retornar una lista de diccionarios con 'id' y 'name'."""
        pass