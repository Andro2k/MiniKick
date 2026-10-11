# backend\utils\paths.py

import os
import sys


def resource_path(relative_path: str) -> str:
    """Ruta a un recurso empaquetado (PyInstaller) o del proyecto, sin depender del directorio de trabajo."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)
