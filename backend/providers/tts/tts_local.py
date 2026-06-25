# backend\providers\tts\tts_local.py

import pyttsx3
from backend.interfaces.tts_interfaces import ITTSProvider

class LocalTTSProvider(ITTSProvider):
    def __init__(self, rate: int = 150, initial_volume: float = 1.0):
        self.rate = rate
        self.volume = initial_volume
        self.voice_id = None

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def speak(self, text: str) -> None:
        try:
            import pythoncom
            pythoncom.CoInitialize()

            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice_id:
                engine.setProperty("voice", self.voice_id)
                
            engine.say(text)
            engine.runAndWait()

        except Exception as e:
            print(f"[Local TTS] Speech error: {e}")
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def stop(self) -> None:
        pass

    def get_available_voices(self) -> list[dict]:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            engine = pyttsx3.init()
            voices = [{"id": v.id, "name": v.name.split(" - ")[0]} for v in engine.getProperty('voices')]
            
            return voices
        except Exception as e:
            print(f"[Local TTS] Error fetching local voices: {e}")
            return [{"id": "default", "name": "System Voice (Default)"}]
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass