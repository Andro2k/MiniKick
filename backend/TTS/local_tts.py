# backend/TTS/local_tts.py

import pyttsx3
from backend.interfaces.tts_interfaces import ITTSProvider

class LocalTTSProvider(ITTSProvider):
    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None
        self._engine = None 

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def speak(self, text: str) -> None:
        try:
            if self._engine is None:
                self._engine = pyttsx3.init()
                
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
            if self.voice_id:
                self._engine.setProperty("voice", self.voice_id)
                
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            print(f"[TTS Local] Error al hablar: {e}")

    def stop(self) -> None:
        if self._engine:
            self._engine.stop()

    def get_available_voices(self) -> list[dict]:
        """Implementación nativa (SoR)"""
        try:
            # Aprovechamos el engine si ya existe, o lo iniciamos
            engine = self._engine if self._engine else pyttsx3.init()
            return [{"id": v.id, "name": v.name.split(" - ")[0]} for v in engine.getProperty('voices')]
        except Exception as e:
            print(f"[TTS Local] Error obteniendo voces locales: {e}")
            return [{"id": "default", "name": "Voz del Sistema (Por Defecto)"}]