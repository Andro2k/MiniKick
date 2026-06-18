# backend/services/media_trigger_service.py

import os
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject

class MediaTriggerService(QObject):
    """Capa de Servicio encargada exclusivamente de la reproducción multimedia (Alta Cohesión)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

    def play_file(self, file_path: str, volume: float = 1.0):
        """Reproduce un archivo local basado en parámetros inyectados."""
        if not file_path or not os.path.exists(file_path):
            print(f"Archivo multimedia no encontrado o vacío: {file_path}")
            return
            
        self.audio_output.setVolume(volume)
        self.player.setSource(QUrl.fromLocalFile(os.path.abspath(file_path)))
        self.player.play()