# resources/tools/frontend_qss_role_state_auditor.py

import ast
import difflib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def _find_project_root(script_path: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(script_path))
    while True:
        if os.path.isfile(os.path.join(current_dir, "frontend", "common", "theme.py")):
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir

    return os.path.abspath(os.path.join(os.path.dirname(script_path), "..", "..", ".."))


BASE_DIR = _find_project_root(__file__)
THEME_PATH = os.path.join(BASE_DIR, "frontend", "common", "theme.py")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

IGNORED_DIRS = {
    '.venv', 'venv', '__pycache__', '.git', '.pytest_cache',
    '.agents', 'build', 'dist', 'walkthroughs', 'locales',
    'scratch', 'node_modules'
}


@dataclass
class ThemeDefinition:
    name: str
    property_type: str
    widget_types: List[str] = field(default_factory=list)
    line_numbers: List[int] = field(default_factory=list)
    selectors: List[str] = field(default_factory=list)

    @property
    def first_line(self) -> int:
        return self.line_numbers[0] if self.line_numbers else 0

    @property
    def location_str(self) -> str:
        rel_theme = os.path.relpath(THEME_PATH, BASE_DIR).replace('\\', '/')
        if self.line_numbers:
            lines = ", ".join(str(l) for l in self.line_numbers)
            return f"{rel_theme}:{lines}"
        return rel_theme


@dataclass
class RoleOccurrence:
    role: str
    file_path: str
    line: int
    property_type: str
    context: str
    inferred_widget: Optional[str] = None


@dataclass
class WidgetMismatch:
    role: str
    widget: str
    expected_widgets: List[str]
    file_path: str
    line: int
    context: str


@dataclass
class RoleAuditReport:
    defined_roles: Dict[str, ThemeDefinition] = field(default_factory=dict)
    defined_states: Dict[str, ThemeDefinition] = field(default_factory=dict)
    used_roles: Dict[str, List[RoleOccurrence]] = field(default_factory=lambda: defaultdict(list))
    used_states: Dict[str, List[RoleOccurrence]] = field(default_factory=lambda: defaultdict(list))
    widget_mismatches: List[WidgetMismatch] = field(default_factory=list)

    @property
    def missing_roles(self) -> Dict[str, List[RoleOccurrence]]:
        return {r: occs for r, occs in self.used_roles.items() if r not in self.defined_roles}

    @property
    def missing_states(self) -> Dict[str, List[RoleOccurrence]]:
        return {s: occs for s, occs in self.used_states.items() if s not in self.defined_states}

    @property
    def unused_roles(self) -> Dict[str, ThemeDefinition]:
        return {r: defn for r, defn in self.defined_roles.items() if r not in self.used_roles}

    @property
    def unused_states(self) -> Dict[str, ThemeDefinition]:
        return {s: defn for s, defn in self.defined_states.items() if s not in self.used_states}

    @property
    def has_errors(self) -> bool:
        return bool(self.missing_roles or self.missing_states)

    @property
    def has_warnings(self) -> bool:
        return bool(self.unused_roles or self.unused_states or self.widget_mismatches)

    @property
    def is_clean(self) -> bool:
        return not self.has_errors and not self.has_warnings


