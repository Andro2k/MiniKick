# resources/tools/frontend_qt_signal_lifecycle_auditor.py

import ast
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Set

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

COLOR_RESET  = "\033[0m"
COLOR_BOLD   = "\033[1m"
COLOR_GREEN  = "\033[92m"
COLOR_RED    = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN   = "\033[96m"
COLOR_MAGENTA= "\033[95m"
COLOR_GRAY   = "\033[90m"

REFRESH_METHOD_PATTERNS = re.compile(
    r"^(?:render_|populate_|update_|refresh_|on_refresh|showEvent|paintEvent|on_filter)",
    re.IGNORECASE
)


@dataclass
class SignalLeakViolation:
    file_path: str
    line: int
    violation_type: str
    signal_target: str
    method_context: str
    description: str
    code_snippet: str


class SignalLeakVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, lines: List[str]):
        self.file_path = file_path
        self.rel_path = os.path.relpath(file_path, PROJECT_ROOT).replace("\\", "/")
        self.lines = lines
        self.current_function: Optional[str] = None
        self.loop_stack: List[ast.AST] = []
        self.local_widgets_created_in_function: Set[str] = set()
        self.local_widgets_created_in_loop: Set[str] = set()
        self.violations: List[SignalLeakViolation] = []

    def _get_line_text(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev_func = self.current_function
        prev_locals = self.local_widgets_created_in_function
        self.current_function = node.name
        self.local_widgets_created_in_function = set()

        self.generic_visit(node)

        self.current_function = prev_func
        self.local_widgets_created_in_function = prev_locals

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_For(self, node: ast.For):
        self.loop_stack.append(node)
        prev_loop_locals = self.local_widgets_created_in_loop
        self.local_widgets_created_in_loop = set()

        self.generic_visit(node)

        self.local_widgets_created_in_loop = prev_loop_locals
        self.loop_stack.pop()

    def visit_While(self, node: ast.While):
        self.loop_stack.append(node)
        prev_loop_locals = self.local_widgets_created_in_loop
        self.local_widgets_created_in_loop = set()

        self.generic_visit(node)

        self.local_widgets_created_in_loop = prev_loop_locals
        self.loop_stack.pop()

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Call):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.local_widgets_created_in_function.add(t.id)
                    if self.loop_stack:
                        self.local_widgets_created_in_loop.add(t.id)

        self.generic_visit(node)

    def _extract_caller_chain(self, node: ast.AST) -> str:
        parts = []
        curr = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        parts.reverse()
        return ".".join(parts)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        caller_node = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            caller_node = node.func.value

        if func_name == "connect" and caller_node is not None:
            caller_chain = self._extract_caller_chain(caller_node)
            first_id = caller_chain.split(".")[0] if caller_chain else ""

            if self.loop_stack:
                is_init_method = self.current_function in ("__init__", "_setup_ui", "_connect_signals", "_init_ui")
                is_iterating_controls = is_init_method and first_id in ("control", "widget", "w", "btn", "switch", "ctrl")
                
                is_local_to_iteration = first_id in self.local_widgets_created_in_loop
                if not is_iterating_controls and (caller_chain.startswith("self.") or (not is_local_to_iteration and first_id not in self.local_widgets_created_in_loop)):
                    if not is_local_to_iteration:
                        self.violations.append(SignalLeakViolation(
                            file_path=self.rel_path,
                            line=node.lineno,
                            violation_type="LOOP_CONNECT",
                            signal_target=caller_chain,
                            method_context=self.current_function or "global",
                            description=(
                                f"Conexión de señal '{caller_chain}.connect()' dentro de bucle. "
                                f"Si el widget persiste entre iteraciones, se acumulan listeners duplicados."
                            ),
                            code_snippet=self._get_line_text(node.lineno)
                        ))

            if self.current_function and REFRESH_METHOD_PATTERNS.match(self.current_function):
                if caller_chain.startswith("self.") and not caller_chain.endswith(".disconnect"):
                    is_local_widget = first_id in self.local_widgets_created_in_function
                    if not is_local_widget:
                        self.violations.append(SignalLeakViolation(
                            file_path=self.rel_path,
                            line=node.lineno,
                            violation_type="REFRESH_METHOD_CONNECT",
                            signal_target=caller_chain,
                            method_context=self.current_function,
                            description=(
                                f"Señal '{caller_chain}.connect()' conectada dentro del método de refresco '{self.current_function}'. "
                                f"Cada llamada a este método acumulará un listener adicional. Mueve la conexión a _setup_ui() o __init__."
                            ),
                            code_snippet=self._get_line_text(node.lineno)
                        ))

            if self.loop_stack and node.args:
                slot_arg = node.args[0]
                if isinstance(slot_arg, ast.Lambda):
                    loop_node = self.loop_stack[-1]
                    loop_vars = set()
                    if isinstance(loop_node, ast.For) and isinstance(loop_node.target, ast.Name):
                        loop_vars.add(loop_node.target.id)
                    elif isinstance(loop_node, ast.For) and isinstance(loop_node.target, (ast.Tuple, ast.List)):
                        for elt in loop_node.target.elts:
                            if isinstance(elt, ast.Name):
                                loop_vars.add(elt.id)

                    lambda_defaults = {arg.arg for arg in slot_arg.args.args if arg.arg in loop_vars}
                    for body_name in ast.walk(slot_arg.body):
                        if isinstance(body_name, ast.Name) and body_name.id in loop_vars:
                            if body_name.id not in lambda_defaults:
                                self.violations.append(SignalLeakViolation(
                                    file_path=self.rel_path,
                                    line=node.lineno,
                                    violation_type="LATE_BINDING_LAMBDA",
                                    signal_target=caller_chain,
                                    method_context=self.current_function or "global",
                                    description=(
                                        f"Lambda conectada a '{caller_chain}' referencia la variable de bucle '{body_name.id}' "
                                        f"sin bind por valor (lambda _, {body_name.id}={body_name.id}: ...). Causará late-binding bug."
                                    ),
                                    code_snippet=self._get_line_text(node.lineno)
                                ))
                                break

        self.generic_visit(node)


