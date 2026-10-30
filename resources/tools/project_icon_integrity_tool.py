# resources\tools\project_icon_integrity_tool.py\

import argparse
import ast
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ICONS_DIR = os.path.join(BASE_DIR, "assets", "icons")

DEFAULT_TARGET_DIRS = ["frontend", "backend"]
DEFAULT_TARGET_FILES = ["main.py"]

IGNORED_DIRS = {
    '.venv', 'venv', '__pycache__', '.git', '.pytest_cache',
    '.agents', '.vscode', 'build', 'dist', 'walkthroughs', 'docs',
    'locales', 'assets', 'resources', 'scratch', 'node_modules'
}

VALID_EXTENSIONS = ('.py', '.qss', '.html', '.css')
ICON_STRING_REGEX = re.compile(r'["\']([^"\'\n\r]+\.(?:svg|ico|png))["\']')


@dataclass
class IconOccurrence:
    icon_name: str
    file_path: str
    line_number: int
    line_content: str


@dataclass
class SvgIntegrityIssue:
    file_name: str
    file_path: str
    issue_type: str
    details: str


@dataclass
class IconAuditReport:
    existing_icons: Set[str] = field(default_factory=set)
    used_icons: Dict[str, List[IconOccurrence]] = field(default_factory=lambda: defaultdict(list))
    missing_icons: Dict[str, List[IconOccurrence]] = field(default_factory=lambda: defaultdict(list))
    unused_icons: Set[str] = field(default_factory=set)
    integrity_issues: List[SvgIntegrityIssue] = field(default_factory=list)

    @property
    def has_missing(self) -> bool:
        return bool(self.missing_icons)

    @property
    def has_unused(self) -> bool:
        return bool(self.unused_icons)

    @property
    def has_integrity_issues(self) -> bool:
        return bool(self.integrity_issues)

    @property
    def is_clean(self) -> bool:
        return not self.has_missing and not self.has_unused and not self.has_integrity_issues


class IconASTVisitor(ast.NodeVisitor):
    def __init__(self, file_lines: List[str]):
        self.file_lines = file_lines
        self.docstring_nodes: Set[int] = set()
        self.occurrences: List[Tuple[str, int, str]] = []

    def _mark_docstring(self, body: List[ast.stmt]):
        if body and isinstance(body[0], ast.Expr):
            val = body[0].value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                self.docstring_nodes.add(id(val))

    def visit_Module(self, node: ast.Module):
        self._mark_docstring(node.body)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._mark_docstring(node.body)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._mark_docstring(node.body)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._mark_docstring(node.body)
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        pass

    def visit_Constant(self, node: ast.Constant):
        if id(node) in self.docstring_nodes:
            return

        if isinstance(node.value, str):
            val = node.value.strip()
            if (val.endswith('.svg') or val.endswith('.ico') or val.endswith('.png')) and '{' not in val and '}' not in val:
                clean_name = os.path.basename(val)
                stem = clean_name.rsplit('.', 1)[0]
                if not stem:
                    return
                lineno = getattr(node, 'lineno', 1)
                line_content = self.file_lines[lineno - 1].strip() if 1 <= lineno <= len(self.file_lines) else ""
                self.occurrences.append((clean_name, lineno, line_content))


def extract_icons_from_file(file_path: str, base_dir: str) -> List[IconOccurrence]:
    rel_path = os.path.relpath(file_path, base_dir).replace('\\', '/')
    occurrences: List[IconOccurrence] = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"⚠️ Error leyendo archivo {rel_path}: {e}")
        return occurrences

    if file_path.endswith('.py'):
        try:
            tree = ast.parse("".join(lines), filename=file_path)
            visitor = IconASTVisitor(lines)
            visitor.visit(tree)
            for icon_name, lineno, line_text in visitor.occurrences:
                occurrences.append(IconOccurrence(
                    icon_name=icon_name,
                    file_path=rel_path,
                    line_number=lineno,
                    line_content=line_text
                ))
            return occurrences
        except SyntaxError:
            pass

    for line_no, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
            continue
        for match in ICON_STRING_REGEX.findall(raw_line):
            if '{' in match or '}' in match:
                continue
            clean_name = os.path.basename(match.strip())
            stem = clean_name.rsplit('.', 1)[0]
            if not stem:
                continue
            occurrences.append(IconOccurrence(
                icon_name=clean_name,
                file_path=rel_path,
                line_number=line_no,
                line_content=stripped
            ))

    return occurrences


def validate_icons_integrity(icons_dir: str = ICONS_DIR) -> List[SvgIntegrityIssue]:
    issues: List[SvgIntegrityIssue] = []
    if not os.path.exists(icons_dir):
        return issues

    for fname in os.listdir(icons_dir):
        fpath = os.path.join(icons_dir, fname)
        if not os.path.isfile(fpath):
            continue

        try:
            size = os.path.getsize(fpath)
            if size == 0:
                issues.append(SvgIntegrityIssue(
                    file_name=fname,
                    file_path=fpath,
                    issue_type="EMPTY",
                    details="El archivo tiene 0 bytes de tamaño."
                ))
                continue

            if fname.lower().endswith('.svg'):
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                if not content:
                    issues.append(SvgIntegrityIssue(
                        file_name=fname,
                        file_path=fpath,
                        issue_type="EMPTY",
                        details="El archivo SVG está vacío."
                    ))
                    continue

                try:
                    root = ET.fromstring(content)
                    tag_name = root.tag.split('}')[-1].lower() if '}' in root.tag else root.tag.lower()
                    if tag_name != 'svg':
                        issues.append(SvgIntegrityIssue(
                            file_name=fname,
                            file_path=fpath,
                            issue_type="NO_SVG_ROOT",
                            details=f"Elemento raíz no es <svg> (encontrado: <{root.tag}>)"
                        ))
                except ET.ParseError as pe:
                    issues.append(SvgIntegrityIssue(
                        file_name=fname,
                        file_path=fpath,
                        issue_type="CORRUPTED_XML",
                        details=f"Error de sintaxis XML: {pe}"
                    ))
        except Exception as e:
            issues.append(SvgIntegrityIssue(
                file_name=fname,
                file_path=fpath,
                issue_type="READ_ERROR",
                details=str(e)
            ))

    return issues


def scan_icons_in_project(
    base_dir: str = BASE_DIR,
    icons_dir: str = ICONS_DIR,
    include_tests: bool = False,
    target_dirs: Optional[List[str]] = None
) -> IconAuditReport:
    report = IconAuditReport()

    if os.path.exists(icons_dir):
        report.existing_icons = set(os.listdir(icons_dir))

    report.integrity_issues = validate_icons_integrity(icons_dir)

    files_to_scan: List[str] = []

    if target_dirs is None:
        for d in DEFAULT_TARGET_DIRS:
            full_d = os.path.join(base_dir, d)
            if os.path.exists(full_d):
                for root, dirs, files in os.walk(full_d):
                    dirs[:] = [sub for sub in dirs if sub not in IGNORED_DIRS]
                    for f in files:
                        if f.endswith(VALID_EXTENSIONS):
                            files_to_scan.append(os.path.join(root, f))

        for f in DEFAULT_TARGET_FILES:
            full_f = os.path.join(base_dir, f)
            if os.path.exists(full_f):
                files_to_scan.append(full_f)

        if include_tests:
            tests_dir = os.path.join(base_dir, "resources", "tests")
            if os.path.exists(tests_dir):
                for root, dirs, files in os.walk(tests_dir):
                    dirs[:] = [sub for sub in dirs if sub not in IGNORED_DIRS]
                    for f in files:
                        if f.endswith(VALID_EXTENSIONS):
                            files_to_scan.append(os.path.join(root, f))
    else:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            if os.path.abspath(root).startswith(os.path.abspath(icons_dir)):
                continue
            for f in files:
                if f in {"project_icon_integrity_tool.py", "icon_manager.py"}:
                    continue
                if f.endswith(VALID_EXTENSIONS):
                    files_to_scan.append(os.path.join(root, f))

    for fpath in files_to_scan:
        occurrences = extract_icons_from_file(fpath, base_dir)
        for occ in occurrences:
            clean_name = occ.icon_name
            if clean_name.endswith('.svg') or clean_name in report.existing_icons:
                report.used_icons[clean_name].append(occ)
                if clean_name not in report.existing_icons:
                    report.missing_icons[clean_name].append(occ)

    report.unused_icons = report.existing_icons - set(report.used_icons.keys())
    return report


def print_header(title: str):
    print("\n" + "=" * 55)
    print(f" {title}")
    print("=" * 55)


