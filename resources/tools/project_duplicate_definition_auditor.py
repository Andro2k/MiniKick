# resources\tools\project_duplicate_definition_auditor.py

import argparse
import ast
import contextlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from resources.tools._project_sources import ROOT_ZONE, iter_python_files

TARGET_ZONES = {
    "all": None,
    "backend": ("backend",),
    "frontend": ("frontend",),
    "bootstrap": ("bootstrap", ROOT_ZONE),
    "resources": ("resources",),
}

COLOR_RESET  = "\033[0m"
COLOR_BOLD   = "\033[1m"
COLOR_RED    = "\033[91m"
COLOR_GREEN  = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN   = "\033[96m"

VERDICT_DIVERGENT = "DIVERGENT"
VERDICT_IDENTICAL = "IDENTICAL"

_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@dataclass(slots=True)
class DuplicateFinding:
    file_path: str
    kind: str
    name: str
    scope: Optional[str]
    first_line: int
    second_line: int
    verdict: str


def _decorator_base(dec: ast.expr) -> Optional[ast.expr]:
    return dec.func if isinstance(dec, ast.Call) else dec


def _is_overload(node: ast.AST) -> bool:
    for dec in getattr(node, "decorator_list", []):
        base = _decorator_base(dec)
        if isinstance(base, ast.Name) and base.id == "overload":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "overload":
            return True
    return False


def _is_variant_of(node: ast.AST, name: str) -> bool:
    """`@name.setter`, `@name.deleter`, `@name.register(...)`: redefinir el nombre es intencional."""
    for dec in getattr(node, "decorator_list", []):
        base = _decorator_base(dec)
        if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) and base.value.id == name:
            return True
    return _is_overload(node)


def _has_decorator(node: ast.AST, decorator_name: str) -> bool:
    return any(
        isinstance(_decorator_base(dec), ast.Name) and _decorator_base(dec).id == decorator_name
        for dec in getattr(node, "decorator_list", [])
    )


def _assigned_name(stmt: ast.stmt) -> Optional[str]:
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id
    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None and isinstance(stmt.target, ast.Name):
        return stmt.target.id
    return None


def _same_body(first: ast.stmt, second: ast.stmt) -> bool:
    if isinstance(first, _DEFINITIONS) != isinstance(second, _DEFINITIONS):
        return False
    if isinstance(first, _DEFINITIONS):
        return ast.dump(first) == ast.dump(second)
    return ast.dump(first.value) == ast.dump(second.value)


def _definition_kind(node: ast.AST, in_class: bool, is_test_file: bool) -> str:
    if isinstance(node, ast.ClassDef):
        return "class"
    if is_test_file and node.name.startswith("test"):
        return "test"
    if in_class:
        return "property" if _has_decorator(node, "property") else "method"
    return "function"


class DuplicateDefinitionScanner:
    def __init__(self, rel_path: str, is_test_file: bool):
        self.rel_path = rel_path
        self.is_test_file = is_test_file
        self.findings: List[DuplicateFinding] = []

    def scan(self, tree: ast.AST) -> List[DuplicateFinding]:
        stack = [(tree, None)]
        while stack:
            node, outer_scope = stack.pop()
            scope = node.name if isinstance(node, ast.ClassDef) else outer_scope
            for field in ("body", "orelse", "finalbody"):
                stmts = getattr(node, field, None)
                if isinstance(stmts, list) and stmts and isinstance(stmts[0], ast.stmt):
                    self._scan_statements(stmts, scope, in_class=isinstance(node, ast.ClassDef))
            if isinstance(node, ast.Dict):
                self._scan_dict(node, scope)
            stack.extend((child, scope) for child in ast.iter_child_nodes(node))
        return sorted(self.findings, key=lambda f: (f.second_line, f.name))

    def _scan_statements(self, stmts: List[ast.stmt], scope: Optional[str], in_class: bool) -> None:
        seen: Dict[str, ast.stmt] = {}
        for stmt in stmts:
            if isinstance(stmt, _DEFINITIONS):
                name = stmt.name
                previous = seen.get(name)
                if previous is not None and not _is_variant_of(stmt, name) and not _is_overload(previous):
                    self._report(_definition_kind(stmt, in_class, self.is_test_file), name, scope, previous, stmt)
                seen[name] = stmt
            elif in_class:
                name = _assigned_name(stmt)
                if name is None:
                    continue
                previous = seen.get(name)
                if previous is not None:
                    self._report("attribute", name, scope, previous, stmt)
                seen[name] = stmt

    def _scan_dict(self, node: ast.Dict, scope: Optional[str]) -> None:
        seen: Dict[tuple, ast.expr] = {}
        for key, value in zip(node.keys, node.values):
            if not isinstance(key, ast.Constant):
                continue
            ident = (type(key.value).__name__, key.value)
            previous_value = seen.get(ident)
            if previous_value is not None:
                verdict = VERDICT_IDENTICAL if ast.dump(previous_value) == ast.dump(value) else VERDICT_DIVERGENT
                self.findings.append(DuplicateFinding(
                    self.rel_path, "dict_key", repr(key.value), scope,
                    previous_value.lineno, key.lineno, verdict
                ))
            seen[ident] = value

    def _report(self, kind: str, name: str, scope: Optional[str], first: ast.stmt, second: ast.stmt) -> None:
        verdict = VERDICT_IDENTICAL if _same_body(first, second) else VERDICT_DIVERGENT
        self.findings.append(DuplicateFinding(
            self.rel_path, kind, name, scope, first.lineno, second.lineno, verdict
        ))


