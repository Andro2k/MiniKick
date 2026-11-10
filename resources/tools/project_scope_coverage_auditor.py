# resources\tools\project_scope_coverage_auditor.py

import argparse
import ast
import contextlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from resources.tools._project_sources import KNOWN_ZONES, iter_python_files, unclassified_zones

TOOLS_DIR = PROJECT_ROOT / "resources" / "tools"
SUITE_FILE = TOOLS_DIR / "project_quality_suite.py"

UNTRACKED_REFERENCES = {"__init__.py", "api_keys.py"}
FILE_REFERENCE_RE = re.compile(r"""["']([A-Za-z0-9_./-]+\.py)["']""")

COLOR_RESET  = "\033[0m"
COLOR_BOLD   = "\033[1m"
COLOR_RED    = "\033[91m"
COLOR_GREEN  = "\033[92m"
COLOR_CYAN   = "\033[96m"


@dataclass(slots=True)
class CoverageIssue:
    rule: str
    location: str
    message: str


def check_unclassified_zones() -> List[CoverageIssue]:
    return [
        CoverageIssue(
            "UNCLASSIFIED_ZONE", f"{zone}/",
            f"{count} archivo(s) .py en una carpeta que ninguna zona conocida cubre ({', '.join(KNOWN_ZONES)}). "
            "Añádela a KNOWN_ZONES en _project_sources.py o revisa si las auditorías deben incluirla."
        )
        for zone, count in sorted(unclassified_zones().items())
    ]


def check_unparsable_files(files: List[Path]) -> List[CoverageIssue]:
    issues = []
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, ValueError) as ex:
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            issues.append(CoverageIssue(
                "UNPARSABLE_FILE", rel,
                f"No se puede analizar ({type(ex).__name__}); varias auditorías lo omiten en silencio."
            ))
    return issues


def check_stale_file_references(files: List[Path]) -> List[CoverageIssue]:
    """Archivos .py que las herramientas citan por nombre (excepciones, rutas de tema, etc.) y ya no existen."""
    project_files = {p.relative_to(PROJECT_ROOT).as_posix() for p in files}
    issues = []
    for tool in sorted(TOOLS_DIR.glob("*.py")):
        text = tool.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            for reference in FILE_REFERENCE_RE.findall(line):
                name = reference.replace("\\", "/")
                if Path(name).name in UNTRACKED_REFERENCES:
                    continue
                if not any(rel == name or rel.endswith("/" + name) for rel in project_files):
                    issues.append(CoverageIssue(
                        "STALE_FILE_REFERENCE", f"resources/tools/{tool.name}:{number}",
                        f"Cita '{reference}', que no existe en el proyecto (¿archivo renombrado o movido?)."
                    ))
    return issues


def check_unregistered_auditors() -> List[CoverageIssue]:
    suite_text = SUITE_FILE.read_text(encoding="utf-8")
    return [
        CoverageIssue(
            "UNREGISTERED_AUDITOR", f"resources/tools/{tool.name}",
            "Auditoría que no está registrada en project_quality_suite.py: la suite nunca la ejecuta."
        )
        for tool in sorted(TOOLS_DIR.glob("*_auditor.py"))
        if f'"{tool.name}"' not in suite_text
    ]


def audit_scope_coverage() -> List[CoverageIssue]:
    files = iter_python_files()
    return (
        check_unclassified_zones()
        + check_unparsable_files(files)
        + check_stale_file_references(files)
        + check_unregistered_auditors()
    )


def print_report(issues: List[CoverageIssue], total_files: int) -> None:
    print("\n" + "=" * 100)
    print(f"  {COLOR_BOLD}MINIKICK - AUDITOR DE COBERTURA DE HERRAMIENTAS (archivos nuevos y renombrados){COLOR_RESET}")
    print("=" * 100)
    print(f"  Archivos .py considerados (versionados + nuevos sin versionar): {COLOR_CYAN}{total_files}{COLOR_RESET}")
    print("-" * 100)

    if not issues:
        print(f"\n  {COLOR_GREEN}✅ EXCELENTE: todos los .py están cubiertos y ninguna herramienta cita archivos inexistentes.{COLOR_RESET}\n")
    else:
        print(f"\n{'REGLA':<22} | {'UBICACIÓN':<52} | MENSAJE")
        print("-" * 100)
        for issue in issues:
            print(f"{COLOR_RED}{issue.rule:<22}{COLOR_RESET} | {issue.location:<52} | {issue.message}")

    print("-" * 100)
    print(f"  Problemas de cobertura: {len(issues)}")
    print("=" * 100 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Verifica que las auditorías cubran todos los .py (incluidos nuevos y renombrados) y que sus excepciones por nombre sigan existiendo.")
    parser.add_argument("--check", action="store_true", help="Sale con código 1 si hay problemas de cobertura (para la suite y CI)")
    parser.add_argument("--json", action="store_true", help="Imprime el reporte en formato JSON")
    args = parser.parse_args()

    issues = audit_scope_coverage()

    if args.json:
        print(json.dumps([asdict(i) for i in issues], indent=2, ensure_ascii=False))
    else:
        print_report(issues, len(iter_python_files()))

    if args.check and issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
