# frontend/utils.py

import sys
import os
import cv2
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPainterPath, QImage
from PyQt6.QtCore import Qt, QRunnable, pyqtSignal, QObject

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_assets_path(subfolder: str = "") -> str:
    path = resource_path("assets")
    if subfolder:
        path = os.path.join(path, subfolder)
    return os.path.normpath(path).replace("\\", "/")

def get_icon(name):
    full_path = resource_path(os.path.join("assets", "icons", name))
    return QIcon(full_path)

def get_icon_colored(name, color_str, size=24):
    full_path = resource_path(os.path.join("assets", "icons", name))
    pixmap = QPixmap(full_path)
    if pixmap.isNull():
        return QIcon()
    if size:
        pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    colored_pixmap = QPixmap(pixmap.size())
    colored_pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(colored_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), QColor(color_str))
    painter.end()
    
    return QIcon(colored_pixmap)

# --- SISTEMA DE MINIATURAS PARA VIDEOS ---

def get_video_thumbnail(file_path, width=160):
    """Extrae el primer frame de un video y devuelve un QPixmap."""
    if not os.path.exists(file_path):
        return None

    try:
        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            return pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
            
    except Exception as e:
        print(f"Error generando thumbnail para {file_path}: {e}")
    
    return None

class WorkerSignals(QObject):
    finished = pyqtSignal(object)

class ThumbnailWorker(QRunnable):
    """Hilo secundario para no congelar la UI al procesar el video."""
    def __init__(self, path, width):
        super().__init__()
        self.path = path
        self.width = width
        self.signals = WorkerSignals()

    def run(self):
        pixmap = get_video_thumbnail(self.path, self.width)
        self.signals.finished.emit(pixmap)