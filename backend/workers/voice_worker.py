# backend\workers\voice_worker.py

from PySide6.QtCore import QThread, Signal

class VoiceFetcherWorker(QThread):
    voices_fetched = Signal(list, str)
    error_occurred = Signal(str, str)

    def __init__(self, tts_manager, provider_type: str, parent=None):
        super().__init__(parent)
        self.tts_manager = tts_manager
        self.provider_type = provider_type

    def run(self):
        try:
            voices = self.tts_manager.get_available_voices(self.provider_type)
            self.voices_fetched.emit(voices, self.provider_type)
        except Exception as e:
            self.error_occurred.emit(str(e), self.provider_type)
