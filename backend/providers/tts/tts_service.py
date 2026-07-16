# backend\providers\tts\tts_service.py

import queue
import threading
from backend.interfaces.tts_interfaces import ITTSProvider
from backend.providers.tts.tts_local import LocalTTSProvider
from backend.providers.tts.tts_online import WebTTSProvider

class TTSManager:
    def __init__(self):
        self._providers = {
            "local": LocalTTSProvider(),
            "web": WebTTSProvider()
        }
        self._active_provider_key = "local"
        self._voices_cache = {"web": [], "local": []}
        self._main_voice_id = ""       
        self.text_queue: queue.Queue[tuple[str, str | None] | None] = queue.Queue()
        self.play_queue: queue.Queue[tuple[str, str | None, str] | None] = queue.Queue()       
        self._downloader_thread = threading.Thread(target=self._downloader_worker, daemon=True)
        self._downloader_thread.start()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    @property
    def _provider(self) -> ITTSProvider:
        return self._providers[self._active_provider_key]

    def set_provider(self, provider_type: str) -> None:
        if provider_type in self._providers:
            self._active_provider_key = provider_type

    def say(self, text: str, voice_id: str = None) -> None:
        if text and text.strip():
            self.text_queue.put((text.strip(), voice_id))

    def stop(self) -> None:
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
                self.text_queue.task_done()
            except queue.Empty:
                break
        
        while not self.play_queue.empty():
            try:
                self.play_queue.get_nowait()
                self.play_queue.task_done()
            except queue.Empty:
                break
                
        self.text_queue.put(None)
        self._provider.stop()

    def _downloader_worker(self) -> None:
        import logging
        while True:
            item = self.text_queue.get()
            try:
                if item is None:
                    self.play_queue.put(None)
                    break
                
                text, voice_id = item
                active_provider = self._provider
                target_voice = voice_id if voice_id else self._main_voice_id
                
                if hasattr(active_provider, "prepare"):
                    active_provider.prepare(text, target_voice)
                
                self.play_queue.put((text, voice_id, target_voice))
            except Exception as e:
                logging.error(f"[TTS Manager] Downloader worker error: {e}")
            finally:
                self.text_queue.task_done()

    def _worker(self) -> None:
        import logging
        while True:
            item = self.play_queue.get()
            try:
                if item is None:
                    break 
                text, voice_id, target_voice = item
                active_provider = self._provider
                
                if target_voice:
                    if hasattr(active_provider, 'voice_id'):
                        active_provider.voice_id = target_voice
                    elif hasattr(active_provider, 'voice'):
                        active_provider.voice = target_voice
                
                active_provider.speak(text)
                
            except Exception as e:
                logging.error(f"[TTS Manager] Critical engine failure avoided: {e}")
            finally:
                self.play_queue.task_done()

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
        self._main_voice_id = voice_id
        if hasattr(self._provider, 'voice_id'):
            self._provider.voice_id = voice_id
        elif hasattr(self._provider, 'voice'):
            self._provider.voice = voice_id
