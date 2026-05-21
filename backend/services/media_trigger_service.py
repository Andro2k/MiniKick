# backend/services/media_trigger_service.py

import os
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject

class MediaTriggerService(QObject):
    """Capa de Servicio encargada exclusivamente de la reproducción de alertas (TriggerFire)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        
        # Mapeo de Recompensas -> Rutas de archivos locales (Sonidos o Videos)
        # Ajusta los nombres exactos de tus recompensas de Kick aquí
        self.trigger_mapping = {
            "Susto": "assets/sounds/susto.mp3",
            "Hidratarse": "assets/sounds/water_drop.mp3",
            "Aplausos": "assets/sounds/applause.wav"
        }

    def play_reward_alert(self, reward_title: str):
        """Busca si la recompensa tiene un trigger multimedia asociado y lo reproduce."""
        if reward_title not in self.trigger_mapping:
            print(f"⚠️ Recompensa '{reward_title}' recibida pero no tiene alerta multimedia asignada.")
            return
            
        file_path = self.trigger_mapping[reward_title]
        
        if not os.path.exists(file_path):
            print(f"❌ Archivo multimedia no encontrado: {file_path}")
            return
            
        # Cargar y reproducir el archivo de manera asíncrona (No bloquea la UI)
        self.player.setSource(QUrl.fromLocalFile(os.path.abspath(file_path)))
        self.audio_output.setVolume(0.8) # 80% de volumen por defecto
        self.player.play()
        print(f"🔊 Reproduciendo alerta para la recompensa: {reward_title}")