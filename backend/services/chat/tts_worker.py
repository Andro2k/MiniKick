# backend/services/chat/tts_worker.py

import os
import warnings
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
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.is_running = True

        self.engine_type = "edge-tts"
        self.volume = 1.0 

        self.current_engine = None 
        self.selected_voice_id = None
        self.rate = 175

        self.edge_voice = "es-MX-JorgeNeural"
        self.loop = None 

        with suppress(Exception):
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)

        self.re_html = re.compile(r'<[^>]+>')
        self.re_url = re.compile(r'http\S+|www\.\S+')

    def add_message(self, text: str):
        if clean_text := self._clean_text(text): 
            self.queue.put(clean_text)

    def stop(self):
        self.is_running = False
        self.immediate_stop()
        self.quit()
        self.wait(1500)

    def immediate_stop(self):
        with self.queue.mutex:
            self.queue.queue.clear()           
        with suppress(Exception):
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

    def run(self):
        with suppress(Exception):
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
            self.backup_engine = pyttsx3.init()

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        while self.is_running:
            try:
                text = self.queue.get(timeout=0.5) 
                self._speak(text)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.error_signal.emit(f"TTS Error: {e}")

        self._cleanup_loop()

    def _cleanup_loop(self):
        if self.loop and not self.loop.is_closed():
            try:
                tasks = asyncio.all_tasks(self.loop)
                for t in tasks: t.cancel()
                self.loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                self.loop.close()
            except: pass
                
        with suppress(Exception):
            if pygame.mixer.get_init(): pygame.mixer.quit()

    def _clean_text(self, text: str) -> str:
        text_no_html = self.re_html.sub('', text)
        return self.re_url.sub('un enlace', text_no_html).strip()

    def _speak(self, text: str):
        if self.engine_type == "edge-tts":
            self._speak_edge(text)
        else:
            self._speak_pyttsx3(text)

    def _speak_edge(self, text: str):
        try:
            if not self.loop or self.loop.is_closed(): return
            audio_bytes = self.loop.run_until_complete(self._get_edge_bytes(text))
            if not audio_bytes: raise Exception("No se generó audio")

            audio_stream = io.BytesIO(audio_bytes)
            pygame.mixer.music.load(audio_stream)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy() and self.is_running:
                time.sleep(0.05)
                
        except Exception as e:
            self.error_signal.emit(f"Edge-TTS falló, usando voz local: {e}")
            self._speak_pyttsx3(text)
        finally:
            with suppress(Exception): pygame.mixer.music.unload()

    async def _get_edge_bytes(self, text: str) -> bytes:
        percent = int((self.rate - 175) / 1.5)
        percent = max(-50, min(80, percent)) 
        rate_str = f"{percent:+d}%"
        communicate = edge_tts.Communicate(text, self.edge_voice, rate=rate_str)
        audio_data = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
                
        return bytes(audio_data)

    def _speak_pyttsx3(self, text: str):
        with suppress(Exception):
            if self.selected_voice_id: self.backup_engine.setProperty('voice', self.selected_voice_id)
            self.backup_engine.setProperty('rate', self.rate)
            self.backup_engine.setProperty('volume', self.volume)
            self.backup_engine.say(text)
            self.backup_engine.runAndWait()
        with suppress(Exception):
            if self.backup_engine: self.backup_engine.stop()