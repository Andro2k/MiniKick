# backend\providers\voices\tts_local.py

import logging
import sys
import pyttsx3
import threading

def _init_com():
    if sys.platform == "win32":
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

def _uninit_com():
    if sys.platform == "win32":
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass

class LocalTTSProvider:
    _lock = threading.Lock()

    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None
        self._engine = None

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def set_speed(self, speed: float) -> None:
        factor = speed if speed <= 3.0 else (speed / 100.0)
        self.rate = max(50, min(400, int(150 * factor)))

    def prepare(self, text: str, voice_id: str = None) -> None:
        pass

    def speak(self, text: str, voice_id: str = None) -> None:
        if not text:
            return
        target_voice = voice_id if voice_id else self.voice_id
        with self._lock:
            engine = None
            try:
                _init_com()
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                if target_voice:
                    try:
                        engine.setProperty("voice", target_voice)
                    except Exception as ve:
                        logging.warning("[Local TTS] Could not set voice %s: %s", target_voice, ve)
                    
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logging.error("[Local TTS] Speech error: %s", e)
            finally:
                if engine is not None:
                    try:
                        engine.stop()
                    except Exception:
                        pass
                    try:
                        del engine
                    except Exception:
                        pass
                _uninit_com()

    def stop(self) -> None:
        pass

    def warm_up(self, voice_id: str = None) -> None:
        pass

    def get_available_voices(self) -> list[dict]:
        with self._lock:
            engine = None
            try:
                _init_com()
                engine = pyttsx3.init()
                voices = [{"id": v.id, "name": v.name.split(" - ")[0]} for v in engine.getProperty('voices')]
                return voices
            except Exception as e:
                logging.error("[Local TTS] Error fetching local voices: %s", e)
                return [{"id": "default", "name": "System Voice (Default)"}]
            finally:
                if engine is not None:
                    try:
                        del engine
                    except Exception:
                        pass
                _uninit_com()
