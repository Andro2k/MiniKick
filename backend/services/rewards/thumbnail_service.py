# backend\services\rewards\thumbnail_service.py

import os
import logging
from PySide6.QtCore import QBuffer, QIODevice, Qt, QUrl, QEventLoop, QTimer
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink

logger = logging.getLogger("minikick.rewards.thumbnail")

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv"}

def generate_media_thumbnail(filepath: str, max_size: int = 128) -> bytes | None:
    if not filepath or not os.path.isfile(filepath):
        return None
        
    ext = os.path.splitext(filepath)[1].lower()
    if ext in AUDIO_EXTENSIONS:
        return None
        
    if ext in IMAGE_EXTENSIONS:
        try:
            img = QImage(filepath)
            if not img.isNull():
                scaled = img.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                scaled.save(buffer, "PNG")
                return bytes(buffer.data())
        except Exception as e:
            logger.warning("Error reading image thumbnail for %s: %s", filepath, e)
        return None

    if ext in VIDEO_EXTENSIONS:
        try:
            player = QMediaPlayer()
            sink = QVideoSink()
            player.setVideoSink(sink)
            
            captured = [None]
            loop = QEventLoop()
            
            def on_frame_changed(frame):
                if not captured[0] and frame.isValid():
                    captured[0] = frame.toImage()
                    loop.quit()
                    
            sink.videoFrameChanged.connect(on_frame_changed)
            player.setSource(QUrl.fromLocalFile(filepath))
            player.setPosition(500)
            player.play()
            
            QTimer.singleShot(1500, loop.quit)
            loop.exec()
            player.stop()
            
            if captured[0] and not captured[0].isNull():
                scaled = captured[0].scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                scaled.save(buffer, "PNG")
                return bytes(buffer.data())
        except Exception as e:
            logger.warning("Error generating video thumbnail for %s: %s", filepath, e)
            
    return None