def audit_unused_icons(report: IconAuditReport) -> int:
    print_header("AUDITORÍA DE ICONOS SIN USO (SOBRANTES)")
    total_existing = len(report.existing_icons)
    total_used = len(report.used_icons)
    unused_list = sorted(list(report.unused_icons))

    print(f"📊 Total de iconos en assets/icons: {total_existing}")
    print(f"✅ Iconos en uso en el código: {total_used}")
    print(f"🟡 Iconos SIN USO detectados: {len(unused_list)}")

    if unused_list:
        print("\n📋 Lista de Iconos Sin Uso (pueden ser eliminados si no se planea usarlos):")
        total_size = 0
        for icon in unused_list:
            icon_path = os.path.join(ICONS_DIR, icon)
            size_bytes = os.path.getsize(icon_path) if os.path.exists(icon_path) else 0
            total_size += size_bytes
            print(f"  [X] {icon:<30} ({size_bytes:>5} bytes)")
        print(f"\n💾 Espacio total recuperable: {total_size:,} bytes (~{total_size / 1024:.1f} KB)")
    else:
        print("\n🎉 ¡Excelente! No hay iconos huérfanos ni sobrantes en assets/icons.")
    return len(unused_list)


def audit_missing_icons(report: IconAuditReport) -> int:
    print_header("AUDITORÍA DE ICONOS FALTANTES (USADOS EN CÓDIGO)")
    missing_items = report.missing_icons

    print(f"🔴 Iconos faltantes detectados: {len(missing_items)}")

    if missing_items:
        print("\n⚠️ Los siguientes iconos son llamados en el código pero NO existen en assets/icons/:")
        for icon, occurrences in sorted(missing_items.items()):
            print(f"\n  ❌ Icono: '{icon}'")
            for occ in occurrences:
                print(f"     -> Archivo: {occ.file_path}:{occ.line_number}")
                print(f"        Código: {occ.line_content}")
    else:
        print("\n✅ ¡Perfecto! Todos los iconos referenciados en el código existen físicamente en disco.")
    return len(missing_items)


def audit_integrity_report(report: IconAuditReport) -> int:
    print_header("AUDITORÍA DE INTEGRIDAD XML / SVG")
    issues = report.integrity_issues
    print(f"🔍 Archivos de icono analizados: {len(report.existing_icons)}")
    print(f"⚠️ Anomalías de integridad detectadas: {len(issues)}")

    if issues:
        for iss in issues:
            print(f"  ❌ [{iss.issue_type}] {iss.file_name}: {iss.details}")
    else:
        print("✅ ¡Todos los archivos SVG son válidos, no están corruptos y tienen tamaño óptimo!")
    return len(issues)


def print_detailed_report(report: IconAuditReport):
    print_header("REPORTE DETALLADO DE USO DE ICONOS")
    print(f"📊 Iconos únicos referenciados: {len(report.used_icons)}")

    for icon in sorted(report.used_icons.keys()):
        occs = report.used_icons[icon]
        status = "✅ EXISTE" if icon in report.existing_icons else "❌ FALTANTE"
        print(f"\n🔹 {icon:<32} [{status}] ({len(occs)} usos):")
        for occ in occs[:5]:
            print(f"    - {occ.file_path}:{occ.line_number}")
        if len(occs) > 5:
            print(f"    - ... y {len(occs) - 5} ocurrencias más.")


def clean_unused_icons(report: IconAuditReport, auto_confirm: bool = False):
    print_header("LIMPIEZA DE ICONOS SIN USO")
    unused_list = sorted(list(report.unused_icons))

    if not unused_list:
        print("🎉 No hay iconos sin uso para limpiar.")
        return

    print(f"Se encontraron {len(unused_list)} iconos sin uso en assets/icons/:\n")
    total_size = 0
    for icon in unused_list:
        icon_path = os.path.join(ICONS_DIR, icon)
        size_bytes = os.path.getsize(icon_path) if os.path.exists(icon_path) else 0
        total_size += size_bytes
        print(f"  - {icon:<30} ({size_bytes:>5} bytes)")

    print(f"\n💾 Espacio total a liberar: {total_size:,} bytes (~{total_size / 1024:.1f} KB)")

    if auto_confirm:
        confirm = 's'
    else:
        confirm = input(f"\n¿Deseas eliminar permanentemente estos {len(unused_list)} archivos de assets/icons? (s/N): ").strip().lower()

    if confirm in ('s', 'si', 'y', 'yes'):
        deleted = 0
        for icon in unused_list:
            fpath = os.path.join(ICONS_DIR, icon)
            try:
                if os.path.exists(fpath):
                    os.remove(fpath)
                    deleted += 1
                    print(f"  🗑️ Eliminado: {icon}")
            except Exception as e:
                print(f"  ⚠️ Error eliminando {icon}: {e}")
        print(f"\n✅ Operación completada: Se eliminaron {deleted} archivos de iconos.")
    else:
        print("❌ Operación cancelada. No se realizaron cambios en el disco.")


