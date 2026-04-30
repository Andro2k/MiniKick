# frontend/utils.py
# ─────────────────────────────────────────────
# Utilidades para manejo de rutas e íconos SVG.
# ─────────────────────────────────────────────
import os
import sys
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QImage, QPainterPath

def resource_path(relative_path: str) -> str:
    """
    Obtiene la ruta absoluta al recurso. 
    Compatible con el empaquetado de PyInstaller (sys._MEIPASS).
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        # Asume que utils.py está en /frontend, por lo que subimos un nivel a la raíz
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_assets_path(subfolder: str = "") -> str:
    """Devuelve la ruta hacia la carpeta de assets/ o una subcarpeta."""
    path = resource_path("assets")
    if subfolder:
        path = os.path.join(path, subfolder)
    return os.path.normpath(path).replace("\\", "/")

def get_icon(name: str) -> QIcon:
    """
    Carga un ícono SVG tal cual está, sin alterar sus colores.
    """
    full_path = resource_path(os.path.join("assets", "icons", name))
    if not os.path.exists(full_path):
        print(f"[-] Advertencia: No se encontró el ícono '{name}' en {full_path}")
        return QIcon()
        
    return QIcon(full_path)

def get_icon_colored(name: str, color_str: str, size: int = 24) -> QIcon:
    """
    Carga un ícono SVG y lo repinta completamente del color especificado.
    Ideal para adaptar los íconos al tema claro/oscuro o estados (hover, active).
    """
    full_path = resource_path(os.path.join("assets", "icons", name))
    
    if not os.path.exists(full_path):
        print(f"[-] Advertencia: No se encontró el ícono '{name}' en {full_path}")
        return QIcon()

    # Cargamos el SVG original en un Pixmap
    pixmap = QPixmap(full_path)
    
    # Lo escalamos con suavizado para evitar bordes pixelados
    if size:
        pixmap = pixmap.scaled(
            size, size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
    
    # Creamos un lienzo transparente del mismo tamaño
    colored_pixmap = QPixmap(pixmap.size())
    colored_pixmap.fill(Qt.GlobalColor.transparent)
    
    # Inicializamos el pintor
    painter = QPainter(colored_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Dibujamos el ícono original
    painter.drawPixmap(0, 0, pixmap)
    
    # Usamos el modo SourceIn: El nuevo color solo pintará donde el ícono original no sea transparente
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), QColor(color_str))
    painter.end()
    
    return QIcon(colored_pixmap)

def create_circular_pixmap(img_data: QByteArray) -> QPixmap:
    """
    Toma los datos crudos de una imagen y devuelve un QPixmap circular
    con antialiasing, listo para la interfaz.
    """
    image = QImage.fromData(img_data)
    
    if image.isNull():
        return QPixmap()

    # Asegurar un cuadrado perfecto
    size = min(image.width(), image.height())
    image = image.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    
    out_img = QImage(size, size, QImage.Format.Format_ARGB32)
    out_img.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(out_img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    
    painter.drawImage(0, 0, image)
    painter.end()
    return QPixmap.fromImage(out_img)