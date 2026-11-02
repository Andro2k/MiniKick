# resources\tools\project_dead_code_auditor.py\

import argparse
import ast
import contextlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_SCOPES = ["frontend", "backend", "bootstrap", "resources"]

IGNORED_DIRS = {
    ".venv", "venv", "__pycache__", ".git", ".pytest_cache",
    ".agents", "build", "dist", "walkthroughs", "locales",
    "scratch", "node_modules", ".idea", ".vscode"
}

ENTRY_POINT_PATTERNS = re.compile(
    r"^(main|app|run|conftest|setup)\.py$|^resources[/\\](tools|tests)[/\\].+\.py$|^tests[/\\].+\.py$",
    re.IGNORECASE,
)

QT_AND_MAGIC_WHITELIST = {
    "__init__", "__post_init__", "__str__", "__repr__", "__call__",
    "__enter__", "__exit__", "__iter__", "__next__", "__getitem__",
    "__setitem__", "__delitem__", "__len__", "__contains__", "__eq__",
    "__hash__", "__del__", "__new__", "__bool__",
    "paintEvent", "resizeEvent", "eventFilter", "viewportEvent",
    "mousePressEvent", "mouseReleaseEvent", "mouseDoubleClickEvent", "mouseMoveEvent",
    "keyPressEvent", "keyReleaseEvent", "wheelEvent", "leaveEvent", "enterEvent",
    "focusInEvent", "focusOutEvent", "changeEvent", "closeEvent", "showEvent", "hideEvent",
    "contextMenuEvent", "dragEnterEvent", "dragMoveEvent", "dragLeaveEvent", "dropEvent",
    "startDrag", "mimeData", "dropMimeData", "supportedDropActions",
    "sizeHint", "minimumSizeHint", "initStyleOption", "setEditorData", "setModelData",
    "updateEditorGeometry", "createEditor", "displayText",
    "setup_method", "teardown_method", "setUp", "tearDown", "setUpClass", "tearDownClass",
}

@dataclass(slots=True)
class SymbolDef:
    name: str
    kind: str
    file_path: Path
    line: int
    parent_class: Optional[str] = None

@dataclass(slots=True)
class UnusedImportDef:
    file_path: Path
    line: int
    imported_name: str
    module_source: str

@dataclass(slots=True)
class OrphanFileDef:
    file_path: Path
    module_name: str
    size_bytes: int
    lines_count: int
    imported_only_by_self_package: bool = False

@dataclass
class AuditReport:
    total_files_scanned: int = 0
    orphan_files: List[OrphanFileDef] = field(default_factory=list)
    unused_symbols: List[SymbolDef] = field(default_factory=list)
    unused_imports: List[UnusedImportDef] = field(default_factory=list)

