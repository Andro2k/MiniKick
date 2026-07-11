# frontend\widgets\scalable_illustration.py

import os
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class ScalableIllustration(QLabel):
    def __init__(self, icon_path: str, aspect_ratio: float = 1.0, 
                 min_size: int = 120, max_size: int = 300, size_offset: int = 220, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.min_size = min_size
        self.max_size = max_size
        self.size_offset = size_offset
        self.aspect_ratio = self._detect_aspect_ratio(aspect_ratio)
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)
        
        if not os.path.exists(self.icon_path):
            self.setHidden(True)
        else:
            icon = QIcon(self.icon_path)
            self.setPixmap(icon.pixmap(self.min_size, int(self.min_size * self.aspect_ratio)))
            self.setFixedSize(self.min_size, int(self.min_size * self.aspect_ratio))

    def _detect_aspect_ratio(self, fallback: float) -> float:
        if not os.path.exists(self.icon_path):
            return fallback
        try:
            import re
            with open(self.icon_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2048)
            
            viewbox_match = re.search(
                r'viewBox\s*=\s*["\']\s*([0-9.-]+)\s+([0-9.-]+)\s+([0-9.-]+)\s+([0-9.-]+)\s*["\']', 
                content, re.IGNORECASE
            )
            if viewbox_match:
                vb_w = float(viewbox_match.group(3))
                vb_h = float(viewbox_match.group(4))
                if vb_w > 0:
                    return vb_h / vb_w

            width_match = re.search(r'width\s*=\s*["\']\s*([0-9.]+)(?:px)?\s*["\']', content, re.IGNORECASE)
            height_match = re.search(r'height\s*=\s*["\']\s*([0-9.]+)(?:px)?\s*["\']', content, re.IGNORECASE)
            if width_match and height_match:
                w = float(width_match.group(1))
                h = float(height_match.group(1))
                if w > 0:
                    return h / w
        except Exception:
            pass
        return fallback

    def update_image(self, container_height: int):
        if not os.path.exists(self.icon_path):
            self.setHidden(True)
            return
            
        width_size = min(max(container_height - self.size_offset, self.min_size), self.max_size)
        height_size = int(width_size * self.aspect_ratio)
        
        icon = QIcon(self.icon_path)
        self.setPixmap(icon.pixmap(width_size, height_size))
        self.setFixedSize(width_size, height_size)
        self.setHidden(False)
