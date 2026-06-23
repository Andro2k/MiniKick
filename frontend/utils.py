# frontend/utils.py

import logging
import os
import sys
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QImage, QPainterPath
logger = logging.getLogger("minikick.utils")

def resource_path(relative_path: str) -> str:
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

def _resolve_icon_path(name: str) -> str | None:
    full_path = get_assets_path(os.path.join("icons", name))
    if not os.path.exists(full_path):
        logger.warning(f"No se encontró el archivo de ícono: '{name}' en {full_path}")
        return None
    return full_path

def get_icon(name: str) -> QIcon:
    full_path = _resolve_icon_path(name)
    return QIcon(full_path) if full_path else QIcon()

def get_icon_colored(name: str, color_str: str, size: int = 24) -> QIcon:
    full_path = _resolve_icon_path(name)
    if not full_path:
        return QIcon()
    pixmap = QPixmap(full_path)
    if size:
        pixmap = pixmap.scaled(
            size, size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
    colored_pixmap = QPixmap(pixmap.size())
    colored_pixmap.fill(Qt.GlobalColor.transparent) 
    painter = QPainter(colored_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), QColor(color_str))
    painter.end()
    return QIcon(colored_pixmap)

def create_circular_pixmap(img_data: QByteArray) -> QPixmap:
    image = QImage.fromData(img_data)   
    if image.isNull():
        return QPixmap()
    size = min(image.width(), image.height())
    image = image.scaled(
        size, size, 
        Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
        Qt.TransformationMode.SmoothTransformation
    )
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