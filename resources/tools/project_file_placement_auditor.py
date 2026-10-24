# resources/tools/project_file_placement_auditor.py

import fnmatch
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

COLOR_RESET  = "\033[0m"
COLOR_BOLD   = "\033[1m"
COLOR_GREEN  = "\033[92m"
COLOR_RED    = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN   = "\033[96m"
COLOR_GRAY   = "\033[90m"

IGNORED_DIRECTORIES = {
    ".venv", "venv", "__pycache__", ".git", ".pytest_cache",
    ".agents", "build", "dist", "walkthroughs", "locales",
    "scratch", "node_modules", "tools", "tests", "assets"
}


@dataclass
class PlacementViolation:
    file_path: str
    rule_id: str
    rule_category: str
    message: str
    expected_location: str


FOLDER_PURITY_RULES: Dict[str, List[str]] = {
    "backend/workers": ["*_worker.py", "__init__.py"],
    "backend/controllers": ["*_controller.py", "__init__.py"],
    "backend/database": ["*_storage.py", "database_manager.py", "migrations.py", "__init__.py"],
    "frontend/views": ["*_view.py", "__init__.py"],
}

REVERSE_PLACEMENT_RULES: Dict[str, str] = {
    "*_worker.py": "backend/workers",
    "*_controller.py": "backend/controllers",
    "*_storage.py": "backend/database",
    "*_view.py": "frontend/views",
}


def audit_file_placements() -> List[PlacementViolation]:
    violations: List[PlacementViolation] = []

    for folder_rel, allowed_patterns in FOLDER_PURITY_RULES.items():
        folder_abs = os.path.join(PROJECT_ROOT, os.path.normpath(folder_rel))
        if not os.path.exists(folder_abs):
            continue

        for item in os.listdir(folder_abs):
            item_path = os.path.join(folder_abs, item)
            if not os.path.isfile(item_path) or not item.endswith(".py"):
                continue

            matches_any = any(fnmatch.fnmatch(item, pat) for pat in allowed_patterns)
            if not matches_any:
                rel_file = os.path.relpath(item_path, PROJECT_ROOT).replace("\\", "/")
                violations.append(
                    PlacementViolation(
                        file_path=rel_file,
                        rule_id="FOLDER_PURITY_VIOLATION",
                        rule_category="Directory Purity & SRP",
                        message=f"Archivo '{item}' no cumple la convención canónica de '{folder_rel}'. Patrones admitidos: {allowed_patterns}.",
                        expected_location=folder_rel
                    )
                )

    backend_abs = os.path.join(PROJECT_ROOT, "backend")
    frontend_abs = os.path.join(PROJECT_ROOT, "frontend")

    for scan_root in [backend_abs, frontend_abs]:
        for root, dirs, files in os.walk(scan_root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
            for file in files:
                if not file.endswith(".py"):
                    continue

                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, PROJECT_ROOT).replace("\\", "/")
                parent_rel = os.path.relpath(root, PROJECT_ROOT).replace("\\", "/")

                for pat, expected_folder in REVERSE_PLACEMENT_RULES.items():
                    if fnmatch.fnmatch(file, pat):
                        if parent_rel != expected_folder:
                            violations.append(
                                PlacementViolation(
                                    file_path=rel_file,
                                    rule_id="MISPLACED_CANONICAL_FILE",
                                    rule_category="File Placement & Convention",
                                    message=f"Archivo '{file}' con patrón '{pat}' se encuentra en '{parent_rel}' en lugar de '{expected_folder}'.",
                                    expected_location=expected_folder
                                )
                            )
                if rel_file.startswith("backend/"):
                    is_util = fnmatch.fnmatch(file, "*util*.py") or fnmatch.fnmatch(file, "*helper*.py")
                    if is_util and parent_rel != "backend/utils":
                        violations.append(
                            PlacementViolation(
                                file_path=rel_file,
                                rule_id="SCATTERED_BACKEND_UTIL",
                                rule_category="Utility Centralization",
                                message=f"Archivo de utilidad '{file}' disperso en '{parent_rel}'. Todas las utilidades del backend deben centralizarse en 'backend/utils/'.",
                                expected_location="backend/utils"
                            )
                        )

    return violations


def print_report(violations: List[PlacementViolation]):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}  MINIKICK - AUDITOR DE UBICACIÓN Y NOMENCLATURA DE ARCHIVOS (SRP)    {COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}\n")

    if not violations:
        print(f"{COLOR_GREEN}{COLOR_BOLD}✅ ¡EXCELENTE! Cero archivos fuera de lugar o con nomenclatura errónea.{COLOR_RESET}")
        print(f"{COLOR_GRAY}Todas las carpetas de workers, controladores, vistas y utilidades cumplen las normas canónicas.{COLOR_RESET}\n")
        return

    print(f"{COLOR_BOLD}{COLOR_RED}⚠️ Se detectaron {len(violations)} inconsistencias de ubicación o convención:{COLOR_RESET}\n")
    for v in violations:
        print(f"  • {COLOR_BOLD}{v.file_path}{COLOR_RESET} [{COLOR_YELLOW}{v.rule_id}{COLOR_RESET}]")
        print(f"    Categoría:  {v.rule_category}")
        print(f"    Detalle:    {COLOR_RED}{v.message}{COLOR_RESET}")
        print(f"    Ubicación:  {COLOR_CYAN}{v.expected_location}{COLOR_RESET}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Audita ubicación y nombres canónicos de archivos del backend y frontend.")
    parser.add_argument("--json", action="store_true", help="Exportar violaciones en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Terminar con código 1 si se detecta cualquier inconsistencia")
    parser.add_argument("--check", "-c", action="store_true", help="Modo verificación rápida para CI / Suite de Salud")

    args = parser.parse_args()
    violations = audit_file_placements()

    if args.json:
        data = {
            "summary": {
                "total_violations": len(violations),
                "is_clean": len(violations) == 0
            },
            "violations": [
                {
                    "file": v.file_path,
                    "rule_id": v.rule_id,
                    "category": v.rule_category,
                    "message": v.message,
                    "expected_location": v.expected_location
                }
                for v in violations
            ]
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_report(violations)

    if (args.strict or args.check) and violations:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
