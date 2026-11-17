# resources\tests\test_installer_script_paths.py
"""Pruebas de las rutas del script de Inno Setup y del gestor de compilación."""

import os
import re

from resources.tools import build_manager

_PATH_DIRECTIVES = ("SetupIconFile", "LicenseFile", "WizardImageFile", "WizardSmallImageFile")


def _resolve(script_dir: str, raw_path: str) -> str:
    """Resuelve una ruta de Inno Setup (separador \\) respecto a la carpeta del script."""
    return os.path.normpath(os.path.join(script_dir, raw_path.strip().replace("\\", "/")))


def test_build_manager_points_to_existing_inno_script():
    assert os.path.isfile(build_manager.INNO_SETUP_PATH)


def test_inno_static_files_exist_relative_to_script():
    script = build_manager.INNO_SETUP_PATH
    script_dir = os.path.dirname(script)
    with open(script, "r", encoding="utf-8") as f:
        content = f.read()

    for directive in _PATH_DIRECTIVES:
        match = re.search(rf"^{directive}=(.+)$", content, re.MULTILINE)
        assert match, f"Falta la directiva {directive} en instalador.iss"
        path = _resolve(script_dir, match.group(1))
        assert os.path.isfile(path), f"{directive} apunta a un archivo inexistente: {path}"


def test_inno_output_dir_matches_build_manager_expectation():
    script_dir = os.path.dirname(build_manager.INNO_SETUP_PATH)
    with open(build_manager.INNO_SETUP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"^OutputDir=(.+)$", content, re.MULTILINE)
    assert match
    output_dir = _resolve(script_dir, match.group(1))
    assert output_dir == os.path.join(build_manager.BASE_DIR, "Output")
