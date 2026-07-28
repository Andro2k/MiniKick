# backend\providers\voices\tts_online.py

import asyncio
import logging
import os
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
        self.player = None
        self.audio_output = None
        self._cache = {}
        self._cache_lock = threading.Lock()
        
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._loop_thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        if self.audio_output:
            self.audio_output.setVolume(self.volume)
        percent = int((self.volume - 1.0) * 100)
        self.volume_str = f"{percent}%" if percent < 0 else f"+{percent}%"

    def prepare(self, text: str, voice_id: str = None) -> None:
        voice = voice_id if voice_id else self.voice
        start_t = time.perf_counter()
        cache_key = (text, voice)
        with self._cache_lock:
            if cache_key in self._cache:
                return
            future = asyncio.run_coroutine_threadsafe(self._async_prepare(text, voice, start_t), self._loop)
            self._cache[cache_key] = (future, start_t)

    async def _async_prepare(self, text: str, voice: str, start_t: float) -> str:
        communicate = edge_tts.Communicate(text, voice, volume=self.volume_str)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        try:
            await communicate.save(temp_path)
            elapsed = time.perf_counter() - start_t
            logging.info(f"[Web TTS Benchmark] Pre-downloaded audio in {elapsed:.3f}s for: '{text[:25]}...' (voice: {voice})")
            return temp_path
        except Exception as e:
            logging.error("[Web TTS] Error pre-downloading audio: %s", e)
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            raise e

    def speak(self, text: str, voice_id: str = None) -> None:
        start_t = time.perf_counter()
        try:
            self._run_async(self._async_speak(text, voice_id, start_t))
        except Exception as e:
            logging.error("[Web TTS] Error in speak wrapper: %s", e)

    async def _async_speak(self, text: str, voice_id: str = None, start_t: float = 0.0) -> None:
        voice = voice_id if voice_id else self.voice
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
                    logging.info(f"[Web TTS Benchmark] CACHE HIT! Prep wait/retrieval time: {t_cache_hit:.3f}s for: '{text[:25]}...'")
                    await self._play_audio_file(temp_path, prep_start_t)
                    return
            except Exception as e:
                logging.error("[Web TTS] Pre-download future error, falling back: %s", e)

        logging.warning(f"[Web TTS Benchmark] CACHE MISS. Downloading on-the-fly for: '{text[:25]}...' (voice: {voice})")
        t_dl_start = time.perf_counter()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        try:
            communicate = edge_tts.Communicate(text, voice, volume=self.volume_str)
            await communicate.save(temp_path)
            t_dl_end = time.perf_counter() - t_dl_start
            logging.info(f"[Web TTS Benchmark] On-the-fly download completed in {t_dl_end:.3f}s")
            await self._play_audio_file(temp_path, start_t)
        except Exception as e:
            logging.error("[Web TTS] Error in fallback play: %s", e)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

    async def _play_audio_file(self, temp_path: str, request_start_t: float = 0.0) -> None:
        play_start_t = time.perf_counter()
        try:
            if not self.player:
                self.player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.player.setAudioOutput(self.audio_output)
            
            self.audio_output.setVolume(self.volume)
            self.player.setSource(QUrl.fromLocalFile(os.path.abspath(temp_path)))
            
            loop = QEventLoop()
            
            def handle_state(state):
                if state == QMediaPlayer.PlaybackState.StoppedState:
                    loop.quit()
            
            def handle_status(status):
                if status in (QMediaPlayer.MediaStatus.InvalidMedia, QMediaPlayer.MediaStatus.NoMedia):
                    loop.quit()
                    
            connection_state = self.player.playbackStateChanged.connect(handle_state)
            connection_status = self.player.mediaStatusChanged.connect(handle_status)
            
            self.player.play()
            
            t_play_ready = time.perf_counter() - play_start_t
            t_total_delay = time.perf_counter() - request_start_t if request_start_t > 0 else t_play_ready
            logging.info(f"[Web TTS Benchmark] 🔊 PLAYBACK STARTED! Audio Prep->Play Latency: {t_play_ready:.3f}s | TOTAL DELAY FROM REQUEST: {t_total_delay:.3f}s")
            
            loop.exec()
            
            self.player.playbackStateChanged.disconnect(connection_state)
            self.player.mediaStatusChanged.disconnect(connection_status)

        except Exception as e:
            logging.error("[Web TTS] Error playing audio file: %s", e)
        finally:
            if self.player:
                try:
                    self.player.setSource(QUrl())
                except Exception:
                    pass
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

    def stop(self) -> None:
        if self.player:
            self.player.stop()
        
        with self._cache_lock:
            for item in self._cache.values():
                temp_path = item[0] if isinstance(item, tuple) else item
                try:
                    if os.path.exists(temp_path):
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
