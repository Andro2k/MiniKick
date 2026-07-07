# frontend/widgets/scalable_illustration.py

import os
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class ScalableIllustration(QLabel):
    def __init__(self, icon_path: str, aspect_ratio: float = 1.0, 
                 min_size: int = 120, max_size: int = 300, size_offset: int = 220, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.aspect_ratio = aspect_ratio
        self.min_size = min_size
        self.max_size = max_size
        self.size_offset = size_offset
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)
        
        if not os.path.exists(self.icon_path):
            self.setHidden(True)
        else:
            icon = QIcon(self.icon_path)
            self.setPixmap(icon.pixmap(self.min_size, int(self.min_size * self.aspect_ratio)))
            self.setFixedSize(self.min_size, int(self.min_size * self.aspect_ratio))

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
