# resources/tools/frontend_design_token_auditor.py

import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
THEME_FILE   = os.path.join(FRONTEND_DIR, "common", "theme.py")

COLOR_RESET  = "\033[0m"
COLOR_BOLD   = "\033[1m"
COLOR_GREEN  = "\033[92m"
COLOR_RED    = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN   = "\033[96m"
COLOR_MAGENTA= "\033[95m"
COLOR_GRAY   = "\033[90m"

HEX_COLOR_REGEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")

EXCLUDED_FILES = {
    "theme.py",
    "color_picker.py",
    "color_picker_widget.py",
    "chat_mockup.py",
    "alert_mockup.py",
    "music_mockup.py"
}

TOKEN_SUGGESTIONS = {
    "#00E701": "COLOR_KICK / COLOR_GREEN",
    "#53FC18": "COLOR_KICK",
    "#2ECD70": "COLOR_GREEN",
    "#16A34A": "COLOR_GREEN_SOLID",
    "#EF4444": "COLOR_RED",
    "#DC2626": "COLOR_RED_DARK",
    "#F59E0B": "COLOR_AMBER",
    "#3B82F6": "COLOR_BLUE",
    "#A855F7": "COLOR_PURPLE",
    "#9146FF": "COLOR_TWITCH",
    "#141519": "COLOR_NEUTRAL_950",
    "#18191E": "COLOR_NEUTRAL_900",
    "#202228": "COLOR_NEUTRAL_750",
    "#282A32": "COLOR_NEUTRAL_750",
    "#343741": "COLOR_NEUTRAL_700",
    "#9CA3AF": "COLOR_NEUTRAL_400",
    "#F4F4F6": "COLOR_NEUTRAL_050",
    "#FFFFFF": "COLOR_NEUTRAL_000",
    "#000000": "COLOR_NEUTRAL_999"
}


@dataclass
class DesignTokenViolation:
    file_path: str
    line: int
    violation_type: str
    detected_value: str
    suggested_token: Optional[str]
    code_snippet: str


def audit_design_tokens(target_dir: str = FRONTEND_DIR) -> List[DesignTokenViolation]:
    violations: List[DesignTokenViolation] = []

    for root, _, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".py") or file in EXCLUDED_FILES:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/")

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for idx, line in enumerate(lines, 1):
                clean_line = line.strip()
                if clean_line.startswith("#"):
                    continue

                if "setStyleSheet(" in clean_line and not clean_line.startswith("#"):
                    if "background" in clean_line.lower() or "color" in clean_line.lower() or "border" in clean_line.lower():
                        violations.append(DesignTokenViolation(
                            file_path=rel_path,
                            line=idx,
                            violation_type="INLINE_STYLESHEET",
                            detected_value="setStyleSheet(...) inline",
                            suggested_token="setProperty('role', ...) / theme.py",
                            code_snippet=clean_line
                        ))

                matches = HEX_COLOR_REGEX.findall(clean_line)
                for hex_val in matches:
                    hex_upper = hex_val.upper()
                    sugg = TOKEN_SUGGESTIONS.get(hex_upper)
                    violations.append(DesignTokenViolation(
                        file_path=rel_path,
                        line=idx,
                        violation_type="HARDCODED_HEX_COLOR",
                        detected_value=hex_val,
                        suggested_token=sugg,
                        code_snippet=clean_line
                    ))

    return violations


def print_report(violations: List[DesignTokenViolation]):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}  MINIKICK - AUDITOR DE TOKENS DE DISEÑO Y COLORES (THEME CHECK)     {COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}======================================================================{COLOR_RESET}\n")

    if not violations:
        print(f"{COLOR_GREEN}{COLOR_BOLD}✅ ¡EXCELENTE! Cero colores hardcodeados ni estilos inline detectados.{COLOR_RESET}")
        print(f"{COLOR_GRAY}Todo el frontend utiliza exclusivamente los tokens centralizados en theme.py.{COLOR_RESET}\n")
        return

    print(f"{COLOR_BOLD}{COLOR_YELLOW}⚠️ Se detectaron {len(violations)} colores hardcodeados o estilos inline fuera de theme.py:{COLOR_RESET}\n")
    for v in violations:
        sugg_text = f" -> Sugerencia: {COLOR_GREEN}{v.suggested_token}{COLOR_RESET}" if v.suggested_token else ""
        print(f"  • {COLOR_BOLD}{v.file_path}:{v.line}{COLOR_RESET} [{COLOR_CYAN}{v.violation_type}{COLOR_RESET}]")
        print(f"    Valor:   {COLOR_MAGENTA}{v.detected_value}{COLOR_RESET}{sugg_text}")
        print(f"    Código:  {COLOR_GRAY}{v.code_snippet}{COLOR_RESET}\n")

    print(f"{COLOR_YELLOW}💡 Regla MiniKick: Importa las constantes COLOR_* desde frontend.common.theme{COLOR_RESET}")
    print(f"{COLOR_YELLOW}   para garantizar coherencia visual con el diseño de Antigravity.{COLOR_RESET}\n")


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Audita colores y estilos del frontend contra los tokens centralizados del tema.")
    parser.add_argument("--json", action="store_true", help="Exportar violaciones en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Terminar con código 1 si se detecta cualquier color hardcodeado")

    args = parser.parse_args()

    violations = audit_design_tokens()

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
                    "value": v.detected_value,
                    "suggested_token": v.suggested_token,
                    "snippet": v.code_snippet
                }
                for v in violations
            ]
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_report(violations)

    if args.strict and violations:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
