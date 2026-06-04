# backend/TTS/local_tts.py

import threading
import pyttsx3
from backend.interfaces.tts_interfaces import ITTSProvider

class LocalTTSProvider(ITTSProvider):
    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None
        self._thread_local = threading.local()

    def _get_engine(self):
        """Asegura que cada hilo tenga su propia instancia COM viva y aislada."""
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        if not hasattr(self._thread_local, 'engine'):
            self._thread_local.engine = pyttsx3.init()
        return self._thread_local.engine

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def speak(self, text: str) -> None:
        try:
            engine = self._get_engine()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice_id:
                engine.setProperty("voice", self.voice_id)
                
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS Local] Error al hablar: {e}")

    def stop(self) -> None:
        try:
            if hasattr(self._thread_local, 'engine'):
                self._thread_local.engine.stop()
        except Exception:
            pass

    def get_available_voices(self) -> list[dict]:
        """Alta Cohesión: Reutiliza el motor seguro del hilo, sin crear 'temp_engines'."""
        try:
            engine = self._get_engine()
            return [{"id": v.id, "name": v.name.split(" - ")[0]} for v in engine.getProperty('voices')]
        except Exception as e:
            print(f"[TTS Local] Error obteniendo voces locales: {e}")
            return [{"id": "default", "name": "Voz del Sistema (Por Defecto)"}]