# resources\tools\frontend_qt_window_lifecycle_auditor.py\

import argparse
import ast
import contextlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")


def _resolve_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "frontend").exists() and (parent / "backend").exists():
            return parent
    return Path(__file__).resolve().parents[3]


PROJECT_ROOT = _resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IGNORED_DIRS = {
    ".venv", "venv", "__pycache__", ".git", ".pytest_cache",
    ".agents", "build", "dist", "walkthroughs", "locales",
    "scratch", "node_modules", ".idea", ".vscode"
}

ALLOWED_INTERNAL_POPUPS = {
    "QComboBoxPrivateContainer",
    "CategorySuggestionsPopup",
    "SearchableComboPopup",
}

COLOR_RESET  = "\033[0m"
COLOR_BOLD   = "\033[1m"
COLOR_RED    = "\033[91m"
COLOR_GREEN  = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN   = "\033[96m"


@dataclass(slots=True)
class WindowViolation:
    severity: str
    source: str
    target: str
    line: Optional[int]
    description: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AuditSummary:
    total_views_tested: int = 0
    total_files_scanned: int = 0
    critical_count: int = 0
    warning_count: int = 0
    clean_views: List[str] = field(default_factory=list)
    violations: List[WindowViolation] = field(default_factory=list)


class AstParentScanner(ast.NodeVisitor):
    RISKY_CALLS = {
        "calendarWidget": "Llamada inmediata a .calendarWidget() fuerza la creación prematura de QCalendarPopup con título 'python'."
    }

    WIDGET_CLASSES_REQUIRING_PARENT = {
        "NoWheelDateEdit", "NoWheelTimeEdit", "NoWheelSpinBox", "NoWheelDoubleSpinBox",
        "NoWheelComboBox", "ModernButton", "ModernSwitch", "ModernCard", "PlatformStatusCard",
        "CategorySearchComboBox"
    }

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.rel_path = file_path.relative_to(PROJECT_ROOT).as_posix()
        self.violations: List[WindowViolation] = []

    def visit_Call(self, node: ast.Call):
        func_name = self._get_func_name(node.func)

        if func_name in self.RISKY_CALLS and "no_wheel.py" not in self.rel_path:
            self.violations.append(WindowViolation(
                severity="CRITICAL",
                source="AST",
                target=self.rel_path,
                line=node.lineno,
                description=f"Llamada riesgosa detectada: {func_name}()",
                details={"call": func_name}
            ))

        if func_name in self.WIDGET_CLASSES_REQUIRING_PARENT:
            has_parent = any(
                kw.arg == "parent" and not (isinstance(kw.value, ast.Constant) and kw.value.value is None)
                for kw in node.keywords
            )
            if not has_parent and node.args:
                last_arg = node.args[-1]
                if isinstance(last_arg, ast.Name) and last_arg.id in ("self", "parent", "container", "tabs_container", "col1", "col2"):
                    has_parent = True

            if not has_parent and ("frontend/views" in self.rel_path or "frontend/components" in self.rel_path):
                self.violations.append(WindowViolation(
                    severity="WARNING",
                    source="AST",
                    target=self.rel_path,
                    line=node.lineno,
                    description=f"Instanciación de '{func_name}' sin 'parent' explícito.",
                    details={"widget": func_name}
                ))

        self.generic_visit(node)

    def _get_func_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""


