# resources\tools\project_quality_suite.py

import argparse
import contextlib
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = PROJECT_ROOT / "resources" / "tools"

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


class AuditConfigProvider:
    @staticmethod
    def get_specs(static_only: bool = False) -> List[AuditSpec]:
        specs = [
            AuditSpec(
                name="Project Icon Integrity",
                command_desc="Auditoría de iconos sobrantes y faltantes",
                tool_filename="project_icon_integrity_tool.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and "faltantes detectados: 0" in out and "SIN USO detectados: 0" in out,
                    "0 faltantes, 0 huérfanos" if (code == 0 and "faltantes detectados: 0" in out) else "Anomalías en iconos"
                )
            ),
            AuditSpec(
                name="Project Translation Keys",
                command_desc="Paridad y uso de traducciones EN vs ES",
                tool_filename="project_translation_integrity_auditor.py",
                args=["--check", "--strict"], 
                evaluator=lambda code, out: (
                    code == 0,
                    "Paridad y limpieza 100%" if code == 0 else "Inconsistencias o claves sobrantes detectadas"
                )
            ),
            AuditSpec(
                name="Frontend Hardcoded Text",
                command_desc="Detección de textos sin i18n",
                tool_filename="frontend_hardcoded_text_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and ("Cero textos hardcodeados" in out or "0 textos hardcodeados" in out),
                    "100% i18n compliant" if code == 0 else "Textos estáticos no traducidos"
                )
            ),
            AuditSpec(
                name="Project Dead Code",
                command_desc="Detección de código y archivos huérfanos",
                tool_filename="project_dead_code_auditor.py",
                args=[],
                evaluator=lambda code, out: (
                    code == 0 and "Archivos huérfanos: 0" in out and "Símbolos no usados: 0" in out,
                    "0 código muerto" if code == 0 else "Código muerto detectado"
                )
            ),
            AuditSpec(
                name="Frontend QSS Roles",
                command_desc="Validación de roles QSS",
                tool_filename="frontend_qss_role_state_auditor.py",
                args=["--strict"],
                evaluator=lambda code, out: (
                    code == 0 and "Roles faltantes (en código, NO en theme) : 0" in out,
                    "100% paridad de roles" if code == 0 else "Roles no sincronizados"
                )
            ),
            AuditSpec(
                name="Project Unused Parameters",
                command_desc="Análisis AST de parámetros",
                tool_filename="project_unused_parameter_auditor.py",
                args=[],
                evaluator=lambda code, out: (
                    code == 0 and ("No se detectaron" in out or "Parámetros Huérfanos (Dead Code Real) : 0" in out),
                    "0 parámetros huérfanos" if code == 0 else "Parámetros no usados"
                )
            ),
            AuditSpec(
                name="Frontend Qt Signals",
                command_desc="Prevención de fugas de memoria por señales",
                tool_filename="frontend_qt_signal_lifecycle_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and ("Cero conexiones repetitivas" in out or "0 fugas" in out),
                    "0 fugas de señales" if code == 0 else "Fugas de señales detectadas"
                )
            ),
            AuditSpec(
                name="Frontend Design Tokens",
                command_desc="Validación Hex en UI",
                tool_filename="frontend_design_token_auditor.py",
                args=[],
                evaluator=lambda code, out: (
                    code == 0 and ("Cero colores" in out or "0 colores" in out or "EXCELENTE" in out),
                    "0 colores hardcodeados" if code == 0 else "Colores hex hardcodeados"
                )
            ),
            AuditSpec(
                name="Project Code Duplication",
                command_desc="Identificación de clonación lógica",
                tool_filename="project_code_duplication_auditor.py",
                args=["--min-statements", "8", "--strict"],
                evaluator=lambda code, out: (
                    code == 0 and ("EXCELENTE" in out or "Cero bloques" in out or "0 clusters" in out),
                    "0 duplicación lógica" if code == 0 else "Lógica clonada detectada"
                )
            ),
            AuditSpec(
                name="Project Architecture",
                command_desc="Separación SoR",
                tool_filename="project_architecture_boundary_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and "Cero violaciones" in out,
                    "Fronteras limpias" if code == 0 else "Violaciones arquitectónicas"
                )
            ),
            AuditSpec(
                name="Project File Placement",
                command_desc="Ubicación canónica",
                tool_filename="project_file_placement_auditor.py",
                args=["--check"],
                evaluator=lambda code, out: (
                    code == 0 and "Cero archivos fuera de lugar" in out,
                    "Pureza de directorios" if code == 0 else "Archivos fuera de lugar"
                )
            ),
            AuditSpec(
                name="Frontend Qt Windows",
                command_desc="Ventanas fantasma (Ghost Windows)",
                tool_filename="frontend_qt_window_lifecycle_auditor.py",
                args=["--static-only"] if static_only else [],
                evaluator=lambda code, out: (
                    code == 0 and ("ESTADO PERFECTO" in out or "Violaciones Críticas (Ghost Windows): 0" in out),
                    "0 ventanas fantasma" if code == 0 else "Riesgo de ventanas fantasma"
                )
            ),
        ]

        if not static_only:
            specs.append(
                AuditSpec(
                    name="Frontend Layout Matrix",
                    command_desc="Matriz Flexbox UI",
                    tool_filename="frontend_layout_responsiveness_auditor.py",
                    args=["--view", "all"],
                    timeout=90.0,
                    quick_support=False,
                    evaluator=lambda code, out: (
                        code == 0 and out.count("PASS") >= 11,
                        "11/11 vistas aprobadas" if code == 0 and out.count("PASS") >= 11 else "Error de Layout/Clipping"
                    )
                )
            )
        return specs


