# backend\providers\voices\tts_online.py

import asyncio
import logging
import os
import re
import tempfile
import threading
import time
import edge_tts
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtCore import QUrl, QEventLoop

logger = logging.getLogger("minikick.providers.web_tts")

class WebTTSProvider:
    def __init__(self, voice: str = "es-ES-AlvaroNeural"):
        self.voice = voice
        self.volume_str = "+0%"
        self.rate_str = "+0%"
        self.volume = 1.0
        self._audio_device_id = "default"
        self._cached_audio_device = None
        self._cached_device_id = None
        
        self._cache = {}
        self._cache_lock = threading.Lock()
        
        self._player: QMediaPlayer | None = None
        self._audio_output: QAudioOutput | None = None
        self._current_loop: QEventLoop | None = None
        
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True, name="WebTTSAsyncLoop")
        self._loop_thread.start()

    def set_audio_device(self, device_id: str) -> None:
        if self._audio_device_id != device_id:
            self._audio_device_id = device_id
            self._cached_audio_device = None
            self._cached_device_id = None

    def _resolve_audio_device(self):
        if self._cached_audio_device is not None and self._cached_device_id == self._audio_device_id:
            return self._cached_audio_device

        target_dev = None
        try:
            if self._audio_device_id and self._audio_device_id != "default":
                for dev in QMediaDevices.audioOutputs():
                    dev_id_str = dev.id().data().decode("utf-8", errors="ignore") if hasattr(dev.id(), "data") else str(dev.id())
                    if dev_id_str == self._audio_device_id or dev.description() == self._audio_device_id:
                        target_dev = dev
                        break
            if not target_dev:
                target_dev = QMediaDevices.defaultAudioOutput()
        except Exception as dev_err:
            logger.error("[Web TTS] Error resolving audio output device: %s", dev_err)

        self._cached_audio_device = target_dev
        self._cached_device_id = self._audio_device_id
        return target_dev

    def _ensure_player(self):
        if self._player is None:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
        return self._player, self._audio_output

    @staticmethod
    def _is_speakable_text(text: str) -> bool:
        if not text or not text.strip():
            return False
        cleaned = re.sub(r'https?://\S+|www\.\S+', '', text).strip()
        if not cleaned:
            return False
        return any(c.isalnum() for c in cleaned)

    def _run_event_loop(self):
        import sys
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        except Exception:
            pass
        finally:
            try:
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                if pending and not self._loop.is_closed():
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            try:
                if not self._loop.is_closed():
                    self._loop.close()
            except Exception:
                pass

    def _run_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        percent = round((self.volume - 1.0) * 100)
        self.volume_str = f"{percent}%" if percent < 0 else f"+{percent}%"
        if self._audio_output:
            self._audio_output.setVolume(self.volume)

    def set_speed(self, speed: float) -> None:
        factor = speed if speed <= 3.0 else (speed / 100.0)
        percent = round((factor - 1.0) * 100)
        self.rate_str = f"{percent}%" if percent < 0 else f"+{percent}%"

    def _resolve_valid_voice(self, voice_id: str | None) -> str:
        if voice_id and ("Neural" in voice_id or "-" in voice_id):
            return voice_id
        if self.voice and ("Neural" in self.voice or "-" in self.voice):
            return self.voice
        return "es-ES-AlvaroNeural"

    def warm_up(self, voice_id: str = None) -> None:
        pass

    def prepare(self, text: str, voice_id: str = None) -> None:
        if not self._is_speakable_text(text):
            logger.debug(f"[Web TTS] Skipping prepare: no speakable content in '{text[:25]}...'")
            return
        voice = self._resolve_valid_voice(voice_id)
        start_t = time.perf_counter()
        cache_key = (text, voice)
        with self._cache_lock:
            if cache_key in self._cache:
                return
            future = asyncio.run_coroutine_threadsafe(self._async_prepare(text, voice, start_t), self._loop)
            self._cache[cache_key] = (future, start_t)

    async def _async_prepare(self, text: str, voice: str, start_t: float) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", prefix="minikick_webtts_") as fp:
            temp_path = fp.name
        
        last_err = None
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice, volume=self.volume_str, rate=self.rate_str)
                await asyncio.wait_for(communicate.save(temp_path), timeout=5.0)
                elapsed = time.perf_counter() - start_t
                logger.debug(f"[Web TTS Benchmark] Pre-downloaded audio in {elapsed:.3f}s for: '{text[:25]}...' (voice: {voice})")
                return temp_path
            except Exception as e:
                last_err = e
                err_msg = str(e)
                if "No audio was received" in err_msg or "parameters are correct" in err_msg:
                    logger.warning(f"[Web TTS] Unsupported text for voice {voice}: '{text[:25]}...' ({e})")
                    break
                if attempt < 2:
                    await asyncio.sleep(0.2 * (attempt + 1))

        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
            
        if last_err is not None:
            err_msg = str(last_err)
            if "No audio was received" in err_msg or "parameters are correct" in err_msg:
                return ""
            raise last_err
        return ""

    def speak(self, text: str, voice_id: str = None) -> None:
        if not self._is_speakable_text(text):
            logger.debug(f"[Web TTS] Skipping speak: no speakable content in '{text[:25]}...'")
            return
        start_t = time.perf_counter()
        try:
            self._run_async(self._async_speak(text, voice_id, start_t))
        except Exception as e:
            logger.error("[Web TTS] Error in speak wrapper: %s", e)

    async def _async_speak(self, text: str, voice_id: str = None, start_t: float = 0.0) -> None:
        voice = self._resolve_valid_voice(voice_id)
        cache_key = (text, voice)
        
        cached_entry = None
        with self._cache_lock:
            if cache_key in self._cache:
                cached_entry = self._cache.pop(cache_key)
                
        if cached_entry:
            future, prep_start_t = cached_entry
            try:
                temp_path = await asyncio.wrap_future(future)
                if temp_path and os.path.exists(temp_path):
                    t_cache_hit = time.perf_counter() - start_t
                    logger.debug(f"[Web TTS Benchmark] CACHE HIT! Prep wait/retrieval time: {t_cache_hit:.3f}s for: '{text[:25]}...'")
                    await self._play_audio_file(temp_path, prep_start_t)
                    return
            except Exception as e:
                logger.error("[Web TTS] Pre-download future error, falling back: %s", e)

        logger.debug(f"[Web TTS Benchmark] CACHE MISS. Downloading on-the-fly for: '{text[:25]}...' (voice: {voice})")
        t_dl_start = time.perf_counter()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", prefix="minikick_webtts_") as fp:
            temp_path = fp.name
        
        last_err = None
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice, volume=self.volume_str, rate=self.rate_str)
                await asyncio.wait_for(communicate.save(temp_path), timeout=5.0)
                t_dl_end = time.perf_counter() - t_dl_start
                logger.debug(f"[Web TTS Benchmark] On-the-fly download completed in {t_dl_end:.3f}s")
                await self._play_audio_file(temp_path, start_t)
                return
            except Exception as e:
                last_err = e
                err_msg = str(e)
                if "No audio was received" in err_msg or "parameters are correct" in err_msg:
                    logger.warning(f"[Web TTS] Unsupported text for voice {voice}: '{text[:25]}...' ({e})")
                    break
                if attempt < 2:
                    await asyncio.sleep(0.2 * (attempt + 1))
        
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

    async def _play_audio_file(self, temp_path: str, request_start_t: float = 0.0) -> None:
        play_start_t = time.perf_counter()
        player, audio_output = self._ensure_player()
        loop = QEventLoop()
        self._current_loop = loop
        
        try:
            target_dev = self._resolve_audio_device()
            if target_dev and audio_output.device() != target_dev:
                audio_output.setDevice(target_dev)
            
            audio_output.setVolume(self.volume)
            player.setSource(QUrl.fromLocalFile(os.path.abspath(temp_path)))
            
            def handle_state(state):
                if state == QMediaPlayer.PlaybackState.StoppedState:
                    if loop.isRunning():
                        loop.quit()
            
            def handle_status(status):
                if status in (QMediaPlayer.MediaStatus.InvalidMedia, QMediaPlayer.MediaStatus.NoMedia, QMediaPlayer.MediaStatus.EndOfMedia):
                    if loop.isRunning():
                        loop.quit()
                    
            connection_state = player.playbackStateChanged.connect(handle_state)
            connection_status = player.mediaStatusChanged.connect(handle_status)

            player.play()
            
            t_play_ready = time.perf_counter() - play_start_t
            t_total_delay = time.perf_counter() - request_start_t if request_start_t > 0 else t_play_ready
            logger.debug(f"[Web TTS Benchmark] PLAYBACK STARTED! Audio Prep->Play Latency: {t_play_ready:.3f}s | TOTAL DELAY FROM REQUEST: {t_total_delay:.3f}s")
            
            loop.exec()
            
            try:
                player.playbackStateChanged.disconnect(connection_state)
                player.mediaStatusChanged.disconnect(connection_status)
            except Exception:
                pass

        except Exception as e:
            logger.error("[Web TTS] Error playing audio file: %s", e)
        finally:
            self._current_loop = None
            if player:
                try:
                    player.stop()
                    player.setSource(QUrl())
                except Exception:
                    pass
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

    def stop(self) -> None:
        if self._player:
            try:
                self._player.stop()
                self._player.setSource(QUrl())
            except Exception:
                pass
        if self._current_loop and self._current_loop.isRunning():
            try:
                self._current_loop.quit()
            except Exception:
                pass
        with self._cache_lock:
            for item in self._cache.values():
                try:
                    future = item[0] if isinstance(item, tuple) else item
                    if hasattr(future, "result"):
                        temp_path = future.result()
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)
                except Exception as e:
                    logger.error("[Web TTS] Error cleaning up cached file: %s", e)
            self._cache.clear()

    def shutdown(self) -> None:
        self.stop()
        if hasattr(self, "_loop") and self._loop and self._loop.is_running():
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass

    def get_available_voices(self) -> list[dict]:
        try:
            voices = asyncio.run(edge_tts.list_voices())
            filtered = [
                {"id": v["ShortName"], "name": v["FriendlyName"]}
                for v in voices
                if "es-" in v["Locale"] or "en-US" in v["Locale"] or "en-GB" in v["Locale"]
            ]
            if filtered:
                return filtered
        except Exception as e:
            logger.error("[Web TTS] Error connecting to Microsoft Edge: %s", e)
        return [
            {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Spain)"},
            {"id": "es-ES-ElviraNeural", "name": "Elvira (Spain)"},
            {"id": "es-MX-JorgeNeural", "name": "Jorge (Mexico)"},
            {"id": "es-MX-DaliaNeural", "name": "Dalia (Mexico)"},
            {"id": "es-AR-ElenaNeural", "name": "Elena (Argentina)"},
            {"id": "es-CO-GonzaloNeural", "name": "Gonzalo (Colombia)"},
            {"id": "en-US-JennyNeural", "name": "Jenny (US English)"},
            {"id": "en-US-GuyNeural", "name": "Guy (US English)"}
        ]
