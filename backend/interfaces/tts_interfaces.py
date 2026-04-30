# backend/interfaces/tts_interfaces.py

from typing import Protocol

class TTSEngine(Protocol):
    """Contrato para cualquier motor de Text-to-Speech."""
    def speak(self, text: str) -> None: ...
    def set_volume(self, volume: float) -> None: ...