class ParallelAuditorService:
    def __init__(self):
        self.python_exec = sys.executable

    def _find_tool_path(self, tool_filename: str) -> Optional[Path]:
        direct_path = TOOLS_DIR / tool_filename
        if direct_path.is_file():
            return direct_path
        matches = sorted(TOOLS_DIR.rglob(tool_filename))
        return matches[0] if matches else None

    def _execute_single(self, spec: AuditSpec) -> CheckResult:
        tool_path = self._find_tool_path(spec.tool_filename)
        if not tool_path:
            return CheckResult(spec.name, spec.command_desc, spec.tool_filename, False, 0.0, "Herramienta no encontrada")

        cmd = [self.python_exec, str(tool_path)] + spec.args
        t0 = time.perf_counter()
        try:
            res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=spec.timeout)
            duration = time.perf_counter() - t0
            clean_out = re.sub(r"\x1b\[[0-9;]*m", "", res.stdout.strip())
            passed, summary = spec.evaluator(res.returncode, clean_out)
            
            return CheckResult(spec.name, spec.command_desc, spec.tool_filename, passed, duration, summary, stdout=res.stdout.strip(), stderr=res.stderr.strip())
        except Exception as ex:
            return CheckResult(spec.name, spec.command_desc, spec.tool_filename, False, time.perf_counter() - t0, "Fallo de ejecución", stdout="", stderr=str(ex))

    def run_all(self, specs: List[AuditSpec]) -> List[CheckResult]:
        results = []
        with ThreadPoolExecutor() as executor:
            future_to_spec = {executor.submit(self._execute_single, spec): spec for spec in specs}
            for future in as_completed(future_to_spec):
                results.append(future.result())
        
        return sorted(results, key=lambda x: x.name)


