# resources\tools\frontend_hardcoded_text_auditor.py\

import ast
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Set

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
COLOR_GRAY   = "\033[90m"

WIDGET_CONSTRUCTORS_WITH_TEXT: Set[str] = {
    "QLabel", "QPushButton", "QCheckBox", "QRadioButton", "QAction",
    "QGroupBox", "ModernButton", "SectionHeader"
}

TEXT_SETTER_METHODS: Set[str] = {
    "setText", "setToolTip", "setPlaceholderText", "setWindowTitle",
    "setTitle", "setWhatsThis", "setHeaderLabel", "setHeaderText"
}

TOAST_METHODS: Set[str] = {"show_toast", "notify"}

IGNORED_PATTERNS = re.compile(
    r"^(?:"
    r"[\s\-_:•><\|\*\./\\#@%=+0-9,]*|"
    r"[0-9]+(?:\.[0-9]+)?(?:\s*(?:%|MB|KB|GB|ms|s|px))?|"
    r"[a-zA-Z0-9_\-\./]+\.(?:svg|png|ico|wav|mp3|json|db|iss|spec|html|css)|"
    r"#[0-9a-fA-F]{3,8}|"
    r"https?://.*|"
    r"[\{\[].*[\}\]]|"
    r"role|state|card|body|caption|h[1-6]|button|badge.*|action_.*|accent.*|"
    r"danger|warning|success|info|everyone|subscriber|vip|moderator|broadcaster|"
    r"kick|twitch|tiktok|youtube|discord|"
    r"[a-z0-9_]+\.[a-z0-9_\.]+|"
    r"Qt::.*|"
    r"[A-Z0-9_]{3,}"
    r")$",
    re.IGNORECASE
)


@dataclass
class HardcodedViolation:
    file_path: str
    line: int
    col: int
    violation_type: str
    target: str
    raw_text: str
    code_snippet: str


class AntiHardcodeVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, lines: List[str]):
        self.file_path = file_path
        self.rel_path = os.path.relpath(file_path, PROJECT_ROOT).replace("\\", "/")
        self.lines = lines
        self.violations: List[HardcodedViolation] = []

    def _get_line_text(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def _is_hardcoded_user_string(self, text: str) -> bool:
        clean = text.strip()
        if not clean or len(clean) <= 1:
            return False
        if IGNORED_PATTERNS.match(clean):
            return False
        has_letters = bool(re.search(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]", clean))
        if not has_letters:
            return False
        if "." in clean and " " not in clean and not clean.endswith("."):
            return False
        return True

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in WIDGET_CONSTRUCTORS_WITH_TEXT:
            if node.args:
                arg0 = node.args[0]
                if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                    if self._is_hardcoded_user_string(arg0.value):
                        self.violations.append(HardcodedViolation(
                            file_path=self.rel_path,
                            line=node.lineno,
                            col=node.col_offset,
                            violation_type="WIDGET_CONSTRUCTOR",
                            target=func_name,
                            raw_text=arg0.value,
                            code_snippet=self._get_line_text(node.lineno)
                        ))

        if func_name in TEXT_SETTER_METHODS:
            if node.args:
                arg0 = node.args[0]
                if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                    if self._is_hardcoded_user_string(arg0.value):
                        self.violations.append(HardcodedViolation(
                            file_path=self.rel_path,
                            line=node.lineno,
                            col=node.col_offset,
                            violation_type="SETTER_CALL",
                            target=func_name,
                            raw_text=arg0.value,
                            code_snippet=self._get_line_text(node.lineno)
                        ))

        if func_name in TOAST_METHODS:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if self._is_hardcoded_user_string(arg.value):
                        self.violations.append(HardcodedViolation(
                            file_path=self.rel_path,
                            line=node.lineno,
                            col=node.col_offset,
                            violation_type="TOAST_MESSAGE",
                            target=func_name,
                            raw_text=arg.value,
                            code_snippet=self._get_line_text(node.lineno)
                        ))
            for kw in node.keywords:
                if kw.arg in ("message", "title", "text"):
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        if self._is_hardcoded_user_string(kw.value.value):
                            self.violations.append(HardcodedViolation(
                                file_path=self.rel_path,
                                line=node.lineno,
                                col=node.col_offset,
                                violation_type="TOAST_MESSAGE",
                                target=func_name,
                                raw_text=kw.value.value,
                                code_snippet=self._get_line_text(node.lineno)
                            ))

        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        if isinstance(node.op, ast.Or):
            for i in range(len(node.values) - 1):
                left = node.values[i]
                right = node.values[i + 1]

                is_i18n_call = False
                if isinstance(left, ast.Call) and isinstance(left.func, ast.Attribute):
                    if left.func.attr in ("get", "t") and "i18n" in getattr(left.func.value, "attr", "") or "i18n" in getattr(left.func.value, "id", ""):
                        is_i18n_call = True

                if is_i18n_call and isinstance(right, ast.Constant) and isinstance(right.value, str):
                    if self._is_hardcoded_user_string(right.value):
                        self.violations.append(HardcodedViolation(
                            file_path=self.rel_path,
                            line=node.lineno,
                            col=node.col_offset,
                            violation_type="INLINE_FALLBACK",
                            target="i18n.get or 'fallback'",
                            raw_text=right.value,
                            code_snippet=self._get_line_text(node.lineno)
                        ))

        self.generic_visit(node)


def audit_frontend_hardcoded_strings(target_dir: str = FRONTEND_DIR) -> List[HardcodedViolation]:
    all_violations: List[HardcodedViolation] = []
    
    EXCLUDED_FILES = {
        "chat_mockup.py"
    }

    for root, _, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".py") or file in EXCLUDED_FILES:
                continue

            full_path = os.path.join(root, file)
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    lines = content.splitlines()

                tree = ast.parse(content, filename=full_path)
                visitor = AntiHardcodeVisitor(full_path, lines)
                visitor.visit(tree)
                all_violations.extend(visitor.violations)
            except Exception as ex:
                print(f"{COLOR_YELLOW}⚠️ Error analizando {file}: {ex}{COLOR_RESET}", file=sys.stderr)

    return all_violations


def print_report(violations: List[HardcodedViolation]):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}  MINIKICK - AUDITOR DE TEXTOS HARDCODEADOS EN UI (i18n LEAK CHECK)   {COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}\n")

    if not violations:
        print(f"{COLOR_GREEN}{COLOR_BOLD}✅ ¡EXCELENTE! Cero textos hardcodeados o fallbacks inline detectados en el frontend.{COLOR_RESET}")
        print(f"{COLOR_GRAY}Todos los widgets utilizan correctamente el servicio de internacionalización (i18n).{COLOR_RESET}\n")
        return

    print(f"{COLOR_BOLD}{COLOR_RED}⚠️ Se detectaron {len(violations)} posibles textos hardcodeados en la UI:{COLOR_RESET}\n")
    for v in violations:
        print(f"  • {COLOR_BOLD}{v.file_path}:{v.line}{COLOR_RESET} [{COLOR_YELLOW}{v.violation_type}{COLOR_RESET}]")
        print(f"    Target:  {COLOR_CYAN}{v.target}{COLOR_RESET}")
        print(f"    Texto:   {COLOR_RED}\"{v.raw_text}\"{COLOR_RESET}")
        print(f"    Código:  {COLOR_GRAY}{v.code_snippet}{COLOR_RESET}\n")

    print(f"{COLOR_YELLOW}💡 Regla MiniKick: Centraliza estos textos en locales/en.json y locales/es.json{COLOR_RESET}")
    print(f"{COLOR_YELLOW}   y accede a ellos exclusivamente vía self.i18n.get('clave').{COLOR_RESET}\n")


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Audita textos visibles del frontend que no pasan por el servicio de traducciones.")
    parser.add_argument("--json", action="store_true", help="Exportar violaciones en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Terminar con código 1 si se detecta cualquier texto hardcodeado")
    parser.add_argument("--check", "-c", action="store_true", help="Modo verificación rápida para CI")

    args = parser.parse_args()

    violations = audit_frontend_hardcoded_strings()

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
                    "type": v.violation_type,
                    "target": v.target,
                    "text": v.raw_text,
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
