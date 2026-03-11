# backend/services/tts_worker.py

import os
import warnings
# Ocultar el mensaje de bienvenida de pygame en la consola
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import queue
import re
import time
import asyncio
import io 
from contextlib import suppress

import pyttsx3
import edge_tts
import pygame

from PyQt6.QtCore import QThread, pyqtSignal

class TTSWorker(QThread):
    """
    Motor de Texto a Voz (TTS) que procesa una cola de mensajes en segundo plano.
    Utiliza Edge-TTS (voces neuronales de alta calidad) por defecto, 
    con fallback a pyttsx3 (voces locales offline) en caso de error.
    """
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.is_running = True

        # --- Configuración General ---
        self.engine_type = "edge-tts"
        self.volume = 1.0 
        self.rate = 175

        # --- Motores y Voces ---
        self.edge_voice = "es-MX-JorgeNeural"
        self.backup_engine = None
        self.selected_voice_id = None
        self.loop = None 

        # Regex para limpiar texto (HTML y enlaces)
        self.re_html = re.compile(r'<[^>]+>')
        self.re_url = re.compile(r'http\S+|www\.\S+')

    def add_message(self, text: str):
        """Añade un mensaje a la cola después de limpiarlo."""
        clean_text = self._clean_text(text)
        if clean_text:
            self.queue.put(clean_text)

    def stop(self):
        """Detiene el hilo completamente (al cerrar el programa)."""
        self.is_running = False
        self.immediate_stop()
        self.quit()
        self.wait(1500)

    def immediate_stop(self):
        """Limpia la cola y corta la reproducción actual instantáneamente (Botón de Skip)."""
        with self.queue.mutex:
            self.queue.queue.clear()           
        
        # Detener audio de Pygame (Edge-TTS)
        with suppress(Exception):
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                
        # Detener audio local (Pyttsx3)
        with suppress(Exception):
            if self.backup_engine:
                self.backup_engine.stop()

    def run(self):
        """Bucle principal del hilo que procesa la cola de mensajes."""
        self._init_audio_engines()
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        while self.is_running:
            try:
                # El timeout permite que el bucle se destrabe y compruebe `is_running`
                text = self.queue.get(timeout=0.5) 
                self._speak(text)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.error_signal.emit(f"TTS Error general: {e}")

        self._cleanup_resources()

    def _init_audio_engines(self):
        """Inicializa los motores de audio al arrancar el hilo."""
        with suppress(Exception):
            # Inicializamos pygame mixer optimizado para voz humana (24kHz, mono)
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
        
        with suppress(Exception):
            # Inicializamos el motor offline
            self.backup_engine = pyttsx3.init()

    def _cleanup_resources(self):
        """Cierra los bucles y libera la tarjeta de sonido al apagar."""
        if self.loop and not self.loop.is_closed():
            try:
                tasks = asyncio.all_tasks(self.loop)
                for t in tasks: 
                    t.cancel()
                self.loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                self.loop.close()
            except Exception: 
                pass
                
        with suppress(Exception):
            if pygame.mixer.get_init(): 
                pygame.mixer.quit()

    def _clean_text(self, text: str) -> str:
        """Elimina etiquetas HTML y reemplaza URLs para evitar que el bot lea texto basura."""
        text_no_html = self.re_html.sub('', text)
        return self.re_url.sub('un enlace', text_no_html).strip()

    def _speak(self, text: str):
        """Enruta el texto al motor de voz seleccionado."""
        if self.engine_type == "edge-tts":
            self._speak_edge(text)
        else:
            self._speak_pyttsx3(text)

    # --- LÓGICA DE EDGE-TTS (Voz Neuronal en la nube) ---

    def _speak_edge(self, text: str):
        """Descarga el audio de Edge y lo reproduce con Pygame."""
        try:
            if not self.loop or self.loop.is_closed(): 
                return
                
            audio_bytes = self.loop.run_until_complete(self._get_edge_bytes(text))
            if not audio_bytes: 
                raise Exception("No se generó audio (bytes vacíos).")

            audio_stream = io.BytesIO(audio_bytes)
            pygame.mixer.music.load(audio_stream)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()

            # Esperamos activamente a que termine, pero permitiendo cancelarlo (skip)
            while pygame.mixer.music.get_busy() and self.is_running:
                time.sleep(0.05)
                
        except Exception as e:
            self.error_signal.emit(f"Edge-TTS falló, usando voz local: {e}")
            self._speak_pyttsx3(text)
        finally:
            with suppress(Exception): 
                pygame.mixer.music.unload()

    async def _get_edge_bytes(self, text: str) -> bytes:
        """Petición asíncrona a Microsoft Edge TTS."""
        # Convertimos la velocidad base (175) a porcentaje (+0%, +20%, etc.)
        percent = int((self.rate - 175) / 1.5)
        percent = max(-50, min(80, percent)) 
        rate_str = f"{percent:+d}%"
        
        communicate = edge_tts.Communicate(text, self.edge_voice, rate=rate_str)
        audio_data = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
                
        return bytes(audio_data)

    # --- LÓGICA DE PYTTSX3 (Voz Robótica Offline) ---

    def _speak_pyttsx3(self, text: str):
        """Reproduce el texto usando las voces instaladas en Windows/Mac/Linux."""
        if not self.backup_engine:
            return
            
        with suppress(Exception):
            if self.selected_voice_id: 
                self.backup_engine.setProperty('voice', self.selected_voice_id)
            self.backup_engine.setProperty('rate', self.rate)
            self.backup_engine.setProperty('volume', self.volume)
            
            self.backup_engine.say(text)
            self.backup_engine.runAndWait()