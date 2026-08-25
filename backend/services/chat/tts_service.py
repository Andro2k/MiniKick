# backend\services\chat\tts_service.py

import queue
import threading
from typing import Dict
from backend.interfaces import ITTSProvider

class TTSManager:
    def __init__(self):
        self._providers: Dict[str, ITTSProvider] = {}
        self._active_provider_key = "piper"
        self._voices_cache = {"piper": [], "web": [], "local": []}
        self._main_voice_id = ""       
        self._audio_device_id = "default"
        self._volume = 1.0
        self._speed = 100
        self.text_queue: queue.Queue[tuple[str, str | None] | None] = queue.Queue()
        self.play_queue: queue.Queue[tuple[str, str | None, str] | None] = queue.Queue()       
        self._downloader_thread = threading.Thread(target=self._downloader_worker, daemon=True)
        self._downloader_thread.start()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _get_provider(self, key: str) -> ITTSProvider:
        if key not in self._providers:
            if key == "piper":
                from backend.providers.voices.tts_piper import PiperTTSProvider
                prov = PiperTTSProvider()
            elif key == "local":
                from backend.providers.voices.tts_local import LocalTTSProvider
                prov = LocalTTSProvider()
            elif key == "web":
                from backend.providers.voices.tts_online import WebTTSProvider
                prov = WebTTSProvider()
            else:
                from backend.providers.voices.tts_piper import PiperTTSProvider
                prov = PiperTTSProvider()
            
            if hasattr(prov, "set_audio_device"):
                prov.set_audio_device(self._audio_device_id)
            if hasattr(prov, "set_volume"):
                prov.set_volume(self._volume)
            if hasattr(prov, "set_speed"):
                prov.set_speed(self._speed)
            if self._main_voice_id:
                if hasattr(prov, "voice_id"):
                    prov.voice_id = self._main_voice_id
                elif hasattr(prov, "voice"):
                    prov.voice = self._main_voice_id
            self._providers[key] = prov
        return self._providers[key]

    @property
    def _provider(self) -> ITTSProvider:
        return self._get_provider(self._active_provider_key)

    def set_provider(self, provider_type: str) -> None:
        if provider_type in ("piper", "local", "web"):
            self._active_provider_key = provider_type
            if provider_type == "piper":
                self.warm_up("piper")

    def warm_up(self, provider_type: str = None, voice_id: str = None) -> None:
        prov_key = provider_type or self._active_provider_key
        if prov_key in self._providers:
            provider = self._providers[prov_key]
            if provider and hasattr(provider, "warm_up"):
                provider.warm_up(voice_id)
        elif prov_key == "piper":
            def _async_init_and_warm():
                prov = self._get_provider("piper")
                if prov and hasattr(prov, "warm_up"):
                    prov.warm_up(voice_id)
            threading.Thread(target=_async_init_and_warm, daemon=True, name="PiperAsyncInitWarm").start()

    def set_audio_device(self, device_id: str) -> None:
        self._audio_device_id = device_id
        for provider in self._providers.values():
            if hasattr(provider, "set_audio_device"):
                provider.set_audio_device(device_id)

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
        if self._active_provider_key in self._providers:
            self._providers[self._active_provider_key].stop()

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
                
                active_provider.speak(text, voice_id=target_voice)
                
            except Exception as e:
                logging.error(f"[TTS Manager] Critical engine failure avoided: {e}")
            finally:
                self.play_queue.task_done()

    def get_available_voices(self, provider_type: str) -> list[dict]:
        if provider_type in self._voices_cache and self._voices_cache[provider_type]:
            return self._voices_cache[provider_type]
            
        target_provider = self._get_provider(provider_type)
        voices = target_provider.get_available_voices()
        self._voices_cache[provider_type] = voices
        return voices

    def invalidate_voices_cache(self, provider_type: str = None) -> None:
        if provider_type:
            self._voices_cache[provider_type] = []
        else:
            for k in self._voices_cache:
                self._voices_cache[k] = []

    def set_volume(self, volume: float) -> None:
        self._volume = volume
        if self._active_provider_key in self._providers:
            self._providers[self._active_provider_key].set_volume(volume)

    def set_speed(self, speed: float) -> None:
        self._speed = speed
        for prov in self._providers.values():
            if hasattr(prov, "set_speed"):
                prov.set_speed(speed)

    def set_voice(self, voice_id: str) -> None:
        self._main_voice_id = voice_id
        if self._active_provider_key in self._providers:
            provider = self._providers[self._active_provider_key]
            if hasattr(provider, 'voice_id'):
                provider.voice_id = voice_id
            elif hasattr(provider, 'voice'):
                provider.voice = voice_id
