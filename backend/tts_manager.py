# backend/tts_manager.py

import queue
import threading
from backend.interfaces.tts_interfaces import ITTSProvider
from backend.TTS.local_tts import LocalTTSProvider
from backend.TTS.web_tts import WebTTSProvider

class TTSManager:
    """Gestiona una cola de mensajes en un hilo secundario y delega."""
    def __init__(self):
        self._provider: ITTSProvider = LocalTTSProvider()
        
        self.queue: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def set_provider(self, provider_type: str) -> None:
        """Cambia el motor en caliente (Factory)."""
        if provider_type == "web":
            self._provider = WebTTSProvider()
        else:
            self._provider = LocalTTSProvider()

    def say(self, text: str) -> None:
        if text and text.strip():
            self.queue.put(text.strip())

    def stop(self) -> None:
        self.queue.put(None)
        self._provider.stop() 

    def _worker(self) -> None:
        while True:
            text = self.queue.get()
            try:
                if text is None:
                    break 
                self._provider.speak(text)
            except Exception as e:
                import logging
                logging.error(f"[TTS Manager] Fallo crítico evitado en el motor: {e}")
            finally:
                self.queue.task_done()

    def get_available_voices(self, provider_type: str) -> list[dict]:
        """Delega la búsqueda de voces al motor activo sin saber cómo lo hace (Decoupling)"""
        # (El parámetro provider_type se mantiene por compatibilidad con tu frontend)
        return self._provider.get_available_voices()

    def set_volume(self, volume: float) -> None:
        self._provider.set_volume(volume)

    def set_voice(self, voice_id: str) -> None:
        if hasattr(self._provider, 'voice_id'):
            self._provider.voice_id = voice_id
        elif hasattr(self._provider, 'voice'):
            self._provider.voice = voice_id