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
        
        # Inicializamos el mixer de audio al crear el proveedor (Alta Cohesión)
        pygame.mixer.init()

    def set_volume(self, volume: float) -> None:
        """Convierte el float (0.0 - 1.0) al formato relativo de edge-tts"""
        volume = max(0.0, min(1.0, volume))
        percent = int((volume - 1.0) * 100)
        
        if percent >= 0:
            self.volume_str = f"+{percent}%"
        else:
            self.volume_str = f"{percent}%"

    def speak(self, text: str) -> None:
        # Ejecuta el flujo asíncrono bloqueando este hilo específico del worker
        asyncio.run(self._async_speak(text))

    async def _async_speak(self, text: str) -> None:
        communicate = edge_tts.Communicate(text, self.voice, volume=self.volume_str)
        
        # 1. Crear un archivo temporal seguro para almacenar el MP3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
            
        try:
            # 2. Descargar y guardar el audio de la IA
            await communicate.save(temp_path)
            
            # 3. Cargar y reproducir el archivo
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            # 4. Esperar a que termine la reproducción (Bloqueante, pero necesario)
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
        except Exception as e:
            print(f"[Web TTS] Error reproduciendo audio: {e}")
            
        finally:
            # 5. Limpieza vitalicia (SoR)
            pygame.mixer.music.unload() # Liberar el control del archivo
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"[Web TTS] No se pudo borrar el temporal: {e}")

    def stop(self) -> None:
        """Detiene la reproducción en seco."""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()