def scan_project(target: str) -> tuple[List[DuplicateFinding], List[str]]:
    findings: List[DuplicateFinding] = []
    unparsable: List[str] = []
    for file_path in iter_python_files(TARGET_ZONES[target]):
        rel_path = file_path.relative_to(PROJECT_ROOT).as_posix()
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            unparsable.append(rel_path)
            continue
        is_test_file = file_path.name.startswith("test_")
        findings.extend(DuplicateDefinitionScanner(rel_path, is_test_file).scan(tree))
    return findings, unparsable


def print_report(findings: List[DuplicateFinding], unparsable: List[str], target: str) -> None:
    divergent = [f for f in findings if f.verdict == VERDICT_DIVERGENT]
    identical = [f for f in findings if f.verdict == VERDICT_IDENTICAL]

    print("\n" + "=" * 100)
    print(f"  {COLOR_BOLD}MINIKICK - AUDITOR DE DEFINICIONES DUPLICADAS (AST){COLOR_RESET}")
    print("=" * 100)
    print(f"  Objetivo: {COLOR_CYAN}{target.upper()}{COLOR_RESET} | Regla: la última definición pisa a las anteriores")
    print("-" * 100)

    if not findings:
        print(f"\n  {COLOR_GREEN}✅ EXCELENTE: no hay definiciones, atributos de clase ni claves de dict duplicados.{COLOR_RESET}\n")
    else:
        print(f"\n{'VEREDICTO':<14} | {'TIPO':<10} | {'SÍMBOLO':<42} | {'LÍNEAS (1ª → pisada por 2ª)'}")
        print("-" * 100)
        for f in findings:
            badge = f"{COLOR_RED}🔴 DIVERGENTE{COLOR_RESET}" if f.verdict == VERDICT_DIVERGENT else f"{COLOR_YELLOW}🟡 IDÉNTICA{COLOR_RESET}"
            symbol = f"{f.scope + '.' if f.scope else ''}{f.name}"
            if len(symbol) > 40:
                symbol = "..." + symbol[-37:]
            print(f"{badge:<23} | {f.kind:<10} | {symbol:<42} | {f.file_path}:{f.first_line} → {f.second_line}")

    if unparsable:
        print(f"\n  ⚠️  Archivos no analizables: {len(unparsable)} ({', '.join(unparsable[:3])}{'...' if len(unparsable) > 3 else ''})")

    print("-" * 100)
    print(f"  Duplicados detectados: {len(findings)}")
    print(f"    🔴 Divergentes (la 1ª es código muerto con lógica distinta, requiere decisión) : {len(divergent)}")
    print(f"    🟡 Idénticas (borrar la 1ª no cambia el comportamiento)                        : {len(identical)}")
    print("=" * 100 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Detecta funciones, métodos, clases, atributos de clase y claves de dict definidos dos veces en el mismo ámbito (la última pisa a la primera).")
    parser.add_argument("--target", choices=list(TARGET_ZONES), default="all", help="Zona a escanear (default: all)")
    parser.add_argument("--check", action="store_true", help="Sale con código 1 si hay duplicados (para la suite y CI)")
    parser.add_argument("--json", action="store_true", help="Imprime el reporte en formato JSON")
    args = parser.parse_args()

    findings, unparsable = scan_project(args.target)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2, ensure_ascii=False))
    else:
        print_report(findings, unparsable, args.target)

    if args.check and findings:
        sys.exit(1)


if __name__ == "__main__":
    main()
