# resources\tools\project_architecture_boundary_auditor.py\

import ast
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Set

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

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
    "scratch", "node_modules", "tools", "tests"
}

EXEMPT_FILES: Dict[str, Set[str]] = {
    "banned_json_import": {
        os.path.normpath("backend/utils/json_utils.py")
    }
}

@dataclass
class ArchitectureViolation:
    file_path: str
    line: int
    col: int
    rule_id: str
    rule_category: str
    message: str
    code_snippet: str


class ArchitectureASTVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str, source_lines: List[str]):
        self.rel_path = rel_path.replace("\\", "/")
        self.source_lines = source_lines
        self.violations: List[ArchitectureViolation] = []
        self._imported_sleep_func = False

        self.is_frontend = self.rel_path.startswith("frontend/")
        self.is_backend = self.rel_path.startswith("backend/")
        self.is_backend_service = self.rel_path.startswith("backend/services/")
        self.is_backend_db = self.rel_path.startswith("backend/database/")
        self.is_backend_worker = self.rel_path.startswith("backend/workers/")
        self.is_controller = self.rel_path.startswith("backend/controllers/")

    def _get_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    def _add_violation(self, node: ast.AST, rule_id: str, category: str, message: str):
        lineno = getattr(node, "lineno", 1)
        col_offset = getattr(node, "col_offset", 0)
        self.violations.append(
            ArchitectureViolation(
                file_path=self.rel_path,
                line=lineno,
                col=col_offset,
                rule_id=rule_id,
                rule_category=category,
                message=message,
                code_snippet=self._get_snippet(lineno)
            )
        )

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.name

            if self.is_frontend:
                if name == "sqlite3" or name.startswith("sqlite3."):
                    self._add_violation(
                        node, "SOR_UI_DB", "Separation of Responsibilities",
                        "Acceso directo a 'sqlite3' desde la interfaz. La UI debe interactuar exclusivamente vía controladores/servicios."
                    )
                elif name == "backend.database" or name.startswith("backend.database."):
                    self._add_violation(
                        node, "SOR_UI_DB", "Separation of Responsibilities",
                        "Importación directa de 'backend.database' desde la UI. El frontend debe desacoplarse de la capa de persistencia."
                    )

            if self.is_backend_db:
                if name.startswith(("PySide6", "PySide2", "PyQt6", "PyQt5")):
                    self._add_violation(
                        node, "SOR_DB_QT", "Decoupled Architecture",
                        f"Importación de Qt ('{name}') en la capa de base de datos. La persistencia debe ser 100% Python/SQLite pura."
                    )

            if self.is_backend_service or self.is_backend_worker:
                if "QtWidgets" in name:
                    self._add_violation(
                        node, "SOR_CORE_WIDGETS", "Presentation Decoupling",
                        f"Importación de componentes visuales ('{name}') en la lógica de negocio o workers. Los widgets pertenecen a frontend/."
                    )

            if self.is_backend_service or self.is_backend_db or self.is_backend_worker:
                if name == "frontend" or name.startswith("frontend."):
                    self._add_violation(
                        node, "INVERTED_DEPENDENCY", "Dependency Direction",
                        f"Dependencia invertida prohibida: '{name}' importado desde la capa central de negocio o workers."
                    )

            if name == "json" or name.startswith("json."):
                norm_rel = os.path.normpath(self.rel_path)
                if norm_rel not in EXEMPT_FILES.get("banned_json_import", set()):
                    self._add_violation(
                        node, "BANNED_JSON_IMPORT", "Project Policy",
                        "Uso de 'import json' directo. Utiliza 'from backend.utils import fast_loads, fast_dumps' para serialización acelerada."
                    )

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""

        if self.is_frontend:
            if mod == "sqlite3" or mod.startswith("sqlite3."):
                self._add_violation(
                    node, "SOR_UI_DB", "Separation of Responsibilities",
                    "Acceso directo a 'sqlite3' desde la interfaz. La UI debe interactuar exclusivamente vía controladores/servicios."
                )
            elif mod == "backend.database" or mod.startswith("backend.database."):
                self._add_violation(
                    node, "SOR_UI_DB", "Separation of Responsibilities",
                    "Importación directa de 'backend.database' desde la UI. El frontend debe desacoplarse de la capa de persistencia."
                )

        if self.is_backend_db:
            if mod.startswith(("PySide6", "PySide2", "PyQt6", "PyQt5")):
                self._add_violation(
                    node, "SOR_DB_QT", "Decoupled Architecture",
                    f"Importación de Qt ('{mod}') en la capa de base de datos. La persistencia debe ser 100% Python/SQLite pura."
                )

        if self.is_backend_service or self.is_backend_worker:
            if "QtWidgets" in mod:
                self._add_violation(
                    node, "SOR_CORE_WIDGETS", "Presentation Decoupling",
                    f"Importación de componentes visuales ('{mod}') en la lógica de negocio o workers. Los widgets pertenecen a frontend/."
                )

        if self.is_backend_service or self.is_backend_db or self.is_backend_worker:
            if mod == "frontend" or mod.startswith("frontend."):
                self._add_violation(
                    node, "INVERTED_DEPENDENCY", "Dependency Direction",
                    f"Dependencia invertida prohibida: '{mod}' importado desde la capa central de negocio o workers."
                )

        if mod == "json" or mod.startswith("json."):
            norm_rel = os.path.normpath(self.rel_path)
            if norm_rel not in EXEMPT_FILES.get("banned_json_import", set()):
                self._add_violation(
                    node, "BANNED_JSON_IMPORT", "Project Policy",
                    "Uso de 'from json import ...' directo. Utiliza 'from backend.utils import fast_loads, fast_dumps'."
                )

        if (self.is_frontend or self.is_controller) and mod == "time":
            for alias in node.names:
                if alias.name == "sleep":
                    self._imported_sleep_func = True

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self._add_violation(
                node, "BANNED_PRINT", "Clean Code & Logging",
                "Llamada a 'print()' en código de producción. Utiliza el logger estructurado vía 'logger = logging.getLogger(...) / logger.info()'."
            )

        if self.is_frontend or self.is_controller:
            is_time_sleep = (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "sleep"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "time"
            )
            is_direct_sleep = (
                self._imported_sleep_func
                and isinstance(node.func, ast.Name)
                and node.func.id == "sleep"
            )

            if is_time_sleep or is_direct_sleep:
                self._add_violation(
                    node, "BLOCKING_SLEEP", "UI Thread Responsiveness",
                    "Llamada bloqueante a 'sleep()' en capa de UI o Controladores. Puede congelar el hilo principal Qt; utiliza QTimer o tareas asíncronas."
                )

        self.generic_visit(node)