class RuntimeWindowAuditor:
    VIEWS_TO_TEST = [
        ("Dashboard", "frontend.views.dashboard_view", "DashboardView"),
        ("Chat", "frontend.views.chat_view", "ChatView"),
        ("Alerts", "frontend.views.alerts_view", "AlertsView"),
        ("Widgets", "frontend.views.widgets_view", "WidgetsView"),
        ("Settings", "frontend.views.settings_view", "SettingsView"),
        ("Stream Info", "frontend.views.schedule_view", "ScheduleView"),
        ("Commands", "frontend.views.commands_view", "CommandView"),
        ("Timers", "frontend.views.timers_view", "TimersView"),
        ("Music", "frontend.views.music_view", "MusicView"),
        ("Rewards", "frontend.views.rewards_view", "RewardsView"),
        ("Logs", "frontend.views.logs_view", "LogView"),
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.app = None
        self.i18n = None

    def _ensure_qt(self):
        from PySide6.QtWidgets import QApplication
        from backend.services.system import TranslationService

        self.app = QApplication.instance() or QApplication(sys.argv[:1])
        if not self.i18n:
            self.i18n = TranslationService()

    def audit_views(self) -> Tuple[List[WindowViolation], List[str]]:
        self._ensure_qt()
        from PySide6.QtWidgets import QApplication

        violations: List[WindowViolation] = []
        clean_views: List[str] = []

        for view_name, mod_path, cls_name in self.VIEWS_TO_TEST:
            before_widgets = set(QApplication.topLevelWidgets())
            view_instance = None
            try:
                mod = __import__(mod_path, fromlist=[cls_name])
                cls = getattr(mod, cls_name)
                try:
                    view_instance = cls(self.i18n)
                except TypeError:
                    view_instance = cls(self.i18n, MagicMock())
            except Exception as e:
                violations.append(WindowViolation(
                    severity="WARNING", source="Runtime", target=f"{view_name} ({cls_name})",
                    line=None, description=f"Error instanciando vista: {e}"
                ))
                continue

            after_widgets = set(QApplication.topLevelWidgets())
            new_top_levels = [w for w in (after_widgets - before_widgets) if w != view_instance]

            view_clean = True
            for w in new_top_levels:
                class_name = w.metaObject().className()
                title = w.windowTitle()
                if class_name in ALLOWED_INTERNAL_POPUPS:
                    continue

                if class_name in ("QCalendarPopup", "QMenu") or title.lower() in ("python", "minikick"):
                    violations.append(WindowViolation(
                        severity="CRITICAL", source="Runtime", target=f"{view_name} ({cls_name})",
                        line=None, description=f"Rogue Top-Level Widget ({class_name}) creado en init."
                    ))
                    view_clean = False

            if view_clean:
                clean_views.append(view_name)
            if view_instance:
                view_instance.deleteLater()

        return violations, clean_views


class WindowAuditManager:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def scan_static(self) -> Tuple[List[WindowViolation], int]:
        violations: List[WindowViolation] = []
        files_scanned = 0
        target_dir = PROJECT_ROOT / "frontend"

        if target_dir.exists():
            for file_path in target_dir.rglob("*.py"):
                if file_path.name.startswith("test_") or any(p in IGNORED_DIRS for p in file_path.parts):
                    continue
                files_scanned += 1
                try:
                    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
                    scanner = AstParentScanner(file_path)
                    scanner.visit(tree)
                    violations.extend(scanner.violations)
                except Exception as e:
                    violations.append(WindowViolation(
                        severity="WARNING", source="AST", target=file_path.relative_to(PROJECT_ROOT).as_posix(),
                        line=1, description=f"Error parseando AST: {e}"
                    ))

        return violations, files_scanned

    def run_full_audit(self, runtime_only: bool = False, static_only: bool = False) -> AuditSummary:
        summary = AuditSummary()

        if not runtime_only:
            static_violations, files_scanned = self.scan_static()
            summary.total_files_scanned = files_scanned
            summary.violations.extend(static_violations)

        if not static_only:
            runtime_auditor = RuntimeWindowAuditor(verbose=self.verbose)
            view_violations, clean_views = runtime_auditor.audit_views()
            summary.total_views_tested = len(runtime_auditor.VIEWS_TO_TEST)
            summary.clean_views = clean_views
            summary.violations.extend(view_violations)

        for v in summary.violations:
            if v.severity == "CRITICAL":
                summary.critical_count += 1
            elif v.severity == "WARNING":
                summary.warning_count += 1

        return summary

    def print_report(self, summary: AuditSummary):
        print(f"\n{COLOR_BOLD}{COLOR_CYAN}{'='*70}{COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN}  MINIKICK - AUDITOR DE VENTANAS Y MICRO-POPUPS FANTASMA (INC-008)  {COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN}{'='*70}{COLOR_RESET}\n")

        print(f"Archivos frontend escaneados (AST): {COLOR_BOLD}{summary.total_files_scanned}{COLOR_RESET}")
        print(f"Vistas del sistema auditadas (Runtime): {COLOR_BOLD}{summary.total_views_tested}{COLOR_RESET}")
        print(f"Vistas totalmente limpias (0 HWND fugados): {COLOR_BOLD}{COLOR_GREEN}{len(summary.clean_views)}{COLOR_RESET}")
        print(f"Violaciones Críticas (Ghost Windows): {COLOR_BOLD}{COLOR_GREEN if summary.critical_count == 0 else COLOR_RED}{summary.critical_count}{COLOR_RESET}")
        print(f"Advertencias de Jerarquía / Parent: {COLOR_BOLD}{COLOR_GREEN if summary.warning_count == 0 else COLOR_YELLOW}{summary.warning_count}{COLOR_RESET}\n")

        if summary.violations:
            print(f"{COLOR_BOLD}Detalle de Hallazgos:{COLOR_RESET}")
            print("-" * 70)
            for v in summary.violations:
                color = COLOR_RED if v.severity == "CRITICAL" else COLOR_YELLOW
                loc = f":{v.line}" if v.line else ""
                print(f"[{color}{v.severity}{COLOR_RESET}] [{v.source}] {COLOR_BOLD}{v.target}{loc}{COLOR_RESET}")
                print(f"   -> {v.description}")
            print("-" * 70)
        else:
            print(f"{COLOR_GREEN}{COLOR_BOLD}✅ ESTADO PERFECTO: No se detectaron micro-ventanas fantasma ni HWNDs huérfanos.{COLOR_RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="Audita ciclo de vida, parentesco y creación de ventanas Qt del frontend.")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--runtime-only", action="store_true")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    manager = WindowAuditManager(verbose=args.verbose)
    summary = manager.run_full_audit(runtime_only=args.runtime_only, static_only=args.static_only)

    if args.json:
        print(json.dumps({
            "critical_count": summary.critical_count,
            "warning_count": summary.warning_count,
            "clean_views": summary.clean_views,
        }, indent=2))
    else:
        manager.print_report(summary)

    sys.exit(1 if summary.critical_count > 0 else 0)


if __name__ == "__main__":
    main()
