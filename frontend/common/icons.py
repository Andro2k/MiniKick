# frontend\common\icons.py

import logging
import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path
from PySide6.QtCore import Qt, QByteArray, QRectF, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QImage, QPainterPath
from PySide6.QtSvg import QSvgRenderer

from backend.utils import resource_path

logger = logging.getLogger("minikick.icons")
_QSS_ICON_CACHE_DIR = Path(tempfile.gettempdir()) / "minikick_qss_icons"


def get_assets_path(subfolder: str = "") -> str:
    path = resource_path("assets")
    if subfolder:
        path = os.path.join(path, subfolder)
    return os.path.normpath(path).replace("\\", "/")


def resolve_icon_path(name: str) -> str | None:
    if not name:
        return None
    if os.path.isabs(name) and os.path.exists(name):
        return name
    base_candidate = os.path.basename(name)
    full_path = get_assets_path(os.path.join("icons", base_candidate))
    if os.path.exists(full_path):
        return full_path
    direct_path = get_assets_path(name)
    if os.path.exists(direct_path):
        return direct_path
    logger.warning("Icon file not found: '%s' in %s", name, full_path)
    return None


def _default_icon_color() -> str:
    from .theme import Palette
    return Palette.NEUTRAL_050


@lru_cache(maxsize=128)
def _load_svg_raw(full_path: str) -> str:
    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _colorize_svg(svg_xml: str, color: str, force_explicit: bool = False) -> str:
    svg_xml = svg_xml.replace("currentColor", color)
    if force_explicit:
        svg_xml = re.sub(r'stroke=["\'](?!none)[^"\']+["\']', f'stroke="{color}"', svg_xml)
        svg_xml = re.sub(r'fill=["\'](?!none)[^"\']+["\']', f'fill="{color}"', svg_xml)
    return svg_xml


@lru_cache(maxsize=128)
def get_qss_colored_icon(icon_name_or_rel_path: str, color_hex: str | None = None) -> str:
    clean_name = os.path.basename(icon_name_or_rel_path)
    original_path = resolve_icon_path(clean_name)
    if not original_path or not os.path.exists(original_path):
        original_path = get_assets_path(icon_name_or_rel_path)
        if not os.path.exists(original_path):
            return ""

    color = _default_icon_color() if color_hex is None else color_hex
    try:
        _QSS_ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cached_file = _QSS_ICON_CACHE_DIR / f"{Path(clean_name).stem}_{color.lstrip('#')}.svg"
        if not cached_file.exists():
            svg_xml = _colorize_svg(_load_svg_raw(original_path), color, force_explicit=True)
            cached_file.write_text(svg_xml, encoding="utf-8")
        return str(cached_file).replace("\\", "/")
    except OSError as exc:
        logger.warning("Unable to cache QSS icon '%s': %s", icon_name_or_rel_path, exc)
        return get_assets_path(icon_name_or_rel_path)


@lru_cache(maxsize=128)
def get_icon(name: str) -> QIcon:
    full_path = resolve_icon_path(name)
    return QIcon(full_path) if full_path else QIcon()

@lru_cache(maxsize=256)
def _get_icon_colored_impl(name: str, color_str: str, size: int, dpr: float) -> QIcon:
    full_path = resolve_icon_path(name)
    if not full_path:
        return QIcon()

    logical_size = size if size else 16
    physical_size = int(logical_size * dpr)

    try:
        raw_xml = _load_svg_raw(full_path)
        colorized_xml = _colorize_svg(raw_xml, color_str)
        renderer = QSvgRenderer(QByteArray(colorized_xml.encode("utf-8")))

        colored_pixmap = QPixmap(physical_size, physical_size)
        colored_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter, QRectF(0, 0, physical_size, physical_size))
        painter.end()

        colored_pixmap.setDevicePixelRatio(colored_pixmap.width() / logical_size)
        return QIcon(colored_pixmap)
    except Exception as e:
        logger.exception("Error rendering colored icon '%s': %s", name, e)
        return QIcon()

def _resolve_dpr(dpr: float | None) -> float:
    if dpr is not None:
        return dpr
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

def _get_colored_icon(name: str, color_str: str | None, size: int, dpr: float | None) -> tuple[QIcon, float]:
    color = _default_icon_color() if color_str is None else color_str
    resolved_dpr = _resolve_dpr(dpr)
    return _get_icon_colored_impl(name, color, size, resolved_dpr), resolved_dpr


def get_icon_colored(name: str, color_str: str | None = None, size: int = 16, dpr: float | None = None) -> QIcon:
    icon, _ = _get_colored_icon(name, color_str, size, dpr)
    return icon

def get_pixmap_colored(name: str, color_str: str | None = None, size: int = 16, dpr: float | None = None) -> QPixmap:
    icon, resolved_dpr = _get_colored_icon(name, color_str, size, dpr)
    return icon.pixmap(QSize(size, size), resolved_dpr)

def create_circular_pixmap(img_data: QByteArray, target_size: int | None = None) -> QPixmap:
    image = QImage.fromData(img_data)
    if image.isNull():
        return QPixmap()
    size = min(image.width(), image.height())
    if target_size and target_size > 0 and size > target_size:
        size = target_size
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
