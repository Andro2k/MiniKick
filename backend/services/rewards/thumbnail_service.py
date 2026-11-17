# backend\services\rewards\thumbnail_service.py
"""Genera miniaturas para archivos multimedia."""

import os
import logging
from PySide6.QtCore import QBuffer, QIODevice, Qt, QUrl, QEventLoop, QTimer
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink

logger = logging.getLogger("minikick.rewards.thumbnail")

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv"}
_VIDEO_FRAME_TIMEOUT_MS = 3000

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
            frame = _capture_video_frame(filepath)
            if frame is not None:
                return _encode_png(frame, max_size)
        except Exception as e:
            logger.warning("Error generating video thumbnail for %s: %s", filepath, e)
            
    return None


def _encode_png(img: QImage, max_size: int) -> bytes:
    scaled = img.scaled(max_size, max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    scaled.save(buffer, "PNG")
    return bytes(buffer.data())


def _capture_video_frame(filepath: str) -> QImage | None:
    """Captura un fotograma con un reproductor silenciado; registra estado y error de Qt si falla."""
    player = QMediaPlayer()
    audio = QAudioOutput()
    audio.setVolume(0.0)
    player.setAudioOutput(audio)
    sink = QVideoSink()
    player.setVideoSink(sink)

    captured: list[QImage] = []
    errors: list[str] = []
    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def on_frame_changed(frame):
        if captured or not frame.isValid():
            return
        img = frame.toImage()
        if not img.isNull():
            captured.append(img)
            loop.quit()

    def on_status_changed(status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            player.setPosition(500)
            player.play()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            loop.quit()

    def on_error(_code, message):
        errors.append(message)
        loop.quit()

    sink.videoFrameChanged.connect(on_frame_changed)
    player.mediaStatusChanged.connect(on_status_changed)
    player.errorOccurred.connect(on_error)
    player.setSource(QUrl.fromLocalFile(filepath))

    timeout.start(_VIDEO_FRAME_TIMEOUT_MS)
    loop.exec()
    timeout.stop()
    status_name = player.mediaStatus().name
    player.stop()
    player.setVideoSink(None)
    player.setAudioOutput(None)

    if not captured:
        logger.warning("No video frame captured for thumbnail: %s (status=%s, error=%s)",
                       filepath, status_name, errors[0] if errors else "-")
        return None
    return captured[0]
