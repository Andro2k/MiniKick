# backend/tts_manager.py

import queue
import threading
from backend.interfaces.tts_interfaces import ITTSProvider
from backend.TTS.local_tts import LocalTTSProvider
from backend.TTS.web_tts import WebTTSProvider

class TTSManager:
    def __init__(self):
        self._providers = {
            "local": LocalTTSProvider(),
            "web": WebTTSProvider()
        }
        self._active_provider_key = "local"
        self._voices_cache = {"web": [], "local": []}
        
        self.queue: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    @property
    def _provider(self) -> ITTSProvider:
        return self._providers[self._active_provider_key]

    def set_provider(self, provider_type: str) -> None:
        if provider_type in self._providers:
            self._active_provider_key = provider_type

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
                active_provider = self._provider
                active_provider.speak(text)
                
            except Exception as e:
                import logging
                logging.error(f"[TTS Manager] Fallo crítico evitado en el motor: {e}")
            finally:
                self.queue.task_done()

    def get_available_voices(self, provider_type: str) -> list[dict]:
        if provider_type in self._voices_cache and self._voices_cache[provider_type]:
            return self._voices_cache[provider_type]
            
        target_provider = self._providers.get(provider_type, self._provider)
        voices = target_provider.get_available_voices()
        self._voices_cache[provider_type] = voices
        return voices

    def set_volume(self, volume: float) -> None:
        self._provider.set_volume(volume)

    def set_voice(self, voice_id: str) -> None:
        if hasattr(self._provider, 'voice_id'):
            self._provider.voice_id = voice_id
        elif hasattr(self._provider, 'voice'):
            self._provider.voice = voice_id