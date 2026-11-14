# backend\services\voice\__init__.py
"""Servicios de voz: administrador de texto a voz y administrador de voces Piper."""

from .tts_service import TTSManager
from .piper_manager_service import (
    PiperVoiceManager,
    PiperVoiceDownloadWorker,
    DEFAULT_PIPER_VOICE_ID,
)

__all__ = [
    "TTSManager",
    "PiperVoiceManager",
    "PiperVoiceDownloadWorker",
    "DEFAULT_PIPER_VOICE_ID",
]
