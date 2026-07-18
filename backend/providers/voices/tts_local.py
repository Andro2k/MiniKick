# backend\providers\voices\tts_local.py

import logging
import pyttsx3
import threading

class LocalTTSProvider:
    _lock = threading.Lock()

    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None
        self._engine = None

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def prepare(self, text: str, voice_id: str = None) -> None:
        pass

    def speak(self, text: str) -> None:
        with self._lock:
            try:
                if not self._engine:
                    import pythoncom
                    pythoncom.CoInitialize()
                    self._engine = pyttsx3.init()
                
                self._engine.setProperty("rate", self.rate)
                self._engine.setProperty("volume", self.volume)
                if self.voice_id:
                    self._engine.setProperty("voice", self.voice_id)
                    
                self._engine.say(text)
                self._engine.runAndWait()

            except Exception as e:
                logging.error("[Local TTS] Speech error: %s", e)

    def stop(self) -> None:
        pass

    def get_available_voices(self) -> list[dict]:
        with self._lock:
            engine = None
            try:
                import pythoncom
                pythoncom.CoInitialize()
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
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