def parse_theme_qss(theme_file: str = THEME_PATH) -> Tuple[Dict[str, ThemeDefinition], Dict[str, ThemeDefinition]]:
    if not os.path.exists(theme_file):
        raise FileNotFoundError(f"theme.py no fue encontrado en: {os.path.abspath(theme_file)}")

    with open(theme_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    defined_roles: Dict[str, ThemeDefinition] = {}
    defined_states: Dict[str, ThemeDefinition] = {}

    role_pattern = re.compile(r'([A-Za-z0-9_]*)\s*\[role=[\"\']?([a-zA-Z0-9_-]+)[\"\']?\]')
    state_pattern = re.compile(r'([A-Za-z0-9_]*)\s*(?:\[role=[\"\']?[a-zA-Z0-9_-]+[\"\']?\])?\s*\[state=[\"\']?([a-zA-Z0-9_-]+)[\"\']?\]')

    for line_idx, line in enumerate(lines, 1):
        for match in role_pattern.finditer(line):
            widget_type = match.group(1) or "*"
            role_name = match.group(2)
            if role_name not in defined_roles:
                defined_roles[role_name] = ThemeDefinition(
                    name=role_name,
                    property_type="role",
                    widget_types=[],
                    line_numbers=[],
                    selectors=[]
                )
            defn = defined_roles[role_name]
            if widget_type not in defn.widget_types:
                defn.widget_types.append(widget_type)
            if line_idx not in defn.line_numbers:
                defn.line_numbers.append(line_idx)
            raw_sel = match.group(0).strip()
            if raw_sel not in defn.selectors:
                defn.selectors.append(raw_sel)

        for match in state_pattern.finditer(line):
            widget_type = match.group(1) or "*"
            state_name = match.group(2)
            if state_name not in defined_states:
                defined_states[state_name] = ThemeDefinition(
                    name=state_name,
                    property_type="state",
                    widget_types=[],
                    line_numbers=[],
                    selectors=[]
                )
            defn = defined_states[state_name]
            if widget_type not in defn.widget_types:
                defn.widget_types.append(widget_type)
            if line_idx not in defn.line_numbers:
                defn.line_numbers.append(line_idx)
            raw_sel = match.group(0).strip()
            if raw_sel not in defn.selectors:
                defn.selectors.append(raw_sel)

    return defined_roles, defined_states


class ASTCodeAuditor(ast.NodeVisitor):
    def __init__(self, file_path: str, lines: List[str], defined_roles: Set[str], defined_states: Set[str]):
        self.file_path = file_path
        self.lines = lines
        self.defined_roles = defined_roles
        self.defined_states = defined_states
        self.parent_stack: List[ast.AST] = []
        self.local_vars: Dict[str, List[str]] = defaultdict(list)
        self.widget_types: Dict[str, str] = {}
        self.occurrences: List[RoleOccurrence] = []

    def visit(self, node: ast.AST):
        self.parent_stack.append(node)
        super().visit(node)
        self.parent_stack.pop()

    def _get_line_text(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def _infer_widget_name(self, target_node: ast.AST) -> Optional[str]:
        name = ""
        if isinstance(target_node, ast.Name):
            name = target_node.id
        elif isinstance(target_node, ast.Attribute):
            name = target_node.attr

        if name in self.widget_types:
            return self.widget_types[name]

        low_name = name.lower()
        if low_name.startswith(("btn_", "button_")):
            return "QPushButton"
        if low_name.startswith(("lbl_", "label_")):
            return "QLabel"
        if low_name.startswith(("card_", "container_", "wrapper_", "box_", "banner_")):
            return "QFrame"
        if low_name.startswith(("combo_", "combobox_")):
            return "QComboBox"
        return None

    def _extract_strings(self, node: ast.AST) -> List[str]:
        values: List[str] = []
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value.strip()
            if v:
                values.append(v)
        elif isinstance(node, ast.Name):
            if node.id in self.local_vars:
                values.extend(self.local_vars[node.id])
        elif isinstance(node, ast.Attribute):
            attr_name = node.attr
            if attr_name in self.local_vars:
                values.extend(self.local_vars[attr_name])
        elif isinstance(node, ast.IfExp):
            values.extend(self._extract_strings(node.body))
            values.extend(self._extract_strings(node.orelse))
        elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for elt in node.elts:
                values.extend(self._extract_strings(elt))
        elif isinstance(node, ast.Dict):
            for k in node.keys:
                if k:
                    values.extend(self._extract_strings(k))
            for val in node.values:
                values.extend(self._extract_strings(val))
        elif isinstance(node, ast.BoolOp):
            for val in node.values:
                values.extend(self._extract_strings(val))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                caller_name = getattr(node.func.value, "attr", None) or getattr(node.func.value, "id", "")
                if caller_name in self.local_vars:
                    values.extend(self.local_vars[caller_name])
            for arg in node.args:
                values.extend(self._extract_strings(arg))
        return values

    def _resolve_values(self, node: ast.AST, expected_type: str) -> List[str]:
        direct_strings = self._extract_strings(node)
        allowed_set = self.defined_roles if expected_type == "role" else self.defined_states
        if direct_strings:
            return [v for v in direct_strings if v in allowed_set]

        if isinstance(node, ast.Name) and node.id in self.local_vars:
            return [v for v in self.local_vars[node.id] if v in allowed_set]

        if isinstance(node, ast.Attribute) and node.attr in self.local_vars:
            return [v for v in self.local_vars[node.attr] if v in allowed_set]

        if isinstance(node, ast.BoolOp):
            res = []
            for v in node.values:
                res.extend(self._resolve_values(v, expected_type))
            return res

        return []

    def _process_assignment(self, targets: List[ast.AST], value: Optional[ast.AST]):
        if value is None:
            return

        assigned_widget = None
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name):
                assigned_widget = value.func.id
            elif isinstance(value.func, ast.Attribute):
                assigned_widget = value.func.attr

        target_names = []
        for target in targets:
            if isinstance(target, ast.Name):
                target_names.append(target.id)
            elif isinstance(target, ast.Attribute):
                target_names.append(target.attr)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        target_names.append(elt.id)
                    elif isinstance(elt, ast.Attribute):
                        target_names.append(elt.attr)

        assigned_strings = self._extract_strings(value)

        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and value.func.attr == "get":
            caller_name = getattr(value.func.value, "attr", None) or getattr(value.func.value, "id", "")
            if caller_name in self.local_vars:
                assigned_strings.extend(self.local_vars[caller_name])
            if value.args:
                key_arg = value.args[0]
                key_id = getattr(key_arg, "id", None) or getattr(key_arg, "attr", None)
                if key_id and caller_name in self.local_vars:
                    for v in self.local_vars[caller_name]:
                        self.local_vars[key_id].append(v)

        for tid in target_names:
            if assigned_widget and assigned_widget.startswith("Q"):
                self.widget_types[tid] = assigned_widget

            for val in assigned_strings:
                if val in self.defined_roles or val in self.defined_states:
                    self.local_vars[tid].append(val)

    def visit_Assign(self, node: ast.Assign):
        self._process_assignment(node.targets, node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self._process_assignment([node.target], node.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        caller_node = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            caller_node = node.func.value

        inferred = self._infer_widget_name(caller_node) if caller_node else None

        if func_name == "setProperty" and len(node.args) >= 2:
            arg0 = node.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                prop_type = arg0.value.lower()
                if prop_type in ("role", "state"):
                    resolved = self._resolve_values(node.args[1], expected_type=prop_type)
                    for v in resolved:
                        self.occurrences.append(RoleOccurrence(
                            role=v,
                            file_path=self.file_path,
                            line=node.lineno,
                            property_type=prop_type,
                            context=self._get_line_text(node.lineno),
                            inferred_widget=inferred
                        ))

        for kw in node.keywords:
            if kw.arg and (kw.arg in ("role", "state") or kw.arg.endswith("_role") or kw.arg.endswith("_state")):
                prop_type = "state" if "state" in kw.arg else "role"
                resolved = self._resolve_values(kw.value, expected_type=prop_type)
                for v in resolved:
                    self.occurrences.append(RoleOccurrence(
                        role=v,
                        file_path=self.file_path,
                        line=node.lineno,
                        property_type=prop_type,
                        context=self._get_line_text(node.lineno),
                        inferred_widget=inferred
                    ))

        if func_name in ("set_dialog_state", "set_state") and node.args:
            is_helper = func_name == "set_state" and isinstance(node.func, ast.Name) and len(node.args) >= 2
            state_arg = node.args[1] if is_helper else node.args[0]
            resolved = self._resolve_values(state_arg, expected_type="state")
            for v in resolved:
                self.occurrences.append(RoleOccurrence(
                    role=v,
                    file_path=self.file_path,
                    line=node.lineno,
                    property_type="state",
                    context=self._get_line_text(node.lineno),
                    inferred_widget=None if is_helper else "QFrame"
                ))

        if func_name == "create_badge":
            resolved = []
            if len(node.args) >= 2:
                resolved.extend(self._resolve_values(node.args[1], expected_type="state"))
            for kw in node.keywords:
                if kw.arg == "state":
                    resolved.extend(self._resolve_values(kw.value, expected_type="state"))
            for v in resolved:
                self.occurrences.append(RoleOccurrence(
                    role=v,
                    file_path=self.file_path,
                    line=node.lineno,
                    property_type="state",
                    context=self._get_line_text(node.lineno),
                    inferred_widget="QFrame"
                ))

        if func_name == "_resolve_role_color" and node.args:
            resolved = self._resolve_values(node.args[0], expected_type="role")
            for v in resolved:
                self.occurrences.append(RoleOccurrence(
                    role=v,
                    file_path=self.file_path,
                    line=node.lineno,
                    property_type="role",
                    context=self._get_line_text(node.lineno),
                    inferred_widget="QPushButton"
                ))

        self.generic_visit(node)


def audit_codebase(frontend_dir: str = FRONTEND_DIR, theme_file: str = THEME_PATH) -> RoleAuditReport:
    if not os.path.isdir(frontend_dir):
        raise FileNotFoundError(f"El directorio frontend no fue encontrado en: {os.path.abspath(frontend_dir)}")

    report = RoleAuditReport()
    defined_roles, defined_states = parse_theme_qss(theme_file)
    report.defined_roles = defined_roles
    report.defined_states = defined_states

    role_names_set = set(defined_roles.keys())
    state_names_set = set(defined_states.keys())

    for root, dirs, files in os.walk(frontend_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue

            full_path = os.path.join(root, f)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    lines = file_obj.readlines()
                content = "".join(lines)
                tree = ast.parse(content, filename=full_path)
                auditor = ASTCodeAuditor(full_path, lines, role_names_set, state_names_set)
                auditor.visit(tree)

                for occ in auditor.occurrences:
                    if occ.property_type == "role":
                        report.used_roles[occ.role].append(occ)
                        if occ.inferred_widget and occ.role in defined_roles:
                            defn = defined_roles[occ.role]
                            if "*" not in defn.widget_types and occ.inferred_widget not in defn.widget_types:
                                report.widget_mismatches.append(WidgetMismatch(
                                    role=occ.role,
                                    widget=occ.inferred_widget,
                                    expected_widgets=defn.widget_types,
                                    file_path=occ.file_path,
                                    line=occ.line,
                                    context=occ.context
                                ))
                    else:
                        report.used_states[occ.role].append(occ)

            except Exception:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    lines = file_obj.readlines()
                for line_idx, line in enumerate(lines, 1):
                    for m in re.finditer(r'setProperty\s*\(\s*[\"\'](role|state)[\"\']\s*,\s*[\"\']([a-zA-Z0-9_-]+)[\"\']\s*\)', line):
                        prop_type = m.group(1)
                        val = m.group(2)
                        occ = RoleOccurrence(
                            role=val,
                            file_path=full_path,
                            line=line_idx,
                            property_type=prop_type,
                            context=line.strip()
                        )
                        if prop_type == "role":
                            report.used_roles[val].append(occ)
                        else:
                            report.used_states[val].append(occ)

    return report


def get_suggestion(target: str, candidates: List[str]) -> Optional[str]:
    matches = difflib.get_close_matches(target, candidates, n=1, cutoff=0.55)
    return matches[0] if matches else None


def print_audit_report(report: RoleAuditReport, mode: str = "all", verbose: bool = False):
    print("=" * 80)
    print(" 🎨  REPORTE DE AUDITORÍA DE ROLES Y ESTADOS QSS (MINIKICK)")
    print("=" * 80)
    print(f"🔹 Roles definidos en theme.py   : {len(report.defined_roles)}")
    print(f"🔹 Roles en uso en el frontend   : {len(report.used_roles)}")
    print(f"🔹 Estados definidos en theme.py : {len(report.defined_states)}")
    print(f"🔹 Estados en uso en el frontend : {len(report.used_states)}")
    print("-" * 80)
    print(f"🔹 Roles faltantes (en código, NO en theme) : {len(report.missing_roles)}")
    print(f"🔹 Estados faltantes (en código, NO en theme): {len(report.missing_states)}")
    print(f"🔸 Roles sin uso (en theme, NO en código)   : {len(report.unused_roles)}")
    print(f"🔸 Estados sin uso (en theme, NO en código)  : {len(report.unused_states)}")
    if report.widget_mismatches:
        print(f"⚠️  Incompatibilidades de tipo Widget/Rol    : {len(report.widget_mismatches)}")
    print("=" * 80)

    show_missing = mode in ("all", "missing")
    show_unused = mode in ("all", "unused")

    missing_roles = report.missing_roles
    missing_states = report.missing_states
    unused_roles = report.unused_roles
    unused_states = report.unused_states

    if show_missing:
        if missing_roles:
            print(f"\n❌ [ERROR] Se encontraron {len(missing_roles)} ROL(ES) FALTANTE(S) (usados en código pero NO definidos en theme.py):")
            for role, occurrences in sorted(missing_roles.items()):
                sugg = get_suggestion(role, list(report.defined_roles.keys()))
                sugg_text = f" -> 💡 ¿Quizás quisiste decir '{sugg}'?" if sugg else ""
                print(f"\n  ➤ Rol: '{role}' ({len(occurrences)} ocurrencia{'s' if len(occurrences) > 1 else ''}){sugg_text}")
                for occ in occurrences[:10]:
                    rel_path = os.path.relpath(occ.file_path, BASE_DIR).replace('\\', '/')
                    print(f"      • {rel_path}:{occ.line} -> {occ.context}")
                if len(occurrences) > 10:
                    print(f"      ... y {len(occurrences) - 10} ocurrencia(s) más")

        if missing_states:
            print(f"\n❌ [ERROR] Se encontraron {len(missing_states)} ESTADO(S) FALTANTE(S) (usados en código pero NO definidos en theme.py):")
            for state, occurrences in sorted(missing_states.items()):
                sugg = get_suggestion(state, list(report.defined_states.keys()))
                sugg_text = f" -> 💡 ¿Quizás quisiste decir '{sugg}'?" if sugg else ""
                print(f"\n  ➤ Estado: '{state}' ({len(occurrences)} ocurrencia{'s' if len(occurrences) > 1 else ''}){sugg_text}")
                for occ in occurrences[:10]:
                    rel_path = os.path.relpath(occ.file_path, BASE_DIR).replace('\\', '/')
                    print(f"      • {rel_path}:{occ.line} -> {occ.context}")
                if len(occurrences) > 10:
                    print(f"      ... y {len(occurrences) - 10} ocurrencia(s) más")

    if report.widget_mismatches and show_missing:
        print(f"\n⚠️  [WIDGET MISMATCH] Se detectaron {len(report.widget_mismatches)} asignaciones de rol sobre tipos de widget incompatibles:")
        for wm in report.widget_mismatches[:5]:
            rel_path = os.path.relpath(wm.file_path, BASE_DIR).replace('\\', '/')
            expected = ", ".join(wm.expected_widgets)
            print(f"  • {rel_path}:{wm.line} -> Rol '{wm.role}' aplicado a '{wm.widget}', pero theme.py lo define para: [{expected}]")

    if show_unused:
        if unused_roles:
            print(f"\n⚠️  [ADVERTENCIA] Se encontraron {len(unused_roles)} ROL(ES) SIN USO en theme.py (definidos en theme.py pero NO utilizados en el frontend):")
            for role_name, defn in sorted(unused_roles.items()):
                widgets = ", ".join(defn.widget_types)
                print(f"\n  ➤ Rol: '{role_name}'")
                print(f"      • Definido para : {widgets}")
                print(f"      • Ubicación     : {defn.location_str}")
                if verbose and defn.selectors:
                    selectors_str = ", ".join(defn.selectors[:3])
                    print(f"      • Selectores    : {selectors_str}")

            print("\n  💡 Recomendación: Estos roles parecen ser código muerto en theme.py y pueden ser eliminados con seguridad (--fix para limpiar).")

        if unused_states:
            print(f"\n⚠️  [ADVERTENCIA] Se encontraron {len(unused_states)} ESTADO(S) SIN USO en theme.py (definidos en theme.py pero NO utilizados en el frontend):")
            for state_name, defn in sorted(unused_states.items()):
                widgets = ", ".join(defn.widget_types)
                print(f"\n  ➤ Estado: '{state_name}'")
                print(f"      • Definido para : {widgets}")
                print(f"      • Ubicación     : {defn.location_str}")
                if verbose and defn.selectors:
                    selectors_str = ", ".join(defn.selectors[:3])
                    print(f"      • Selectores    : {selectors_str}")

            print("\n  💡 Recomendación: Estos estados parecen ser código muerto en theme.py y pueden ser eliminados con seguridad (--fix para limpiar).")

    print("\n" + "-" * 80)
    if report.has_errors:
        print("❌ [AUDITORÍA FALLIDA] Se detectaron definiciones faltantes en theme.py. Corrige los roles/estados no definidos.")
    elif report.has_warnings:
        print("⚠️  [ADVERTENCIA DE AUDITORÍA] Se detectaron anomalías o estilos sin uso en theme.py.")
    else:
        print("✅ [APROBADO] ¡Todos los roles y estados están perfectamente sincronizados! (Sin faltantes ni estilos sin uso)")

    print("=" * 80 + "\n")


def fix_unused_in_theme(report: RoleAuditReport, theme_file: str = THEME_PATH) -> bool:
    if not report.unused_roles and not report.unused_states:
        print("🎉 No hay roles ni estados sin uso que limpiar.")
        return True

    lines_to_remove: Set[int] = set()
    for defn in list(report.unused_roles.values()) + list(report.unused_states.values()):
        lines_to_remove.update(defn.line_numbers)

    with open(theme_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = [line for idx, line in enumerate(lines, 1) if idx not in lines_to_remove]

    with open(theme_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"✅ Se eliminaron {len(lines_to_remove)} líneas de selectores sin uso en {theme_file}.")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auditoría y verificación de roles y estados QSS en MiniKick.")
    parser.add_argument("--check", action="store_true", help="Ejecutar verificación completa (modo CI/desatendido)")
    parser.add_argument("--json", action="store_true", help="Exportar resultados en formato JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar detalles ampliados, incluyendo selectores QSS")
    parser.add_argument("--unused", action="store_true", help="Auditar únicamente roles y estados sin uso en theme.py")
    parser.add_argument("--missing", action="store_true", help="Auditar únicamente roles y estados faltantes en theme.py")
    parser.add_argument("--strict", action="store_true", help="Terminar con código de error 1 si se detecta cualquier estilo faltante o sin uso")
    parser.add_argument("--fix", action="store_true", help="Poda automáticamente definiciones sin uso en theme.py")
    args = parser.parse_args()

    try:
        report = audit_codebase()
    except FileNotFoundError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(2)

    if args.fix:
        fix_unused_in_theme(report)
        report = audit_codebase()

    if args.json:
        data = {
            "summary": {
                "defined_roles_count": len(report.defined_roles),
                "used_roles_count": len(report.used_roles),
                "missing_roles_count": len(report.missing_roles),
                "unused_roles_count": len(report.unused_roles),
                "defined_states_count": len(report.defined_states),
                "used_states_count": len(report.used_states),
                "missing_states_count": len(report.missing_states),
                "unused_states_count": len(report.unused_states),
                "widget_mismatches_count": len(report.widget_mismatches),
                "is_clean": report.is_clean,
            },
            "defined_roles": {
                name: {
                    "widgets": defn.widget_types,
                    "lines": defn.line_numbers,
                    "location": defn.location_str,
                    "selectors": defn.selectors,
                }
                for name, defn in report.defined_roles.items()
            },
            "defined_states": {
                name: {
                    "widgets": defn.widget_types,
                    "lines": defn.line_numbers,
                    "location": defn.location_str,
                    "selectors": defn.selectors,
                }
                for name, defn in report.defined_states.items()
            },
            "missing_roles": {
                r: [{"file": os.path.relpath(o.file_path, BASE_DIR).replace('\\', '/'), "line": o.line, "context": o.context} for o in occs]
                for r, occs in report.missing_roles.items()
            },
            "missing_states": {
                s: [{"file": os.path.relpath(o.file_path, BASE_DIR).replace('\\', '/'), "line": o.line, "context": o.context} for o in occs]
                for s, occs in report.missing_states.items()
            },
            "unused_roles": {
                name: {
                    "widgets": defn.widget_types,
                    "lines": defn.line_numbers,
                    "location": defn.location_str,
                    "selectors": defn.selectors,
                }
                for name, defn in report.unused_roles.items()
            },
            "unused_states": {
                name: {
                    "widgets": defn.widget_types,
                    "lines": defn.line_numbers,
                    "location": defn.location_str,
                    "selectors": defn.selectors,
                }
                for name, defn in report.unused_states.items()
            },
            "widget_mismatches": [
                {
                    "role": wm.role,
                    "widget": wm.widget,
                    "expected_widgets": wm.expected_widgets,
                    "file": os.path.relpath(wm.file_path, BASE_DIR).replace('\\', '/'),
                    "line": wm.line,
                    "context": wm.context
                }
                for wm in report.widget_mismatches
            ]
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        mode = "all"
        if args.unused:
            mode = "unused"
        elif args.missing:
            mode = "missing"

        print_audit_report(report, mode=mode, verbose=args.verbose)

    if report.missing_roles or report.missing_states:
        sys.exit(1)

    if args.strict and (report.unused_roles or report.unused_states):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