class ConsoleDashboardUI:    
    C_RST = "\033[0m"
    C_BLD = "\033[1m"
    C_GRN = "\033[92m"
    C_RED = "\033[91m"
    C_CYN = "\033[96m"
    C_GRY = "\033[90m"

    @staticmethod
    def print_dashboard(results: List[CheckResult]):
        total_time = sum(r.duration_sec for r in results)
        failed_results = [r for r in results if not r.passed]
        passed_count = len(results) - len(failed_results)
        all_passed = len(failed_results) == 0

        print(f"\n{ConsoleDashboardUI.C_BLD}{ConsoleDashboardUI.C_CYN}{'='*92}{ConsoleDashboardUI.C_RST}")
        print(f"{ConsoleDashboardUI.C_BLD}{ConsoleDashboardUI.C_CYN} 🛡️  MINIKICK - SUITE MAESTRA DE SALUD Y CONTROL DE CALIDAD (HEALTH AUDIT)           {ConsoleDashboardUI.C_RST}")
        print(f"{ConsoleDashboardUI.C_BLD}{ConsoleDashboardUI.C_CYN}{'='*92}{ConsoleDashboardUI.C_RST}")
        print(f" {ConsoleDashboardUI.C_BLD}{'Auditoría / Herramienta':<28} | {'Alcance / Diagnóstico':<38} | {'Tiempo':<7} | {'Estado':<7}{ConsoleDashboardUI.C_RST}")
        print("-" * 92)

        for r in results:
            status_badge = f"{ConsoleDashboardUI.C_GRN}✅ PASS{ConsoleDashboardUI.C_RST}" if r.passed else f"{ConsoleDashboardUI.C_RED}❌ FAIL{ConsoleDashboardUI.C_RST}"
            duration_str = f"{r.duration_sec:.2f}s"
            summary_disp = r.summary[:38] if len(r.summary) <= 38 else r.summary[:35] + "..."
            print(f" {r.name:<28} | {summary_disp:<38} | {duration_str:<7} | {status_badge}")

        print("=" * 92)
        if all_passed:
            print(f" {ConsoleDashboardUI.C_BLD}{ConsoleDashboardUI.C_GRN}🎉 [TODO EN ORDEN] {passed_count}/{len(results)} herramientas aprobadas. Salud óptima.{ConsoleDashboardUI.C_RST}")
        else:
            print(f" {ConsoleDashboardUI.C_BLD}{ConsoleDashboardUI.C_RED}⚠️ [HALLAZGOS DETECTADOS] {len(failed_results)} herramienta(s) fallaron.{ConsoleDashboardUI.C_RST}")

        print(f" {ConsoleDashboardUI.C_GRY}Tiempo Total Acumulado (Threads): {total_time:.2f} segundos{ConsoleDashboardUI.C_RST}")
        print(f"{ConsoleDashboardUI.C_BLD}{ConsoleDashboardUI.C_CYN}{'='*92}{ConsoleDashboardUI.C_RST}\n")

        if failed_results:
            print(f"{ConsoleDashboardUI.C_BLD}{ConsoleDashboardUI.C_RED}--- 🚨 DETALLE ESTRICTO DE ERRORES/ADVERTENCIAS ---{ConsoleDashboardUI.C_RST}")
            for r in failed_results:
                print(f"\n{ConsoleDashboardUI.C_BLD}[FAILED] {r.name} ({r.target_tool}){ConsoleDashboardUI.C_RST}")
                print("-" * 60)
                output = r.stdout.strip() + "\n" + r.stderr.strip()
                print(output if output.strip() else "Sin salida capturada.")
                print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description="Ejecuta las auditorías de calidad de forma paralela y estricta.")
    parser.add_argument("--quick", "-q", action="store_true", help="Auditoría estática rápida (omite UI runtime)")
    args = parser.parse_args()

    specs = AuditConfigProvider.get_specs(static_only=args.quick)
    
    print("Iniciando auditoría concurrente de herramientas...")
    auditor = ParallelAuditorService()
    results = auditor.run_all(specs)
    
    ConsoleDashboardUI.print_dashboard(results)

    if not all(r.passed for r in results):
        print("\n❌ CÓDIGO DE SALIDA 1: Corrige las advertencias de arriba para que el código sea admitido.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()