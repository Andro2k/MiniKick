# frontend\widgets\draggable_component.py

import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint, Signal, QUrl
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class DraggableBox(QFrame):
    position_updated = Signal(int, int)

    def __init__(self, parent, canvas_w: int, canvas_h: int, scale_factor_obs: float, filepath: str, scale_val: float):
        super().__init__(parent)
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.scale_factor = scale_factor_obs 
        self.base_scale_val = scale_val
        self._target_local_pos = QPoint(0, 0)
        
        self.setFixedSize(100, 100)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        self._drag_active = False
        self._drag_offset = QPoint()

        self.media_layout = QVBoxLayout(self)
        self.media_layout.setContentsMargins(2, 2, 2, 2)
        
        if filepath and os.path.exists(filepath):
            ext = filepath.lower()
            if ext.endswith(('.mp4', '.webm')):
                self.video_widget = QVideoWidget()
                self.video_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self.media_layout.addWidget(self.video_widget)

                self.player = QMediaPlayer(self)
                self.audio = QAudioOutput(self)
                self.audio.setVolume(0.0) 
                
                self.player.setAudioOutput(self.audio)
                self.player.setVideoOutput(self.video_widget)
                self.player.setSource(QUrl.fromLocalFile(filepath))
                self.player.setLoops(QMediaPlayer.Loops.Infinite)
                
                self.video_widget.videoSink().videoSizeChanged.connect(self._adjust_to_media_size)
                self.player.play()
                
            elif ext.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.img_lbl = QLabel()
                self.img_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self.img_lbl.setScaledContents(True)
                pixmap = QPixmap(filepath)
                self.img_lbl.setPixmap(pixmap)
                self.media_layout.addWidget(self.img_lbl)
                self._adjust_to_media_size(pixmap.size())

    def _clamp_position(self, x: int, y: int) -> tuple[int, int]:
        if self.width() <= self.canvas_w:
            min_x = 0
            max_x = self.canvas_w - self.width()
        else:
            min_x = self.canvas_w - self.width()
            max_x = 0
            
        if self.height() <= self.canvas_h:
            min_y = 0
            max_y = self.canvas_h - self.height()
        else:
            min_y = self.canvas_h - self.height()
            max_y = 0
            
        return max(min_x, min(x, max_x)), max(min_y, min(y, max_y))

    def _adjust_to_media_size(self, size=None):
        if size is None or type(size) == bool or not getattr(size, 'isValid', lambda: False)():
            if hasattr(self, 'video_widget') and self.video_widget.videoSink():
                size = self.video_widget.videoSink().videoSize()

        if not size or not getattr(size, 'isValid', lambda: False)() or size.width() == 0:
            return

        obs_w = size.width() * self.base_scale_val
        obs_h = size.height() * self.base_scale_val

        local_w = int(obs_w / self.scale_factor)
        local_h = int(obs_h / self.scale_factor)

        self.setFixedSize(local_w, local_h)
        
        target_x = self._target_local_pos.x() if hasattr(self, '_target_local_pos') else self.x()
        target_y = self._target_local_pos.y() if hasattr(self, '_target_local_pos') else self.y()
        
        x, y = self._clamp_position(target_x, target_y)
        self.move(x, y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_offset = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_active:
            new_pos = self.mapToParent(event.pos()) - self._drag_offset
            x, y = self._clamp_position(new_pos.x(), new_pos.y())
            self.move(x, y)
            self._target_local_pos = QPoint(x, y)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_active = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        obs_x, obs_y = self.get_obs_coordinates()
        self.position_updated.emit(obs_x, obs_y)

    def get_obs_coordinates(self) -> tuple[int, int]:
        return int(self.x() * self.scale_factor), int(self.y() * self.scale_factor)

    def set_obs_coordinates(self, obs_x: int, obs_y: int):
        local_x = int(obs_x / self.scale_factor)
        local_y = int(obs_y / self.scale_factor)
        self._target_local_pos = QPoint(local_x, local_y)
        local_x, local_y = self._clamp_position(local_x, local_y)
        self.move(local_x, local_y)