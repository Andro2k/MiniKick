# backend\providers\voices\tts_online.py

import asyncio
import logging
import os
import re
import tempfile
import threading
import time
import edge_tts
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QEventLoop

class WebTTSProvider:
    def __init__(self, voice: str = "es-ES-AlvaroNeural"):
        self.voice = voice
        self.volume_str = "+0%"
        self.volume = 1.0
        self._audio_device_id = "default"
        self._cache = {}
        self._cache_lock = threading.Lock()
        
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._loop_thread.start()

    def set_audio_device(self, device_id: str) -> None:
        self._audio_device_id = device_id

    @staticmethod
    def _is_speakable_text(text: str) -> bool:
        if not text or not text.strip():
            return False
        cleaned = re.sub(r'https?://\S+|www\.\S+', '', text).strip()
        if not cleaned:
            return False
        return any(c.isalnum() for c in cleaned)

    def _run_event_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        percent = int((self.volume - 1.0) * 100)
        self.volume_str = f"{percent}%" if percent < 0 else f"+{percent}%"

    def _resolve_valid_voice(self, voice_id: str | None) -> str:
        if voice_id and ("Neural" in voice_id or "-" in voice_id):
            return voice_id
        if self.voice and ("Neural" in self.voice or "-" in self.voice):
            return self.voice
        return "es-ES-AlvaroNeural"

    def prepare(self, text: str, voice_id: str = None) -> None:
        if not self._is_speakable_text(text):
            logging.debug(f"[Web TTS] Skipping prepare: no speakable content in '{text[:25]}...'")
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        
        last_err = None
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice, volume=self.volume_str)
                await communicate.save(temp_path)
                elapsed = time.perf_counter() - start_t
                logging.debug(f"[Web TTS Benchmark] Pre-downloaded audio in {elapsed:.3f}s for: '{text[:25]}...' (voice: {voice})")
                return temp_path
            except Exception as e:
                last_err = e
                err_msg = str(e)
                if "No audio was received" in err_msg or "parameters are correct" in err_msg:
                    logging.warning(f"[Web TTS] Unsupported text for voice {voice}: '{text[:25]}...' ({e})")
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
            logging.debug(f"[Web TTS] Skipping speak: no speakable content in '{text[:25]}...'")
            return
        start_t = time.perf_counter()
        try:
            self._run_async(self._async_speak(text, voice_id, start_t))
        except Exception as e:
            logging.error("[Web TTS] Error in speak wrapper: %s", e)

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
                    logging.debug(f"[Web TTS Benchmark] CACHE HIT! Prep wait/retrieval time: {t_cache_hit:.3f}s for: '{text[:25]}...'")
                    await self._play_audio_file(temp_path, prep_start_t)
                    return
            except Exception as e:
                logging.error("[Web TTS] Pre-download future error, falling back: %s", e)

        logging.warning(f"[Web TTS Benchmark] CACHE MISS. Downloading on-the-fly for: '{text[:25]}...' (voice: {voice})")
        t_dl_start = time.perf_counter()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        
        last_err = None
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice, volume=self.volume_str)
                await communicate.save(temp_path)
                t_dl_end = time.perf_counter() - t_dl_start
                logging.debug(f"[Web TTS Benchmark] On-the-fly download completed in {t_dl_end:.3f}s")
                await self._play_audio_file(temp_path, start_t)
                return
            except Exception as e:
                last_err = e
                err_msg = str(e)
                if "No audio was received" in err_msg or "parameters are correct" in err_msg:
                    logging.warning(f"[Web TTS] Unsupported text for voice {voice}: '{text[:25]}...' ({e})")
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
        player = None
        audio_output = None
        try:
            player = QMediaPlayer()
            audio_output = QAudioOutput()
            if hasattr(self, "_audio_device_id") and self._audio_device_id and self._audio_device_id != "default":
                try:
                    from PySide6.QtMultimedia import QMediaDevices
                    for dev in QMediaDevices.audioOutputs():
                        dev_id_str = dev.id().data().decode("utf-8", errors="ignore") if hasattr(dev.id(), "data") else str(dev.id())
                        if dev_id_str == self._audio_device_id or dev.description() == self._audio_device_id:
                            audio_output.setDevice(dev)
                            break
                except Exception as dev_err:
                    logging.error("[Web TTS] Error setting audio output device: %s", dev_err)
            player.setAudioOutput(audio_output)
            audio_output.setVolume(self.volume)
            player.setSource(QUrl.fromLocalFile(os.path.abspath(temp_path)))
            
            loop = QEventLoop()
            
            def handle_state(state):
                if state == QMediaPlayer.PlaybackState.StoppedState:
                    loop.quit()
            
            def handle_status(status):
                if status in (QMediaPlayer.MediaStatus.InvalidMedia, QMediaPlayer.MediaStatus.NoMedia, QMediaPlayer.MediaStatus.EndOfMedia):
                    loop.quit()
                    
            connection_state = player.playbackStateChanged.connect(handle_state)
            connection_status = player.mediaStatusChanged.connect(handle_status)
            
            player.play()
            
            t_play_ready = time.perf_counter() - play_start_t
            t_total_delay = time.perf_counter() - request_start_t if request_start_t > 0 else t_play_ready
            logging.debug(f"[Web TTS Benchmark] PLAYBACK STARTED! Audio Prep->Play Latency: {t_play_ready:.3f}s | TOTAL DELAY FROM REQUEST: {t_total_delay:.3f}s")
            
            loop.exec()
            
            try:
                player.playbackStateChanged.disconnect(connection_state)
                player.mediaStatusChanged.disconnect(connection_status)
            except Exception:
                pass

        except Exception as e:
            logging.error("[Web TTS] Error playing audio file: %s", e)
        finally:
            if player:
                try:
                    player.stop()
                    player.setSource(QUrl())
                    player.deleteLater()
                except Exception:
                    pass
            if audio_output:
                try:
                    audio_output.deleteLater()
                except Exception:
                    pass
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

    def stop(self) -> None:
        with self._cache_lock:
            for item in self._cache.values():
                try:
                    future = item[0] if isinstance(item, tuple) else item
                    if hasattr(future, "result"):
                        temp_path = future.result()
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)
                except Exception as e:
                    logging.error("[Web TTS] Error cleaning up cached file: %s", e)
            self._cache.clear()

    def get_available_voices(self) -> list[dict]:
        try:
            voices = asyncio.run(edge_tts.list_voices())
            return [{"id": v["ShortName"], "name": v["FriendlyName"]} for v in voices if "es-" in v["Locale"]]
        except Exception as e:
            logging.error("[Web TTS] Error connecting to Microsoft Edge: %s", e)
            return [
                {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Spain) - Offline"},
                {"id": "es-ES-ElviraNeural", "name": "Elvira (Spain) - Offline"},
                {"id": "es-MX-JorgeNeural", "name": "Jorge (Mexico) - Offline"},
                {"id": "es-MX-DaliaNeural", "name": "Dalia (Mexico) - Offline"}
            ]
