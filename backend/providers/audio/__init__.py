# backend\providers\audio\__init__.py

from .devices import audio_output_exists, resolve_audio_output

__all__ = ["audio_output_exists", "resolve_audio_output"]
