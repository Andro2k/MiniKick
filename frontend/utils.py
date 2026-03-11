# frontend/utils.py

import sys
import os
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPainterPath, QImage
from PyQt6.QtCore import Qt, QRunnable, pyqtSignal, QObject

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

def get_assets_path(subfolder: str = "") -> str:
    """
    Devuelve la ruta absoluta a la carpeta 'assets' (o subcarpeta).
    """
    path = resource_path("assets")
    
    if subfolder:
        path = os.path.join(path, subfolder)
    
    return os.path.normpath(path).replace("\\", "/")

def get_icon(name):
    full_path = resource_path(os.path.join("assets", "icons", name))
    return QIcon(full_path)

def get_icon_colored(name, color_str, size=24):
    """
    Carga un SVG, lo pinta de color y maneja errores si el archivo no existe.
    """
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

def get_rounded_pixmap(pixmap: QPixmap, radius: int = 0, is_circle: bool = False) -> QPixmap:
    """
    Recorta un QPixmap en forma de círculo o rectángulo redondeado.
    """
    if pixmap.isNull(): 
        return pixmap
        
    size = pixmap.size()
    result = QPixmap(size)
    result.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    
    path = QPainterPath()
    if is_circle:
        s = min(size.width(), size.height())
        path.addEllipse(0, 0, s, s)
    else:
        path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
        
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    
    return result

def crop_to_square(pixmap: QPixmap, size: int) -> QPixmap:
    """Escala y recorta la imagen al centro para que sea un cuadrado perfecto."""
    return pixmap.scaled(
        size, size, 
        Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
        Qt.TransformationMode.SmoothTransformation
    )

# def get_video_thumbnail(file_path, width=300):
#     """
#     Extrae el primer frame de un video y devuelve un QPixmap.
#     """
#     if not os.path.exists(file_path):
#         return None

#     try:
#         cap = cv2.VideoCapture(file_path)
#         ret, frame = cap.read()
#         cap.release()

#         if ret:
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             h, w, ch = frame.shape
#             bytes_per_line = ch * w
#             qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
#             pixmap = QPixmap.fromImage(qimg)
#             return pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
            
#     except Exception as e:
#         print(f"Error generando thumbnail para {file_path}: {e}")
    
#     return None

class WorkerSignals(QObject):
    finished = pyqtSignal(object)

# class ThumbnailWorker(QRunnable):
#     def __init__(self, path, width):
#         super().__init__()
#         self.path = path
#         self.width = width
#         self.signals = WorkerSignals()

#     def run(self):
#         pixmap = get_video_thumbnail(self.path, self.width)
#         self.signals.finished.emit(pixmap)