def audit_architecture_boundaries() -> List[ArchitectureViolation]:
    violations: List[ArchitectureViolation] = []
    target_dirs = [BACKEND_DIR, FRONTEND_DIR]

    for base_dir in target_dirs:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
            for file in files:
                if not file.endswith(".py"):
                    continue

                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, PROJECT_ROOT)

                try:
                    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                        source = f.read()
                    lines = source.splitlines()
                    tree = ast.parse(source, filename=rel_path)
                    visitor = ArchitectureASTVisitor(rel_path, lines)
                    visitor.visit(tree)
                    violations.extend(visitor.violations)
                except Exception as ex:
                    print(f"{COLOR_YELLOW}⚠️ Error analizando {rel_path}: {ex}{COLOR_RESET}", file=sys.stderr)

    return violations


def print_report(violations: List[ArchitectureViolation]):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}    MINIKICK - AUDITOR DE ARQUITECTURA Y FRONTERAS DE CAPA (SoR)     {COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}\n")

    if not violations:
        print(f"{COLOR_GREEN}{COLOR_BOLD}✅ ¡EXCELENTE! Cero violaciones arquitectónicas o dependencias prohibidas.{COLOR_RESET}")
        print(f"{COLOR_GRAY}Todas las capas (UI, Controladores, Servicios, BD) respetan estrictamente sus fronteras.{COLOR_RESET}\n")
        return

    print(f"{COLOR_BOLD}{COLOR_RED}⚠️ Se detectaron {len(violations)} violaciones arquitectónicas / de estilo:{COLOR_RESET}\n")
    for v in violations:
        print(f"  • {COLOR_BOLD}{v.file_path}:{v.line}{COLOR_RESET} [{COLOR_YELLOW}{v.rule_id}{COLOR_RESET}] - {v.rule_category}")
        print(f"    Detalle: {COLOR_RED}{v.message}{COLOR_RESET}")
        print(f"    Código:  {COLOR_GRAY}{v.code_snippet}{COLOR_RESET}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Audita dependencias y límites de arquitectura entre frontend, controladores y backend.")
    parser.add_argument("--json", action="store_true", help="Exportar violaciones en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Terminar con código 1 si se detecta cualquier violación")
    parser.add_argument("--check", "-c", action="store_true", help="Modo verificación rápida para CI / Suite de Salud")

    args = parser.parse_args()
    violations = audit_architecture_boundaries()

    if args.json:
        data = {
            "summary": {
                "total_violations": len(violations),
                "is_clean": len(violations) == 0
            },
            "violations": [
                {
                    "file": v.file_path,
                    "line": v.line,
                    "col": v.col,
                    "rule_id": v.rule_id,
                    "category": v.rule_category,
                    "message": v.message,
                    "snippet": v.code_snippet
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
