# frontend\common\paths.py

import logging
import os
import sys

logger = logging.getLogger("minikick.paths")

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

def resolve_icon_path(name: str) -> str | None:
    full_path = get_assets_path(os.path.join("icons", name))
    if not os.path.exists(full_path):
        logger.warning(f"No se encontró el archivo de ícono: '{name}' en {full_path}")
        return None
    return full_path
