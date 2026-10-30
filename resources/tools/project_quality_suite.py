# resources\tools\project_quality_suite.py\

import argparse
import contextlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = PROJECT_ROOT / "resources" / "tools"

COLOR_RESET   = "\033[0m"
COLOR_BOLD    = "\033[1m"
COLOR_GREEN   = "\033[92m"
COLOR_RED     = "\033[91m"
COLOR_YELLOW  = "\033[93m"
COLOR_CYAN    = "\033[96m"
COLOR_MAGENTA = "\033[95m"
COLOR_GRAY    = "\033[90m"


def clean_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


@dataclass(slots=True)
class CheckResult:
    name: str
    command_desc: str
    target_tool: str
    passed: bool
    duration_sec: float
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""


@dataclass(slots=True)
class AuditSpec:
    name: str
    command_desc: str
    tool_filename: str
    args: List[str]
    evaluator: Callable[[int, str], Tuple[bool, str]]
    timeout: float = 60.0
    quick_support: bool = True


class SystemHealthAuditor:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.python_exec = sys.executable

    def _find_tool_path(self, tool_filename: str) -> Optional[Path]:
        direct_path = TOOLS_DIR / tool_filename
        if direct_path.is_file():
            return direct_path

        matches = sorted(TOOLS_DIR.rglob(tool_filename))
        return matches[0] if len(matches) == 1 else None

    def _run_tool(self, tool_filename: str, args: List[str], timeout: float = 60.0) -> Tuple[int, str, str, float]:
        tool_path = self._find_tool_path(tool_filename)
        if not tool_path:
            return -1, "", f"Herramienta no encontrada: {tool_filename}", 0.0

        cmd = [self.python_exec, str(tool_path)] + args
        t0 = time.perf_counter()
        try:
            res = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip(), time.perf_counter() - t0
        except subprocess.TimeoutExpired:
            return -1, "", f"Timeout tras {timeout}s", time.perf_counter() - t0
        except Exception as ex:
            return -1, "", str(ex), time.perf_counter() - t0

    def get_specs(self, static_only: bool = False) -> List[AuditSpec]:
        specs = [
            AuditSpec(
                name="Project Icon Integrity",
                command_desc="Auditoría de iconos sobrantes, faltantes y XML válido",
                tool_filename="project_icon_integrity_tool.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and "faltantes detectados: 0" in out and "SIN USO detectados: 0" in out,
                    "0 faltantes, 0 huérfanos" if (code == 0 and "faltantes detectados: 0" in out) else "Anomalías en iconos detectadas"
                )
            ),
            AuditSpec(
                name="Project Translation Keys",
                command_desc="Paridad y placeholders EN vs ES",
                tool_filename="project_translation_integrity_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and "Claves faltantes en en.json: 0" in out and "Claves SIN USO detectadas: 0" in out,
                    "Paridad 100% EN/ES" if (code == 0 and "Claves faltantes en en.json: 0" in out) else "Inconsistencias de traducción detectadas"
                )
            ),
            AuditSpec(
                name="Frontend Hardcoded Text",
                command_desc="Detección de textos directos sin i18n en widgets Qt",
                tool_filename="frontend_hardcoded_text_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and ("Cero textos hardcodeados" in out or "0 textos hardcodeados" in out),
                    "0 textos hardcodeados (100% i18n compliant)" if code == 0 and "Cero textos" in out else "Textos estáticos no traducidos detectados"
                )
            ),
            AuditSpec(
                name="Project Dead Code",
                command_desc="Detección de archivos, clases y funciones huérfanas",
                tool_filename="project_dead_code_auditor.py",
                args=[],
                evaluator=lambda code, out: (
                    code == 0 and "Archivos huérfanos: 0" in out and "Símbolos no usados: 0" in out,
                    "0 archivos huérfanos, 0 símbolos muertos" if code == 0 and "Archivos huérfanos: 0" in out else "Código muerto o huérfano detectado"
                )
            ),
            AuditSpec(
                name="Frontend QSS Roles",
                command_desc="Validación de selectores QSS y roles de widgets",
                tool_filename="frontend_qss_role_state_auditor.py",
                args=["--strict"],
                evaluator=lambda code, out: (
                    code == 0 and "Roles faltantes (en código, NO en theme) : 0" in out,
                    "100% paridad de roles con theme.py" if code == 0 and "Roles faltantes (en código, NO en theme) : 0" in out else "Roles no sincronizados"
                )
            ),
            AuditSpec(
                name="Project Unused Parameters",
                command_desc="Análisis AST de signaturas y parámetros no referenciados",
                tool_filename="project_unused_parameter_auditor.py",
                args=[],
                evaluator=lambda code, out: (
                    code == 0 and ("No se detectaron parámetros" in out or "Parámetros Huérfanos (Dead Code Real) : 0" in out),
                    "0 parámetros huérfanos detectados" if code == 0 and ("No se detectaron" in out or ": 0" in out) else "Parámetros no usados detectados"
                )
            ),
            AuditSpec(
                name="Frontend Qt Signals",
                command_desc="Prevención de listeners duplicados y closures tardíos",
                tool_filename="frontend_qt_signal_lifecycle_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and ("Cero conexiones repetitivas" in out or "0 fugas" in out),
                    "0 fugas de señales Qt ni listeners duplicados" if code == 0 and "Cero conexiones" in out else "Fugas de señales detectadas"
                )
            ),
            AuditSpec(
                name="Frontend Design Tokens",
                command_desc="Validación de coherencia con el tema Figma / Hex",
                tool_filename="frontend_design_token_auditor.py",
                args=[],
                evaluator=lambda code, out: (
                    code == 0 and ("Cero colores" in out or "0 colores" in out or "EXCELENTE" in out),
                    "0 colores hex hardcodeados en UI" if (code == 0 and ("Cero colores" in out or "EXCELENTE" in out)) else "Colores hex hardcodeados detectados"
                )
            ),
            AuditSpec(
                name="Project Code Duplication",
                command_desc="Identificación de bloques de lógica clonados",
                tool_filename="project_code_duplication_auditor.py",
                args=["--min-statements", "8", "--strict"],
                evaluator=lambda code, out: (
                    code == 0 and ("EXCELENTE" in out or "Cero bloques" in out or "0 clusters" in out),
                    "0 clusters de lógica duplicada" if code == 0 else "Lógica duplicada/clonada detectada"
                )
            ),
            AuditSpec(
                name="Project Architecture",
                command_desc="Separación SoR, desacoplamiento y políticas",
                tool_filename="project_architecture_boundary_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and "Cero violaciones arquitectónicas" in out,
                    "Fronteras SoR limpias (0 violaciones)" if code == 0 and "Cero violaciones" in out else "Violaciones arquitectónicas detectadas"
                )
            ),
            AuditSpec(
                name="Project File Placement",
                command_desc="Pureza de carpetas y ubicación canónica",
                tool_filename="project_file_placement_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and "Cero archivos fuera de lugar" in out,
                    "Pureza de directorios (0 desvíos)" if code == 0 and "Cero archivos" in out else "Archivos fuera de lugar detectados"
                )
            ),
            AuditSpec(
                name="Frontend Qt Windows",
                command_desc="Prevención de micro-ventanas fantasma y HWNDs",
                tool_filename="frontend_qt_window_lifecycle_auditor.py",
                args=["--static-only"] if static_only else [],
                evaluator=lambda code, out: (
                    code == 0 and ("ESTADO PERFECTO" in out or "Violaciones Críticas (Ghost Windows): 0" in out),
                    "0 ventanas fantasma / HWNDs huérfanos" if code == 0 else "Riesgo de ventanas fantasma detectado"
                )
            ),
        ]

        if not static_only:
            specs.append(
                AuditSpec(
                    name="Frontend Layout Matrix",
                    command_desc="Inspección de flexbox y clipping en vistas",
                    tool_filename="frontend_layout_responsiveness_auditor.py",
                    args=["--view", "all"],
                    timeout=90.0,
                    quick_support=False,
                    evaluator=lambda code, out: (
                        code == 0 and out.count("PASS") >= 11,
                        "11/11 vistas aprobadas en matriz flex" if code == 0 and out.count("PASS") >= 11 else "Clipping/Flex error en UI"
                    )
                )
            )

        return specs

    def run_all(self, quick: bool = False, silent: bool = False) -> List[CheckResult]:
        specs = self.get_specs(static_only=quick)
        results: List[CheckResult] = []

        for spec in specs:
            if not silent:
                sys.stdout.write(f"  {COLOR_CYAN}▶{COLOR_RESET} Evaluando {COLOR_BOLD}{spec.name:<26}{COLOR_RESET}...")
                sys.stdout.flush()

            code, out, err, elapsed = self._run_tool(spec.tool_filename, spec.args, timeout=spec.timeout)
            clean_out = clean_ansi(out)
            passed, summary = spec.evaluator(code, clean_out)

            res = CheckResult(
                name=spec.name,
                command_desc=spec.command_desc,
                target_tool=spec.tool_filename,
                passed=passed,
                duration_sec=elapsed,
                summary=summary,
                stdout=out,
                stderr=err,
            )
            results.append(res)

            if not silent:
                status_tag = f"{COLOR_GREEN}✅ PASS{COLOR_RESET}" if passed else f"{COLOR_RED}❌ FAIL{COLOR_RESET}"
                sys.stdout.write(f"\r  {status_tag} {COLOR_BOLD}{spec.name:<32}{COLOR_RESET} ({elapsed:.2f}s)\n")
                sys.stdout.flush()

        return results

    def print_dashboard(self, results: List[CheckResult]):
        total_time = sum(r.duration_sec for r in results)
        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count
        all_passed = failed_count == 0

        print(f"\n{COLOR_BOLD}{COLOR_CYAN}{'='*92}{COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN} 🛡️  MINIKICK - SUITE MAESTRA DE SALUD Y CONTROL DE CALIDAD (HEALTH AUDIT)           {COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN}{'='*92}{COLOR_RESET}")
        print(f" {COLOR_BOLD}{'Auditoría / Herramienta':<28} | {'Alcance / Diagnóstico':<38} | {'Tiempo':<7} | {'Estado':<7}{COLOR_RESET}")
        print("-" * 92)

        for r in results:
            status_badge = f"{COLOR_GREEN}✅ PASS{COLOR_RESET}" if r.passed else f"{COLOR_RED}❌ FAIL{COLOR_RESET}"
            duration_str = f"{r.duration_sec:.2f}s"
            summary_disp = r.summary[:38] if len(r.summary) <= 38 else r.summary[:35] + "..."
            print(f" {r.name:<28} | {summary_disp:<38} | {duration_str:<7} | {status_badge}")

        print("=" * 92)
        if all_passed:
            print(f" {COLOR_BOLD}{COLOR_GREEN}🎉 [TODO EN ORDEN] {passed_count}/{len(results)} herramientas aprobadas. Salud óptima del codebase.{COLOR_RESET}")
        else:
            print(f" {COLOR_BOLD}{COLOR_RED}⚠️ [HALLAZGOS DETECTADOS] {failed_count} herramienta(s) reportaron fallos o anomalías.{COLOR_RESET}")

        print(f" {COLOR_GRAY}Tiempo Total de Auditoría: {total_time:.2f} segundos{COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN}{'='*92}{COLOR_RESET}\n")

        if not all_passed and self.verbose:
            print(f"{COLOR_BOLD}{COLOR_RED}Detalle de Fallas Detectadas:{COLOR_RESET}")
            for r in results:
                if not r.passed:
                    print(f"\n--- Fallo en {r.name} ({r.target_tool}) ---")
                    print(r.stdout if r.stdout else r.stderr)


