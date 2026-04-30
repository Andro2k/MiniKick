# backend/interfaces/tts_interfaces.py

from abc import ABC, abstractmethod

class ITTSProvider(ABC):
    """Contrato único para cualquier motor de Text-to-Speech."""
    
    @abstractmethod
    def speak(self, text: str) -> None:
        """Reproduce el texto enviado."""
        pass
        
    @abstractmethod
    def stop(self) -> None:
        """Detiene la reproducción actual."""
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """Ajusta el volumen del motor (0.0 a 1.0)."""
        pass