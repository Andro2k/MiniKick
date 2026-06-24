# backend/TTS/web_tts.py

import asyncio
import os
import tempfile
import edge_tts
import pygame
from backend.interfaces.tts_interfaces import ITTSProvider

class WebTTSProvider(ITTSProvider):
    def __init__(self, voice: str = "es-ES-AlvaroNeural"):
        self.voice = voice
        self.volume_str = "+0%"
        pygame.mixer.init()

    def set_volume(self, volume: float) -> None:
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)
        percent = int((volume - 1.0) * 100)
        self.volume_str = f"{percent}%" if percent < 0 else f"+{percent}%"

    def speak(self, text: str) -> None:
        asyncio.run(self._async_speak(text))

    async def _async_speak(self, text: str) -> None:
        communicate = edge_tts.Communicate(text, self.voice, volume=self.volume_str)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
            
        try:
            await communicate.save(temp_path)
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"[Web TTS] Error playing audio: {e}")
        finally:
            pygame.mixer.music.unload() 
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                pass

    def stop(self) -> None:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    def get_available_voices(self) -> list[dict]:
        try:
            voices = asyncio.run(edge_tts.list_voices())
            return [{"id": v["ShortName"], "name": v["FriendlyName"]} for v in voices if "es-" in v["Locale"]]
        except Exception as e:
            print(f"[Web TTS] Error connecting to Microsoft Edge: {e}")
            return [
                {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Spain) - Offline"},
                {"id": "es-ES-ElviraNeural", "name": "Elvira (Spain) - Offline"},
                {"id": "es-MX-JorgeNeural", "name": "Jorge (Mexico) - Offline"},
                {"id": "es-MX-DaliaNeural", "name": "Dalia (Mexico) - Offline"}
            ]