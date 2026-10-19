# resources/tools/project_unused_parameter_auditor.py

import argparse
import ast
import contextlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IGNORED_DIRS = {
    ".venv", "venv", "__pycache__", ".git", ".pytest_cache",
    ".agents", "build", "dist", "walkthroughs", "locales",
    "scratch", "node_modules", ".idea", ".vscode"
}

QT_EVENT_PATTERNS = {
    "resizeEvent", "paintEvent", "closeEvent", "showEvent", "hideEvent",
    "enterEvent", "leaveEvent", "mousePressEvent", "mouseReleaseEvent",
    "mouseDoubleClickEvent", "mouseMoveEvent", "wheelEvent", "keyPressEvent",
    "keyReleaseEvent", "focusInEvent", "focusOutEvent", "dragEnterEvent",
    "dragMoveEvent", "dragLeaveEvent", "dropEvent", "contextMenuEvent",
    "changeEvent", "timerEvent", "nativeEvent", "actionEvent", "moveEvent"
}

COLOR_RESET  = "\033[0m"
COLOR_BOLD   = "\033[1m"
COLOR_RED    = "\033[91m"
COLOR_GREEN  = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE   = "\033[94m"
COLOR_CYAN   = "\033[96m"


@dataclass(slots=True)
class UnusedParamOccurrence:
    file_path: str
    line: int
    func_name: str
    class_name: Optional[str]
    param_name: str
    category: str
    snippet: str
    is_method: bool

class ParameterUsageVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path | str, code_lines: List[str]):
        self.file_path = Path(file_path)
        try:
            self.rel_path = self.file_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            self.rel_path = self.file_path.as_posix()
        self.code_lines = code_lines
        self.class_stack: List[str] = []
        self.occurrences: List[UnusedParamOccurrence] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        is_protocol = any(
            (isinstance(b, ast.Name) and b.id in ("Protocol", "ABC"))
            or (isinstance(b, ast.Attribute) and b.attr in ("Protocol", "ABC"))
            for b in node.bases
        )
        if is_protocol or "interfaces" in self.file_path.parts:
            return
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        raw_params = [
            (arg.arg, arg.lineno)
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            if arg.arg not in ("self", "cls") and not arg.arg.startswith("_")
        ]
        if not raw_params:
            return

        used_identifiers = {
            n.id for stmt in node.body for n in ast.walk(stmt)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }

        current_class = self.class_stack[-1] if self.class_stack else None
        for param_name, line_no in raw_params:
            if param_name not in used_identifiers:
                snippet = self.code_lines[line_no - 1].strip() if 0 <= line_no - 1 < len(self.code_lines) else ""
                self.occurrences.append(UnusedParamOccurrence(
                    file_path=str(self.file_path),
                    line=line_no,
                    func_name=node.name,
                    class_name=current_class,
                    param_name=param_name,
                    category=self._classify(node, current_class, param_name),
                    snippet=snippet,
                    is_method=current_class is not None
                ))

    def _classify(self, node: ast.AST, class_name: Optional[str], param_name: str) -> str:
        if node.name in QT_EVENT_PATTERNS or node.name.endswith("Event"):
            return "QT_OVERRIDE"

        for dec in node.decorator_list:
            dec_id = ""
            if isinstance(dec, ast.Name):
                dec_id = dec.id
            elif isinstance(dec, ast.Call):
                dec_id = dec.func.id if isinstance(dec.func, ast.Name) else (dec.func.attr if isinstance(dec.func, ast.Attribute) else "")
            elif isinstance(dec, ast.Attribute):
                dec_id = dec.attr

            if dec_id in ("Slot", "pyqtSlot"):
                return "QT_OVERRIDE"
            if dec_id in ("abstractmethod", "override"):
                return "CONTRACT_HOOK"

        return "CONTRACT_HOOK" if self._is_trivial_body(node) else "DEAD_PARAMETER"

    def _is_trivial_body(self, node: ast.AST) -> bool:
        body_stmts = [
            s for s in node.body
            if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant) and isinstance(s.value.value, str))
        ]
        if not body_stmts:
            return True
        if len(body_stmts) == 1:
            stmt = body_stmts[0]
            if isinstance(stmt, (ast.Pass, ast.Raise)):
                return True
            if isinstance(stmt, ast.Return):
                if stmt.value is None or isinstance(stmt.value, ast.Constant):
                    return True
                if isinstance(stmt.value, (ast.List, ast.Dict, ast.Set, ast.Tuple)) and not getattr(stmt.value, "elts", None) and not getattr(stmt.value, "keys", None):
                    return True
            if isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and stmt.value.value is Ellipsis:
                return True
        return False

def scan_directory(target_dir: Path) -> List[UnusedParamOccurrence]:
    results = []
    if not target_dir.exists():
        return results
    for file_path in target_dir.rglob("*.py"):
        if file_path.name.startswith("test_") or any(p in IGNORED_DIRS for p in file_path.parts):
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            tree = ast.parse(content, filename=str(file_path))
            visitor = ParameterUsageVisitor(file_path, lines)
            visitor.visit(tree)
            results.extend(visitor.occurrences)
        except Exception:
            pass
    return results

