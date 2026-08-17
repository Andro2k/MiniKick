# frontend\widgets\scalable_illustration.py

import os
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

class ScalableIllustration(QLabel):
    _aspect_ratio_cache: dict[str, float] = {}

    def __init__(self, icon_path: str, aspect_ratio: float = 1.0, 
                 min_size: int = 120, max_size: int = 280, size_offset: int = 180, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.min_size = min_size
        self.max_size = max_size
        self.size_offset = size_offset
        self.aspect_ratio = self._detect_aspect_ratio(aspect_ratio)
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(False)
        
        if not os.path.exists(self.icon_path):
            self.setHidden(True)
        else:
            self._render_illustration(self.min_size)

    def _detect_aspect_ratio(self, fallback: float) -> float:
        if self.icon_path in ScalableIllustration._aspect_ratio_cache:
            return ScalableIllustration._aspect_ratio_cache[self.icon_path]

        if not os.path.exists(self.icon_path):
            return fallback

        try:
            if self.icon_path.lower().endswith(".svg"):
                renderer = QSvgRenderer(self.icon_path)
                if renderer.isValid():
                    sz = renderer.defaultSize()
                    if sz.width() > 0 and sz.height() > 0:
                        ratio = sz.height() / sz.width()
                        ScalableIllustration._aspect_ratio_cache[self.icon_path] = ratio
                        return ratio
            
            pix = QPixmap(self.icon_path)
            if not pix.isNull() and pix.width() > 0:
                ratio = pix.height() / pix.width()
                ScalableIllustration._aspect_ratio_cache[self.icon_path] = ratio
                return ratio
        except Exception:
            pass

        ScalableIllustration._aspect_ratio_cache[self.icon_path] = fallback
        return fallback

    def _render_illustration(self, target_width: int):
        width_size = max(self.min_size, min(target_width, self.max_size))
        height_size = int(width_size * self.aspect_ratio)

        dpr = self.devicePixelRatio()
        pixel_w = int(width_size * dpr)
        pixel_h = int(height_size * dpr)

        if self.icon_path.lower().endswith(".svg"):
            renderer = QSvgRenderer(self.icon_path)
            if renderer.isValid():
                pixmap = QPixmap(QSize(pixel_w, pixel_h))
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                renderer.render(painter)
                painter.end()
                pixmap.setDevicePixelRatio(dpr)
                self.setPixmap(pixmap)
                self.setFixedSize(width_size, height_size)
                self._current_target_width = width_size
                return

        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                QSize(pixel_w, pixel_h),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            scaled_pixmap.setDevicePixelRatio(dpr)
            self.setPixmap(scaled_pixmap)
            self.setFixedSize(width_size, height_size)
            self._current_target_width = width_size

    def update_image(self, container_height: int):
        if not os.path.exists(self.icon_path):
            self.setHidden(True)
            return
            
        width_size = min(max(container_height - self.size_offset, self.min_size), self.max_size)

        if hasattr(self, "_current_target_width") and abs(self._current_target_width - width_size) < 4:
            return
            
        self._render_illustration(width_size)
        self.setHidden(False)
