# frontend\common\utils.py

import logging
import os
import sys
from functools import lru_cache
from PySide6.QtWidgets import QComboBox, QSlider
from PySide6.QtCore import Qt, QByteArray, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QImage, QPainterPath
from PySide6.QtSvg import QSvgRenderer
logger = logging.getLogger("minikick.utils")

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

@lru_cache(maxsize=64)
def _load_svg_raw(full_path: str) -> str:
    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

@lru_cache(maxsize=64)
def get_icon(name: str) -> QIcon:
    full_path = _resolve_icon_path(name)
    return QIcon(full_path) if full_path else QIcon()

@lru_cache(maxsize=256)
def _get_icon_colored_impl(name: str, color_str: str, size: int, dpr: float) -> QIcon:
    full_path = _resolve_icon_path(name)
    if not full_path:
        return QIcon()

    logical_size = size if size else 24
    physical_size = int(logical_size * dpr)

    try:
        raw_xml = _load_svg_raw(full_path)
        colorized_xml = raw_xml.replace("currentColor", color_str)
        renderer = QSvgRenderer(QByteArray(colorized_xml.encode("utf-8")))
        
        colored_pixmap = QPixmap(physical_size, physical_size)
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter, QRectF(0, 0, physical_size, physical_size))
        painter.end()
        
        if logical_size > 0:
            colored_pixmap.setDevicePixelRatio(colored_pixmap.width() / logical_size)
        else:
            colored_pixmap.setDevicePixelRatio(dpr)
            
        return QIcon(colored_pixmap)
    except Exception as e:
        logger.exception(f"Error renderizando icono coloreado {name}: {e}")
        return QIcon()

def _get_default_dpr() -> float:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        active_win = app.activeWindow()
        if active_win:
            return active_win.devicePixelRatio()
        screen = app.primaryScreen()
        if screen:
            return screen.devicePixelRatio()
    return 1.0

def get_icon_colored(name: str, color_str: str, size: int = 24, dpr: float | None = None) -> QIcon:
    if dpr is None:
        dpr = _get_default_dpr()
    return _get_icon_colored_impl(name, color_str, size, dpr)

def get_pixmap_colored(name: str, color_str: str, size: int = 24, dpr: float | None = None) -> QPixmap:
    if dpr is None:
        dpr = _get_default_dpr()
    icon = get_icon_colored(name, color_str, size, dpr)
    from PySide6.QtCore import QSize
    return icon.pixmap(QSize(size, size), dpr)

def get_pixmap(name: str, size: int, dpr: float | None = None) -> QPixmap:
    if dpr is None:
        dpr = _get_default_dpr()
    icon = get_icon(name)
    from PySide6.QtCore import QSize
    return icon.pixmap(QSize(size, size), dpr)

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
    
class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)

class NoWheelSlider(QSlider):
    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)

def validate_trigger_prefix(text: str) -> bool:
    return not text.strip() or text.startswith("!")
