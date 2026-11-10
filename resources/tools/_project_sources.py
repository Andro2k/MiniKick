# resources\tools\_project_sources.py

import subprocess
from pathlib import Path
from typing import List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IGNORED_DIRS = {
    ".venv", "venv", "__pycache__", ".git", ".pytest_cache",
    ".agents", "build", "dist", "walkthroughs", "locales",
    "scratch", "node_modules", ".idea", ".vscode"
}

ROOT_ZONE = "."
KNOWN_ZONES = ("backend", "frontend", "bootstrap", "resources")
APPLICATION_ZONES = ("backend", "frontend", "bootstrap", ROOT_ZONE)


def _git_python_files() -> Optional[List[str]]:
    """Archivos .py versionados y nuevos sin versionar (respeta .gitignore), según el árbol de trabajo actual."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.py"],
            cwd=PROJECT_ROOT, capture_output=True, check=True, timeout=15
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    listed = [p for p in out.decode("utf-8", errors="replace").split("\0") if p]
    return listed or None


def _walk_python_files() -> List[str]:
    return [p.relative_to(PROJECT_ROOT).as_posix() for p in PROJECT_ROOT.rglob("*.py")]


def iter_python_files(zones: Optional[Sequence[str]] = None) -> List[Path]:
    """Todos los .py del proyecto (rutas absolutas). `zones` filtra por carpeta de primer nivel; ROOT_ZONE ('.') son los módulos de la raíz."""
    candidates = _git_python_files() or _walk_python_files()
    result: List[Path] = []
    for rel in sorted(set(candidates)):
        parts = Path(rel).parts
        if any(part in IGNORED_DIRS for part in parts[:-1]):
            continue
        zone = parts[0] if len(parts) > 1 else ROOT_ZONE
        if zones is not None and zone not in zones:
            continue
        path = PROJECT_ROOT / rel
        if path.is_file():
            result.append(path)
    return result


def unclassified_zones() -> dict:
    """Carpetas de primer nivel con .py que ninguna zona conocida cubre: {carpeta: cantidad de archivos}."""
    counts: dict = {}
    for path in iter_python_files():
        zone = path.relative_to(PROJECT_ROOT).parts[0] if len(path.relative_to(PROJECT_ROOT).parts) > 1 else ROOT_ZONE
        if zone != ROOT_ZONE and zone not in KNOWN_ZONES:
            counts[zone] = counts.get(zone, 0) + 1
    return counts
