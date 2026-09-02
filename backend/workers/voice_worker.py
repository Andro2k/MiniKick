# backend\workers\voice_worker.py

import sys
import logging
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("minikick.workers.voice")

class VoiceFetcherWorker(QThread):
    voices_fetched = Signal(object, str)
    error_occurred = Signal(str, str)

    def __init__(self, tts_manager, provider_type: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Voice_Fetcher")
        self.tts_manager = tts_manager
        self.provider_type = provider_type

    def run(self):
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
        logger.debug("[VoiceFetcherWorker] Fetching available voices for provider: %s...", self.provider_type)
        try:
            voices = self.tts_manager.get_available_voices(self.provider_type)
            logger.debug("[VoiceFetcherWorker] Fetched %d voices for %s.", len(voices) if voices else 0, self.provider_type)
            self.voices_fetched.emit(voices, self.provider_type)
        except Exception as e:
            logger.error("[VoiceFetcherWorker] Error fetching voices for %s: %s", self.provider_type, e)
            self.error_occurred.emit(str(e), self.provider_type)
