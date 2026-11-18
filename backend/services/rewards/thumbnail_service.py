# backend\services\rewards\thumbnail_service.py
"""Genera miniaturas para archivos multimedia."""

import os
import logging
from collections import deque
from PySide6.QtCore import QBuffer, QIODevice, QObject, Qt, QUrl, QEventLoop, QTimer, Signal
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


class ThumbnailBatchGenerator(QObject):
    """Genera miniaturas en lote sin bloquear la UI: un solo reproductor reutilizado y sin bucles de eventos anidados."""

    progress = Signal(int, int)
    finished = Signal(dict)

    def __init__(self, filepaths, max_size: int = 128, parent=None):
        super().__init__(parent)
        self._queue = deque(dict.fromkeys(filepaths))
        self._total = len(self._queue)
        self._max_size = max_size
        self._results: dict[str, bytes | None] = {}
        self._current: str | None = None
        self._player = None
        self._sink = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

    def start(self) -> None:
        logger.info("[ThumbnailBatch] Start: %d files", self._total)
        QTimer.singleShot(0, self._next)

    def _next(self) -> None:
        while self._queue:
            path = self._queue.popleft()
            if os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS and os.path.isfile(path):
                self._start_video(path)
                return
            self._store(path, self._safe_static_thumbnail(path))
        self._finish()

    @staticmethod
    def _safe_static_thumbnail(path: str) -> bytes | None:
        try:
            return generate_media_thumbnail(path)
        except Exception:
            logger.exception("[ThumbnailBatch] Static thumbnail failed: %s", path)
            return None

    def _store(self, path: str, thumb: bytes | None) -> None:
        self._results[path] = thumb
        self.progress.emit(len(self._results), self._total)

    def _ensure_player(self) -> None:
        if self._player is not None:
            return
        self._player = QMediaPlayer(self)
        # Sin QAudioOutput a propósito: un fotograma no necesita audio y evita depender del dispositivo de sonido.
        self._sink = QVideoSink(self)
        self._player.setVideoSink(self._sink)
        self._sink.videoFrameChanged.connect(self._on_frame)
        self._player.mediaStatusChanged.connect(self._on_status)
        self._player.errorOccurred.connect(self._on_error)

    def _start_video(self, path: str) -> None:
        logger.info("[ThumbnailBatch] Video %d/%d: %s", len(self._results) + 1, self._total, path)
        self._current = path
        try:
            self._ensure_player()
            self._player.setSource(QUrl.fromLocalFile(path))
            self._timer.start(_VIDEO_FRAME_TIMEOUT_MS)
        except Exception:
            logger.exception("[ThumbnailBatch] Could not start player for %s", path)
            self._complete(None)

    def _on_status(self, status) -> None:
        if self._current is None:
            return
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self._player.setPosition(500)
            self._player.play()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            logger.warning("[ThumbnailBatch] Invalid media: %s", self._current)
            self._complete(None)

    def _on_frame(self, frame) -> None:
        if self._current is None or not frame.isValid():
            return
        img = frame.toImage()
        if img.isNull():
            return
        try:
            thumb = _encode_png(img, self._max_size)
        except Exception:
            logger.exception("[ThumbnailBatch] Encoding failed: %s", self._current)
            thumb = None
        self._complete(thumb)

    def _on_error(self, _code, message) -> None:
        if self._current is not None:
            logger.warning("[ThumbnailBatch] Player error for %s: %s", self._current, message)
            self._complete(None)

    def _on_timeout(self) -> None:
        if self._current is not None:
            logger.warning("[ThumbnailBatch] Timeout waiting for frame: %s", self._current)
            self._complete(None)

    def _complete(self, thumb: bytes | None) -> None:
        path, self._current = self._current, None
        self._timer.stop()
        try:
            self._player.stop()
            self._player.setSource(QUrl())
        except Exception:
            logger.exception("[ThumbnailBatch] Player reset failed")
        self._store(path, thumb)
        QTimer.singleShot(0, self._next)

    def _finish(self) -> None:
        if self._player is not None:
            self._player.stop()
            self._player.setVideoSink(None)
            self._player.deleteLater()
            self._sink.deleteLater()
            self._player = self._sink = None
        ok = sum(1 for t in self._results.values() if t)
        logger.info("[ThumbnailBatch] Done: %d/%d with thumbnail", ok, self._total)
        self.finished.emit(self._results)

