# backend\providers\audio\__init__.py
"""Proveedores y utilidades para dispositivos de audio."""

from .audio_devices_provider import audio_output_exists, resolve_audio_output

__all__ = ["audio_output_exists", "resolve_audio_output"]