class FileASTVisitor(ast.NodeVisitor):
    def __init__(self, scanner: "DeadCodeScanner", file_path: Path):
        self.scanner = scanner
        self.file_path = file_path
        self.class_stack: List[str] = []
        self.local_names: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        self.local_names.add(node.id)
        self.scanner.global_referenced_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.local_names.add(node.attr)
        self.scanner.global_referenced_names.add(node.attr)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.scanner.symbols_by_file[self.file_path].append(
            SymbolDef(node.name, "class", self.file_path, node.lineno)
        )
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        kind = "method" if self.class_stack else "function"
        parent = self.class_stack[-1] if self.class_stack else None
        self.scanner.symbols_by_file[self.file_path].append(
            SymbolDef(node.name, kind, self.file_path, node.lineno, parent)
        )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign):
        if not self.class_stack:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.scanner.symbols_by_file[self.file_path].append(
                        SymbolDef(target.id, "variable", self.file_path, node.lineno)
                    )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if not self.class_stack and isinstance(node.target, ast.Name):
            self.scanner.symbols_by_file[self.file_path].append(
                SymbolDef(node.target.id, "variable", self.file_path, node.lineno)
            )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            target = alias.name
            self.scanner.file_imports[self.file_path].add(target)
            imported_as = alias.asname or (target.split(".")[-1] if "." in target else target)
            self.scanner.imports_by_file[self.file_path].append(
                UnusedImportDef(self.file_path, node.lineno, imported_as, target)
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        resolved_mod = self.scanner._resolve_relative_import(self.file_path, node.module, node.level)
        if resolved_mod:
            self.scanner.file_imports[self.file_path].add(resolved_mod)
            for alias in node.names:
                self.scanner.file_imports[self.file_path].add(f"{resolved_mod}.{alias.name}")
                imported_as = alias.asname or alias.name
                self.scanner.imports_by_file[self.file_path].append(
                    UnusedImportDef(self.file_path, node.lineno, imported_as, resolved_mod)
                )
        self.generic_visit(node)

class DeadCodeScanner:
    def __init__(self, root_dir: Path, scopes: List[str]):
        self.root_dir = root_dir.resolve()
        self.scopes = scopes
        self.file_list: List[Path] = []
        self.module_to_file: Dict[str, Path] = {}
        self.file_to_module: Dict[Path, str] = {}

        self.file_imports: Dict[Path, Set[str]] = defaultdict(set)
        self.global_referenced_names: Set[str] = set()
        self.file_local_referenced_names: Dict[Path, Set[str]] = defaultdict(set)
        self.symbols_by_file: Dict[Path, List[SymbolDef]] = defaultdict(list)
        self.imports_by_file: Dict[Path, List[UnusedImportDef]] = defaultdict(list)
        self.package_inits: Dict[Path, Path] = {}

    def _is_entry_point(self, rel_path: str) -> bool:
        return bool(ENTRY_POINT_PATTERNS.search(rel_path.replace("\\", "/")))

    def collect_files(self) -> None:
        for item in self.root_dir.glob("*.py"):
            rel_path = item.relative_to(self.root_dir)
            self.file_list.append(item)
            mod_name = rel_path.with_suffix("").as_posix().replace("/", ".")
            self.module_to_file[mod_name] = item
            self.file_to_module[item] = mod_name

        for scope in self.scopes:
            target_dir = self.root_dir / scope
            if not target_dir.exists():
                continue
            for path in target_dir.rglob("*.py"):
                if any(part in IGNORED_DIRS for part in path.parts):
                    continue
                rel_path = path.relative_to(self.root_dir)
                rel_no_ext = rel_path.with_suffix("").as_posix().replace("/", ".")
                self.file_list.append(path)

                if path.name == "__init__.py":
                    pkg_name = rel_no_ext.rsplit(".__init__", 1)[0]
                    self.module_to_file[pkg_name] = path
                    self.module_to_file[rel_no_ext] = path
                    self.file_to_module[path] = pkg_name
                    self.package_inits[path.parent] = path
                else:
                    self.module_to_file[rel_no_ext] = path
                    self.file_to_module[path] = rel_no_ext

    def _resolve_relative_import(self, current_file: Path, module_str: Optional[str], level: int) -> Optional[str]:
        if level == 0 and module_str:
            return module_str
        cur_dir = current_file.parent
        for _ in range(level - 1):
            cur_dir = cur_dir.parent
        try:
            rel_to_root = cur_dir.relative_to(self.root_dir)
            pkg_base = rel_to_root.as_posix().replace("/", ".")
        except ValueError:
            pkg_base = ""

        if module_str:
            return f"{pkg_base}.{module_str}" if pkg_base and pkg_base != "." else module_str
        return pkg_base if pkg_base != "." else None

    def scan_all_ast(self) -> None:
        for file_path in self.file_list:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content, filename=str(file_path))
            except Exception:
                continue

            visitor = FileASTVisitor(self, file_path)
            visitor.visit(tree)
            self.file_local_referenced_names[file_path] = visitor.local_names

    def analyze(self) -> AuditReport:
        report = AuditReport(total_files_scanned=len(self.file_list))
        imported_modules_count: Dict[str, Set[Path]] = defaultdict(set)
        for importing_file, imported_set in self.file_imports.items():
            for imp in imported_set:
                imported_modules_count[imp].add(importing_file)

        for file_path in self.file_list:
            rel_path_str = file_path.relative_to(self.root_dir).as_posix()
            if self._is_entry_point(rel_path_str) or file_path.name == "__init__.py":
                continue

            mod_name = self.file_to_module.get(file_path, "")
            importers = {
                f for imp_name, files in imported_modules_count.items()
                if imp_name == mod_name or imp_name.startswith(f"{mod_name}.")
                for f in files
            }
            importers.discard(file_path)

            self_init = self.package_inits.get(file_path.parent)
            symbols_in_file = self.symbols_by_file.get(file_path, [])
            top_level_names = {s.name for s in symbols_in_file if s.kind in ("class", "function", "variable")}

            has_external_usage = any(
                name in self.global_referenced_names for name in top_level_names
            ) and any(
                name in other_names
                for other_file, other_names in self.file_local_referenced_names.items()
                if other_file not in (file_path, self_init)
                for name in top_level_names
            )

            is_orphan = False
            only_self_init = False

            if not importers and not has_external_usage:
                is_orphan = True
            elif len(importers) == 1 and self_init in importers and not has_external_usage:
                is_orphan = True
                only_self_init = True

            if is_orphan:
                try:
                    stat = file_path.stat()
                    lines = len(file_path.read_text(encoding="utf-8", errors="ignore").splitlines())
                    size, count = stat.st_size, lines
                except Exception:
                    size, count = 0, 0

                report.orphan_files.append(
                    OrphanFileDef(file_path, mod_name, size, count, only_self_init)
                )

        orphan_paths = {o.file_path for o in report.orphan_files}
        for file_path, symbols in self.symbols_by_file.items():
            rel_path_str = file_path.relative_to(self.root_dir).as_posix()
            if self._is_entry_point(rel_path_str) or file_path in orphan_paths:
                continue

            local_refs = self.file_local_referenced_names.get(file_path, set())
            for sym in symbols:
                if (
                    sym.name in QT_AND_MAGIC_WHITELIST
                    or sym.name.startswith(("test_", "_"))
                    or sym.kind not in ("class", "function")
                ):
                    continue

                if sym.name not in self.global_referenced_names and sym.name not in local_refs:
                    report.unused_symbols.append(sym)
                else:
                    referenced_outside = any(
                        sym.name in other_names
                        for other_file, other_names in self.file_local_referenced_names.items()
                        if other_file != file_path
                    )
                    if not referenced_outside and sym.name not in local_refs:
                        report.unused_symbols.append(sym)

        for file_path, imp_list in self.imports_by_file.items():
            if file_path.name == "__init__.py":
                continue
            local_names = self.file_local_referenced_names.get(file_path, set())
            for imp in imp_list:
                if imp.module_source != "__future__" and imp.imported_name not in local_names:
                    report.unused_imports.append(imp)

        return report

