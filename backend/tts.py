import pyttsx3, queue

class TTSManager:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.queue = queue.Queue()

    def speak_next(self):
        try:
            text = self.queue.get(timeout=0.5)
            # Re-inicialización preventiva si el motor se bloquea
            self.engine.say(text)
            self.engine.runAndWait()
            self.queue.task_done()
        except queue.Empty:
            pass
        except Exception as e:
            print(f"[*] Error TTS: {e}. Reiniciando motor...")
            self.engine = pyttsx3.init()