def fix_contract_hooks(occurrences: List[UnusedParamOccurrence]) -> int:
    hooks = [o for o in occurrences if o.category == "CONTRACT_HOOK"]
    if not hooks:
        return 0

    by_file = {}
    for o in hooks:
        by_file.setdefault(o.file_path, []).append(o)

    fixed_count = 0
    for file_str, items in by_file.items():
        try:
            file_path = Path(file_str)
            lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
            items.sort(key=lambda x: x.line, reverse=True)
            modified = False

            for item in items:
                line_idx = item.line - 1
                if 0 <= line_idx < len(lines):
                    orig_line = lines[line_idx]
                    new_line = re.sub(r'\b(' + re.escape(item.param_name) + r')\b', r'_\1', orig_line, count=1)
                    if new_line != orig_line:
                        lines[line_idx] = new_line
                        modified = True
                        fixed_count += 1

            if modified:
                file_path.write_text("".join(lines), encoding="utf-8")
        except Exception as e:
            print(f"Error modificando {file_str}: {e}")

    return fixed_count

def print_report(occurrences: List[UnusedParamOccurrence], target: str, category_filter: str):
    filters = {
        "dead": "DEAD_PARAMETER",
        "hooks": "CONTRACT_HOOK",
        "qt": "QT_OVERRIDE"
    }
    filtered = [o for o in occurrences if o.category == filters[category_filter]] if category_filter in filters else occurrences

    print("\n" + "=" * 80)
    print(f"  {COLOR_BOLD}MINIKICK - AUDITOR DE PARÁMETROS NO UTILIZADOS (AST Manager){COLOR_RESET}")
    print("=" * 80)
    print(f"  Objetivo: {COLOR_CYAN}{target.upper()}{COLOR_RESET} | Filtro: {COLOR_CYAN}{category_filter.upper()}{COLOR_RESET}")
    print("-" * 80)

    count_dead = sum(1 for o in occurrences if o.category == "DEAD_PARAMETER")
    count_hooks = sum(1 for o in occurrences if o.category == "CONTRACT_HOOK")
    count_qt = sum(1 for o in occurrences if o.category == "QT_OVERRIDE")

    if not filtered:
        print(f"\n  {COLOR_GREEN}✅ ¡Excelente! No se detectaron parámetros huérfanos con los filtros seleccionados.{COLOR_RESET}\n")
    else:
        print(f"\n{'TIPO':<18} | {'UBICACIÓN':<45} | {'FUNCIÓN / PARÁMETRO'}")
        print("-" * 80)
        for o in filtered:
            rel_path = Path(o.file_path).relative_to(PROJECT_ROOT).as_posix()
            loc = f"{rel_path}:{o.line}"
            if len(loc) > 43:
                loc = "..." + loc[-40:]
            fn_display = f"{o.class_name + '.' if o.class_name else ''}{o.func_name}({COLOR_BOLD}{o.param_name}{COLOR_RESET})"
            cat_tag = (
                f"{COLOR_RED}🔴 DEAD_PARAM{COLOR_RESET}" if o.category == "DEAD_PARAMETER"
                else f"{COLOR_YELLOW}🟡 HOOK_BASE{COLOR_RESET}" if o.category == "CONTRACT_HOOK"
                else f"{COLOR_BLUE}🔵 QT_OVERRIDE{COLOR_RESET}"
            )
            print(f"{cat_tag:<27} | {loc:<45} | {fn_display}")

    print("-" * 80)
    print(f"  {COLOR_BOLD}Resumen Global de Hallazgos:{COLOR_RESET}")
    print(f"    🔴 Parámetros Huérfanos (Dead Code Real) : {COLOR_BOLD}{count_dead}{COLOR_RESET}")
    print(f"    🟡 Hooks / Contratos de Clases Base      : {COLOR_BOLD}{count_hooks}{COLOR_RESET} (usar prefijo '_')")
    print(f"    🔵 Eventos y Callbacks de Qt (PySide6)   : {COLOR_BOLD}{count_qt}{COLOR_RESET}")
    print(f"    👉 Total hallazgos detectados            : {COLOR_BOLD}{len(occurrences)}{COLOR_RESET}")
    print("=" * 80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Audita parámetros no usados en backend y frontend, incluidos contratos y callbacks Qt.")
    parser.add_argument("--target", choices=["all", "backend", "frontend"], default="all", help="Directorio a escanear (default: all)")
    parser.add_argument("--category", choices=["all", "dead", "hooks", "qt"], default="all", help="Filtrar por categoría (default: all)")
    parser.add_argument("--fix-hooks", action="store_true", help="Aplica automáticamente el prefijo '_' a los parámetros en contratos base")
    parser.add_argument("--json", action="store_true", help="Imprime el reporte en formato JSON")

    args = parser.parse_args()

    targets_to_scan = []
    if args.target in ("all", "backend"):
        targets_to_scan.append(PROJECT_ROOT / "backend")
    if args.target in ("all", "frontend"):
        targets_to_scan.append(PROJECT_ROOT / "frontend")

    all_occurrences: List[UnusedParamOccurrence] = []
    for t in targets_to_scan:
        all_occurrences.extend(scan_directory(t))

    if args.fix_hooks:
        fixed = fix_contract_hooks(all_occurrences)
        print(f"\n{COLOR_GREEN}✨ Se aplicó el prefijo '_' a {fixed} parámetro(s) en métodos base.{COLOR_RESET}\n")
        all_occurrences = []
        for t in targets_to_scan:
            all_occurrences.extend(scan_directory(t))

    if args.json:
        print(json.dumps([asdict(o) for o in all_occurrences], indent=2, ensure_ascii=False))
    else:
        print_report(all_occurrences, args.target, args.category)

if __name__ == "__main__":
    main()
