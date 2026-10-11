# frontend\common\paths.py

import logging
import os
from backend.utils.paths import resource_path

from backend.utils.paths import resource_path  # reexportado: la implementación vive en el backend

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
