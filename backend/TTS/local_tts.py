# backend/TTS/local_tts.py

import pyttsx3
from backend.interfaces.tts_interfaces import ITTSProvider

class LocalTTSProvider(ITTSProvider):
    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None
        self._engine = None # Mantenemos una única referencia al motor

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def speak(self, text: str) -> None:
        try:
            # Lazy Initialization: Iniciamos el motor solo la primera vez que se usa
            # Esto evita crear miles de procesos de espeak en Linux
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
        # Limpieza correcta de la memoria del motor C
        if self._engine:
            self._engine.stop()