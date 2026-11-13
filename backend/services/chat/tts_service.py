# backend\services\chat\tts_service.py

import logging
import queue
import threading
import time
from typing import Dict
from backend.interfaces import ITTSProvider
from backend.utils import strip_emojis

logger = logging.getLogger("minikick.services.chat.tts")

DEFAULT_MESSAGE_GAP_S = 0.7

class TTSManager:
    def __init__(self):
        self._providers: Dict[str, ITTSProvider] = {}
        self._active_provider_key = "piper"
        self._voices_cache = {"piper": [], "web": [], "local": []}
        self._main_voice_id = ""       
        self._audio_device_id = "default"
        self._volume = 1.0
        self._speed = 100
        self._piper_length_scale = 1.0
        self._piper_noise_scale = 0.667
        self._piper_noise_w_scale = 0.8
        self.text_queue: queue.Queue[tuple[str, str | None] | None] = queue.Queue()
        self.play_queue: queue.Queue[tuple[str, str | None, str] | None] = queue.Queue()
        self.on_speech_started = None
        self.on_speech_finished = None
        self._is_speaking = False       
        self._is_shutdown = False
        self._message_gap_s = DEFAULT_MESSAGE_GAP_S
        self._last_speech_end = 0.0
        self._stop_generation = 0
        self._interrupt_event = threading.Event()
        self._downloader_thread = threading.Thread(target=self._downloader_worker, daemon=True)
        self._downloader_thread.start()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _get_provider(self, key: str) -> ITTSProvider:
        if key not in self._providers:
            if key == "piper":
                from backend.providers.voices import PiperTTSProvider
                prov = PiperTTSProvider()
                prov.set_synthesis_params(self._piper_length_scale, self._piper_noise_scale, self._piper_noise_w_scale)
            elif key == "local":
                from backend.providers.voices import LocalTTSProvider
                prov = LocalTTSProvider()
            elif key == "web":
                from backend.providers.voices import WebTTSProvider
                prov = WebTTSProvider()
            else:
                from backend.providers.voices import PiperTTSProvider
                prov = PiperTTSProvider()
                prov.set_synthesis_params(self._piper_length_scale, self._piper_noise_scale, self._piper_noise_w_scale)
            
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
        logger.info("[TTS Manager] Setting audio output device: %s", device_id)
        for provider in self._providers.values():
            if hasattr(provider, "set_audio_device"):
                provider.set_audio_device(device_id)

    def say(self, text: str, voice_id: str = None) -> None:
        if self._is_shutdown:
            logger.warning("[TTS Manager] Ignoring speech request after shutdown.")
        elif text and text.strip():
            clean_t = strip_emojis(text)
            if not clean_t:
                logger.debug("[TTS Manager] Ignoring text that only contains emojis.")
                return
            self._trim_backlog()
            self.text_queue.put((clean_t, voice_id))
            logger.debug("[TTS Manager] Enqueued text (qsize=%d): '%s' (voice=%s)", self.text_queue.qsize(), clean_t[:35], voice_id or "default")

    def speak(self, text: str, voice_id: str = None) -> None:
        self.say(text, voice_id=voice_id)

    def set_message_gap(self, seconds: float) -> None:
        self._message_gap_s = max(0.0, float(seconds))

    def _wait_message_gap(self, generation: int) -> bool:
        if self._message_gap_s > 0 and self._last_speech_end > 0:
            remaining = self._message_gap_s - (time.monotonic() - self._last_speech_end)
            if remaining > 0:
                self._interrupt_event.clear()
                self._interrupt_event.wait(remaining)
        return generation == self._stop_generation

    def stop(self) -> None:
        self._stop_generation += 1
        self._interrupt_event.set()
        discarded_text = 0
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
                self.text_queue.task_done()
                discarded_text += 1
            except queue.Empty:
                break
        
        discarded_play = 0
        while not self.play_queue.empty():
            try:
                self.play_queue.get_nowait()
                self.play_queue.task_done()
                discarded_play += 1
            except queue.Empty:
                break
                
        if discarded_text > 0 or discarded_play > 0:
            logger.info("[TTS Manager] Stop requested: cleared %d pending text items, %d playback items", discarded_text, discarded_play)

        if self._active_provider_key in self._providers:
            self._providers[self._active_provider_key].stop()

        if self._is_speaking:
            self._is_speaking = False
            if self.on_speech_finished:
                try:
                    self.on_speech_finished()
                except Exception as fin_err:
                    logger.debug("[TTS Manager] on_speech_finished on stop error: %s", fin_err)

    _MAX_PENDING_SPEECH = 25

    def _trim_backlog(self) -> None:
        dropped = 0
        while self.text_queue.qsize() + self.play_queue.qsize() >= self._MAX_PENDING_SPEECH:
            source = self.play_queue if not self.play_queue.empty() else self.text_queue
            try:
                item = source.get_nowait()
            except queue.Empty:
                break
            source.task_done()
            if item is None:
                source.put(None)
                break
            dropped += 1
        if dropped:
            logger.warning("[TTS Manager] Backlog full; skipped %d stale message(s).", dropped)

    def shutdown(self) -> None:
        if self._is_shutdown:
            return
        self._is_shutdown = True
        try:
            self.stop()
        except Exception:
            logger.exception("[TTS Manager] Failed to stop active speech during shutdown.")
        self.text_queue.put(None)
        for prov in list(self._providers.values()):
            if hasattr(prov, "shutdown"):
                try:
                    prov.shutdown()
                except Exception:
                    logger.exception(
                        "[TTS Manager] Failed to shut down provider %s.",
                        type(prov).__name__,
                    )

    def _downloader_worker(self) -> None:
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
                logger.error("[TTS Manager] Downloader worker error (%s): %s", type(e).__name__, e, exc_info=True)
            finally:
                self.text_queue.task_done()

    def _worker(self) -> None:
        import sys
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
        while True:
            item = self.play_queue.get()
            try:
                if item is None:
                    break 
                generation = self._stop_generation
                text, voice_id, target_voice = item
                active_provider = self._provider
                
                if target_voice:
                    if hasattr(active_provider, 'voice_id'):
                        active_provider.voice_id = target_voice
                    elif hasattr(active_provider, 'voice'):
                        active_provider.voice = target_voice
                
                if not self._is_speaking:
                    self._is_speaking = True
                    if self.on_speech_started:
                        try:
                            self.on_speech_started()
                        except Exception as start_err:
                            logger.debug("[TTS Manager] on_speech_started error: %s", start_err)

                if self._wait_message_gap(generation):
                    active_provider.speak(text, voice_id=target_voice)
                    self._last_speech_end = time.monotonic()
                
            except Exception as e:
                logger.error("[TTS Manager] Critical engine failure avoided (%s): %s", type(e).__name__, e, exc_info=True)
            finally:
                self.play_queue.task_done()
                if self.play_queue.empty() and self._is_speaking:
                    self._is_speaking = False
                    if self.on_speech_finished:
                        try:
                            self.on_speech_finished()
                        except Exception as fin_err:
                            logger.debug("[TTS Manager] on_speech_finished error: %s", fin_err)

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

    def set_piper_synthesis_params(self, length_scale: float = 1.0, noise_scale: float = 0.667, noise_w_scale: float = 0.8) -> None:
        self._piper_length_scale = float(length_scale)
        self._piper_noise_scale = float(noise_scale)
        self._piper_noise_w_scale = float(noise_w_scale)
        if "piper" in self._providers:
            prov = self._providers["piper"]
            if hasattr(prov, "set_synthesis_params"):
                prov.set_synthesis_params(self._piper_length_scale, self._piper_noise_scale, self._piper_noise_w_scale)

    def get_piper_synthesis_params(self) -> tuple[float, float, float]:
        return (self._piper_length_scale, self._piper_noise_scale, self._piper_noise_w_scale)