def run_interactive():
    while True:
        print("\n=======================================================")
        print("         MINI-KICK ICON TOOLKIT & AUDITOR")
        print("=======================================================")
        print("1. Auditar iconos sin uso (Sobran en assets/icons)")
        print("2. Auditar iconos faltantes (Usados en código)")
        print("3. Validar integridad de archivos SVG (XML/0-bytes)")
        print("4. Reporte de uso detallado (Iconos y ocurrencias)")
        print("5. Limpiar iconos sin uso (Eliminar)")
        print("6. Salir")
        print("=======================================================")

        try:
            choice = input("Selecciona una opción (1-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Saliendo...")
            break

        if choice in ("1", "2", "3", "4", "5"):
            report = scan_icons_in_project()

        if choice == "1":
            audit_unused_icons(report)
        elif choice == "2":
            audit_missing_icons(report)
        elif choice == "3":
            audit_integrity_report(report)
        elif choice == "4":
            print_detailed_report(report)
        elif choice == "5":
            clean_unused_icons(report)
        elif choice == "6":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("⚠️ Opción inválida. Intenta nuevamente.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita referencias e integridad de iconos usados por backend, frontend y la aplicación.")
    parser.add_argument("--check", action="store_true", help="Auditoría no-bloqueante integral para CI/scripts")
    parser.add_argument("--audit", action="store_true", help="Ejecuta una auditoría completa (sin uso y faltantes)")
    parser.add_argument("--missing", action="store_true", help="Audita únicamente iconos faltantes")
    parser.add_argument("--unused", action="store_true", help="Audita únicamente iconos sin uso")
    parser.add_argument("--integrity", action="store_true", help="Valida integridad física XML/SVG")
    parser.add_argument("--report", action="store_true", help="Imprime reporte detallado de ocurrencias")
    parser.add_argument("--clean", action="store_true", help="Limpia los iconos sin uso eliminándolos de assets/icons")
    parser.add_argument("--force", action="store_true", help="Omite la confirmación interactiva al limpiar")
    parser.add_argument("--json", action="store_true", help="Exporta resultados en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Falla (exit code 1) ante cualquier anomalía o icono sin uso")
    parser.add_argument("--include-tests", action="store_true", help="Incluye la carpeta de tests en el escaneo")

    args = parser.parse_args()

    has_flags = (
        args.check or args.audit or args.missing or args.unused or
        args.integrity or args.report or args.clean or args.json or args.strict
    )

    if has_flags or not sys.stdin.isatty():
        report = scan_icons_in_project(include_tests=args.include_tests)

        if args.json:
            out = {
                "status": "PASS" if not report.has_missing and not report.has_integrity_issues and (not args.strict or not report.has_unused) else "FAIL",
                "total_existing": len(report.existing_icons),
                "total_used": len(report.used_icons),
                "unused_count": len(report.unused_icons),
                "missing_count": len(report.missing_icons),
                "integrity_issues_count": len(report.integrity_issues),
                "unused_icons": sorted(list(report.unused_icons)),
                "missing_icons": {k: [f"{o.file_path}:{o.line_number}" for o in v] for k, v in report.missing_icons.items()},
                "integrity_issues": [{"file": i.file_name, "type": i.issue_type, "details": i.details} for i in report.integrity_issues]
            }
            print(json.dumps(out, indent=2, ensure_ascii=False))
            if args.strict:
                return 0 if report.is_clean else 1
            return 0 if not (report.has_missing or report.has_integrity_issues) else 1

        exit_code = 0
        should_run_audit = args.check or args.audit or (args.strict and not (args.unused or args.missing or args.report or args.clean or args.integrity))

        if args.unused or should_run_audit:
            audit_unused_icons(report)
        if args.missing or should_run_audit:
            missing_count = audit_missing_icons(report)
            if missing_count > 0:
                exit_code = 1
        if args.integrity or should_run_audit:
            integrity_count = audit_integrity_report(report)
            if integrity_count > 0:
                exit_code = 1
        if args.report:
            print_detailed_report(report)
        if args.clean:
            clean_unused_icons(report, auto_confirm=args.force)

        if args.strict and (report.has_missing or report.has_unused or report.has_integrity_issues):
            exit_code = 1

        return exit_code

    run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
