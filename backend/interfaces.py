# backend/interfaces.py

from typing import Protocol

class TokenStorage(Protocol):
    """Contrato para almacenar y recuperar tokens."""
    def load(self) -> dict | None: ...
    def save(self, tokens: dict) -> None: ...

class TTSEngine(Protocol):
    """Contrato para cualquier motor de Text-to-Speech."""
    def speak(self, text: str) -> None: ...
    def set_volume(self, volume: float) -> None: ... # NUEVO CONTRATO