def run_vulture_audit(scopes: List[str], min_confidence: int = 80) -> int:
    print(f"\n🔍 [Vulture] Ejecutando análisis profundo (confianza >= {min_confidence}%)...")
    try:
        res = subprocess.run(
            ["uvx", "vulture", *scopes, f"--min-confidence={min_confidence}"],
            cwd=PROJECT_ROOT, text=True, capture_output=True
        )
        if res.stdout:
            print(res.stdout)
        if res.stderr and "Installed" not in res.stderr:
            print(res.stderr)
        return res.returncode
    except Exception as e:
        print(f"❌ Error al ejecutar uvx vulture: {e}")
        return 1

class DeadCodePresenter:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def print_report(cls, report: AuditReport, root_dir: Path, show_symbols=True, show_imports=True):
        print(f"\n{cls.BOLD}{cls.CYAN}{'='*68}\n 🧹 MiniKick - Dead Code & Orphan Manager (v1.6.0)\n{'='*68}{cls.RESET}")
        print(f"📁 Total archivos escaneados: {report.total_files_scanned}\n{'-'*68}")

        print(f"\n{cls.BOLD}{cls.RED}🚨 Archivos y Módulos Huérfanos ({len(report.orphan_files)} encontrados):{cls.RESET}")
        if not report.orphan_files:
            print(f"  {cls.GREEN}✅ Cero archivos huérfanos detectados. Estructura de módulos óptima.{cls.RESET}")
        for orphan in report.orphan_files:
            rel = orphan.file_path.relative_to(root_dir).as_posix()
            tag = f"{cls.YELLOW}[Solo importado en su __init__.py]{cls.RESET}" if orphan.imported_only_by_self_package else f"{cls.RED}[Sin referencias]{cls.RESET}"
            print(f"  • {cls.BOLD}{rel}{cls.RESET} ({orphan.lines_count} líneas, {orphan.size_bytes} bytes) {tag}")

        if show_symbols:
            print(f"\n{cls.BOLD}{cls.YELLOW}⚠️ Clases y Funciones Top-Level No Usadas ({len(report.unused_symbols)} encontradas):{cls.RESET}")
            if not report.unused_symbols:
                print(f"  {cls.GREEN}✅ Cero símbolos top-level huérfanos detectados.{cls.RESET}")
            for sym in report.unused_symbols[:30]:
                rel = sym.file_path.relative_to(root_dir).as_posix()
                print(f"  • {cls.BOLD}{sym.name}{cls.RESET} ({sym.kind}) -> {rel}:{sym.line}")
            if len(report.unused_symbols) > 30:
                print(f"  ... y {len(report.unused_symbols) - 30} más.")

        if show_imports:
            print(f"\n{cls.BOLD}{cls.BLUE}📦 Importaciones Innecesarias ({len(report.unused_imports)} encontradas):{cls.RESET}")
            if not report.unused_imports:
                print(f"  {cls.GREEN}✅ Todas las importaciones están siendo utilizadas.{cls.RESET}")
            for imp in report.unused_imports[:25]:
                rel = imp.file_path.relative_to(root_dir).as_posix()
                print(f"  • {cls.BOLD}{imp.imported_name}{cls.RESET} (de {imp.module_source}) -> {rel}:{imp.line}")
            if len(report.unused_imports) > 25:
                print(f"  ... y {len(report.unused_imports) - 25} más.")

        print(f"\n{'-'*68}\n{cls.BOLD}📊 Resumen de Salud del Código:{cls.RESET}")
        print(f"  - Archivos huérfanos: {len(report.orphan_files)}")
        print(f"  - Símbolos no usados: {len(report.unused_symbols)}")
        print(f"  - Imports innecesarios: {len(report.unused_imports)}\n{'-'*68}\n")

