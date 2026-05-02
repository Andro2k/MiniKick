# backend/tts.py

import queue
import threading
from backend.interfaces.tts_interfaces import ITTSProvider
from backend.TTS.local_tts import LocalTTSProvider
from backend.TTS.web_tts import WebTTSProvider

class TTSManager:
    """
    Gestiona una cola de mensajes en un hilo secundario y delega
    """
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
        """Detiene la cola y el motor actual."""
        self.queue.put(None)
        self._provider.stop() 

    def _worker(self) -> None:
        while True:
            text = self.queue.get()

            if text is None:
                self.queue.task_done()
                break

            self._provider.speak(text)
            self.queue.task_done()

    def get_available_voices(self, provider_type: str) -> list[dict]:
        """Obtiene las voces disponibles según el motor activo."""
        if provider_type == "web":
            import asyncio
            import edge_tts
            try:
                voices = asyncio.run(edge_tts.list_voices())
                return [{"id": v["ShortName"], "name": v["FriendlyName"]} for v in voices if "es-" in v["Locale"]]
            except Exception as e:
                print(f"[TTS Web] Error al conectar con Microsoft Edge: {e}")
                return [
                    {"id": "es-ES-AlvaroNeural", "name": "Álvaro (España) - Modo Desconectado"},
                    {"id": "es-ES-ElviraNeural", "name": "Elvira (España) - Modo Desconectado"},
                    {"id": "es-MX-JorgeNeural", "name": "Jorge (México) - Modo Desconectado"},
                    {"id": "es-MX-DaliaNeural", "name": "Dalia (México) - Modo Desconectado"}
                ]
        else:
            import pyttsx3
            try:
                engine = pyttsx3.init()
                return [{"id": v.id, "name": v.name.split(" - ")[0]} for v in engine.getProperty('voices')]
            except Exception as e:
                print(f"[TTS Local] Error obteniendo voces locales: {e}")
                return [{"id": "default", "name": "Voz del Sistema (Por Defecto)"}]

    def set_volume(self, volume: float) -> None:
        """Delega el cambio de volumen al proveedor activo."""
        if hasattr(self._provider, 'set_volume'):
            self._provider.set_volume(volume)

    def set_voice(self, voice_id: str) -> None:
        """Delega el cambio de voz al proveedor activo."""
        if hasattr(self._provider, 'voice_id'):
            self._provider.voice_id = voice_id
        elif hasattr(self._provider, 'voice'):
            self._provider.voice = voice_id