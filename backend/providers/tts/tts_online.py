# backend\providers\tts\tts_online.py

import asyncio
import logging
import os
import tempfile
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

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        if self.audio_output:
            self.audio_output.setVolume(self.volume)
        percent = int((self.volume - 1.0) * 100)
        self.volume_str = f"{percent}%" if percent < 0 else f"+{percent}%"

    def speak(self, text: str) -> None:
        asyncio.run(self._async_speak(text))

    async def _async_speak(self, text: str) -> None:
        communicate = edge_tts.Communicate(text, self.voice, volume=self.volume_str)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
            
        try:
            await communicate.save(temp_path)
            
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
            loop.exec()
            
            self.player.playbackStateChanged.disconnect(connection_state)
            self.player.mediaStatusChanged.disconnect(connection_status)

        except Exception as e:
            logging.error("[Web TTS] Error playing audio: %s", e)
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