def clean_orphan_files(orphans: List[OrphanFileDef], root_dir: Path, dry_run: bool = False):
    if not orphans:
        print("ℹ️ No hay archivos huérfanos para limpiar.")
        return

    print(f"\n🗑️ Limpieza de archivos huérfanos ({len(orphans)} candidatos):")
    for orphan in orphans:
        rel = orphan.file_path.relative_to(root_dir).as_posix()
        if dry_run:
            print(f"  [DRY RUN] Se eliminaría: {rel}")
            continue
        try:
            orphan.file_path.unlink()
            print(f"  ✅ Eliminado: {rel}")
            parent = orphan.file_path.parent
            if parent.exists():
                remaining = list(parent.iterdir())
                if [p.name for p in remaining] == ["__init__.py"]:
                    (parent / "__init__.py").unlink()
                    print(f"  ✅ Eliminado paquete huérfano: {(parent / '__init__.py').relative_to(root_dir).as_posix()}")
                    parent.rmdir()
                    print(f"  ✅ Eliminado directorio vacío: {parent.relative_to(root_dir).as_posix()}")
                elif not remaining:
                    parent.rmdir()
                    print(f"  ✅ Eliminado directorio vacío: {parent.relative_to(root_dir).as_posix()}")
        except Exception as e:
            print(f"  ❌ Error eliminando {rel}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Audita archivos, símbolos e importaciones Python sin uso en backend, frontend y bootstrap.")
    parser.add_argument("--scope", choices=[*DEFAULT_SCOPES, "all"], default="all", help="Subsistema a escanear.")
    parser.add_argument("--orphans-only", action="store_true", help="Reportar únicamente archivos .py huérfanos.")
    parser.add_argument("--symbols-only", action="store_true", help="Reportar únicamente clases y funciones no referenciadas.")
    parser.add_argument("--imports-only", action="store_true", help="Reportar únicamente importaciones no utilizadas.")
    parser.add_argument("--clean-orphans", action="store_true", help="Eliminar archivos huérfanos detectados.")
    parser.add_argument("--dry-run", action="store_true", help="Simula la eliminación sin borrar nada.")
    parser.add_argument("--vulture", action="store_true", help="Ejecuta el linter 'uvx vulture'.")
    parser.add_argument("--json", action="store_true", help="Exporta el reporte en formato JSON.")

    args = parser.parse_args()

    scopes = DEFAULT_SCOPES if args.scope == "all" else [args.scope]
    scanner = DeadCodeScanner(PROJECT_ROOT, scopes)
    scanner.collect_files()
    scanner.scan_all_ast()
    report = scanner.analyze()

    if args.json:
        output = {
            "scanned_files": report.total_files_scanned,
            "orphan_files": [
                {
                    "path": o.file_path.relative_to(PROJECT_ROOT).as_posix(),
                    "lines": o.lines_count,
                    "bytes": o.size_bytes,
                    "isolated_in_package": o.imported_only_by_self_package,
                }
                for o in report.orphan_files
            ],
            "unused_symbols": [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "path": s.file_path.relative_to(PROJECT_ROOT).as_posix(),
                    "line": s.line,
                }
                for s in report.unused_symbols
            ],
            "unused_imports": [
                {
                    "name": i.imported_name,
                    "module": i.module_source,
                    "path": i.file_path.relative_to(PROJECT_ROOT).as_posix(),
                    "line": i.line,
                }
                for i in report.unused_imports
            ],
        }
        print(json.dumps(output, indent=2))
        return

    show_symbols = not args.orphans_only and not args.imports_only
    show_imports = not args.orphans_only and not args.symbols_only
    DeadCodePresenter.print_report(report, PROJECT_ROOT, show_symbols=show_symbols, show_imports=show_imports)

    if args.clean_orphans or args.dry_run:
        clean_orphan_files(report.orphan_files, PROJECT_ROOT, dry_run=args.dry_run)

    if args.vulture:
        vulture_scopes = DEFAULT_SCOPES if args.scope == "all" else [args.scope]
        run_vulture_audit(vulture_scopes)

if __name__ == "__main__":
    main()