def main():
    parser = argparse.ArgumentParser(description="Ejecuta las auditorías registradas para validar la calidad del proyecto MiniKick.")
    parser.add_argument("--all", "-a", action="store_true", help="Ejecutar suite completa de salud")
    parser.add_argument("--quick", "-q", action="store_true", help="Auditoría estática rápida (omite UI runtime)")
    parser.add_argument("--json", action="store_true", help="Exportar resultados consolidados en JSON")
    parser.add_argument("--strict", action="store_true", help="Terminar con código 1 si algún chequeo falla")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar salida detallada de cada herramienta")

    args = parser.parse_args()

    auditor = SystemHealthAuditor(verbose=args.verbose)
    results = auditor.run_all(quick=args.quick, silent=args.json)

    if args.json:
        data = {
            "summary": {
                "total_checks": len(results),
                "passed_checks": sum(1 for r in results if r.passed),
                "failed_checks": sum(1 for r in results if not r.passed),
                "total_duration_sec": round(sum(r.duration_sec for r in results), 2),
                "all_passed": all(r.passed for r in results),
            },
            "checks": [
                {
                    "name": r.name,
                    "target_tool": r.target_tool,
                    "passed": r.passed,
                    "duration_sec": round(r.duration_sec, 2),
                    "summary": r.summary,
                }
                for r in results
            ],
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        auditor.print_dashboard(results)

    if args.strict and not all(r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
