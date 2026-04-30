# backend/TTS/local_tts.py

import pyttsx3
from backend.interfaces.tts_interfaces import ITTSProvider

class LocalTTSProvider(ITTSProvider):
    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def speak(self, text: str) -> None:
        try:
            # Inicialización local para evitar colisiones de memoria en el Worker Thread
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice_id:
                engine.setProperty("voice", self.voice_id)
                
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS Local] Error al hablar: {e}")

    def stop(self) -> None:
        pass # pyttsx3 es bloqueante en runAndWait(), pero mantenemos la firma