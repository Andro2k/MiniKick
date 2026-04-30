# backend/tts.py

import queue
import threading
import pyttsx3
from backend.interfaces.tts_interfaces import TTSEngine

# --- Implementación Concreta de Hardware ---
class Pyttsx3Engine:
    """Implementación específica de pyttsx3 (Alta Cohesión con el hardware)"""
    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None # Voz por defecto del sistema

    def get_available_voices(self) -> list[dict[str, str]]:
        """Interroga al OS por las voces instaladas"""
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        # Limpiamos el nombre para que la UI no reciba texto basura
        return [{"id": v.id, "name": v.name.split(" - ")[0]} for v in voices]

    def set_voice(self, voice_id: str) -> None:
        self.voice_id = voice_id

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def speak(self, text: str) -> None:
        try:
            # Inicializamos dentro del hilo para evitar colisiones de memoria (COM errors)
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice_id:
                engine.setProperty("voice", self.voice_id)
                
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS] Error al hablar: {e}")

# --- Orquestador (Lógica de Negocio Asíncrona) ---
class TTSManager:
    """
    Gestiona una cola de mensajes en un hilo secundario.
    """
    def __init__(self, engine: TTSEngine):
        self.engine = engine
        self.queue: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def say(self, text: str) -> None:
        if text and text.strip():
            self.queue.put(text.strip())

    def stop(self) -> None:
        self.queue.put(None)
        self._thread.join(timeout=5)

    def _worker(self) -> None:
        while True:
            text = self.queue.get()

            if text is None:
                self.queue.task_done()
                break

            self.engine.speak(text)
            self.queue.task_done()