def audit_signal_connections(target_dir: str = FRONTEND_DIR) -> List[SignalLeakViolation]:
    all_violations: List[SignalLeakViolation] = []

    for root, _, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            full_path = os.path.join(root, file)
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    lines = content.splitlines()

                tree = ast.parse(content, filename=full_path)
                visitor = SignalLeakVisitor(full_path, lines)
                visitor.visit(tree)
                all_violations.extend(visitor.violations)
            except Exception as ex:
                print(f"{COLOR_YELLOW}⚠️ Error analizando {file}: {ex}{COLOR_RESET}", file=sys.stderr)

    return all_violations


def print_report(violations: List[SignalLeakViolation]):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}  MINIKICK - AUDITOR DE SEÑALES Y EVENT LOOPS QT (SIGNAL LEAK CHECK)  {COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}\n")

    if not violations:
        print(f"{COLOR_GREEN}{COLOR_BOLD}✅ ¡EXCELENTE! Cero conexiones repetitivas ni fugas de señales Qt detectadas.{COLOR_RESET}")
        print(f"{COLOR_GRAY}Todas las señales están conectadas en métodos seguros de ciclo de vida (init / setup).{COLOR_RESET}\n")
        return

    print(f"{COLOR_BOLD}{COLOR_RED}⚠️ Se detectaron {len(violations)} posibles fugas o duplicaciones de señales Qt:{COLOR_RESET}\n")
    for v in violations:
        print(f"  • {COLOR_BOLD}{v.file_path}:{v.line}{COLOR_RESET} [{COLOR_YELLOW}{v.violation_type}{COLOR_RESET}]")
        print(f"    Método:   {COLOR_CYAN}{v.method_context}(){COLOR_RESET}")
        print(f"    Señal:    {COLOR_MAGENTA}{v.signal_target}{COLOR_RESET}")
        print(f"    Detalle:  {v.description}")
        print(f"    Código:   {COLOR_GRAY}{v.code_snippet}{COLOR_RESET}\n")


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Audita conexiones de señales Qt y patrones de callbacks en el frontend.")
    parser.add_argument("--json", action="store_true", help="Exportar violaciones en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Terminar con código 1 si se detecta cualquier anomalía")
    parser.add_argument("--check", "-c", action="store_true", help="Modo verificación rápida para CI")

    args = parser.parse_args()

    violations = audit_signal_connections()

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
                    "type": v.violation_type,
                    "target": v.signal_target,
                    "method": v.method_context,
                    "description": v.description,
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
