# tests/tools/role_manager.py

import ast
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
THEME_PATH = os.path.join(BASE_DIR, "frontend", "common", "theme.py")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

IGNORED_DIRS = {
    '.venv', 'venv', '__pycache__', '.git', '.pytest_cache',
    '.agents', 'build', 'dist', 'walkthroughs', 'locales'
}

@dataclass
class RoleOccurrence:
    role: str
    file_path: str
    line: int
    property_type: str
    context: str

@dataclass
class RoleAuditReport:
    defined_roles: Dict[str, List[str]] = field(default_factory=dict)
    defined_states: Dict[str, List[str]] = field(default_factory=dict)
    used_roles: Dict[str, List[RoleOccurrence]] = field(default_factory=lambda: defaultdict(list))
    used_states: Dict[str, List[RoleOccurrence]] = field(default_factory=lambda: defaultdict(list))
    
    @property
    def missing_roles(self) -> Dict[str, List[RoleOccurrence]]:
        return {r: occs for r, occs in self.used_roles.items() if r not in self.defined_roles}

    @property
    def missing_states(self) -> Dict[str, List[RoleOccurrence]]:
        return {s: occs for s, occs in self.used_states.items() if s not in self.defined_states}

    @property
    def unused_roles(self) -> Set[str]:
        return set(self.defined_roles.keys()) - set(self.used_roles.keys())

    @property
    def unused_states(self) -> Set[str]:
        return set(self.defined_states.keys()) - set(self.used_states.keys())


def parse_theme_qss(theme_file: str = THEME_PATH) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    if not os.path.exists(theme_file):
        print(f"[ERROR] theme.py not found at: {theme_file}", file=sys.stderr)
        return {}, {}

    with open(theme_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    defined_roles: Dict[str, List[str]] = defaultdict(list)
    defined_states: Dict[str, List[str]] = defaultdict(list)

    role_pattern = re.compile(r'([A-Za-z0-9_]*)\s*\[role=[\"\']?([a-zA-Z0-9_-]+)[\"\']?\]')
    for match in role_pattern.finditer(content):
        widget_type = match.group(1) or "*"
        role_name = match.group(2)
        if widget_type not in defined_roles[role_name]:
            defined_roles[role_name].append(widget_type)

    state_pattern = re.compile(r'([A-Za-z0-9_]*)\s*(?:\[role=[\"\']?[a-zA-Z0-9_-]+[\"\']?\])?\s*\[state=[\"\']?([a-zA-Z0-9_-]+)[\"\']?\]')
    for match in state_pattern.finditer(content):
        widget_type = match.group(1) or "*"
        state_name = match.group(2)
        if widget_type not in defined_states[state_name]:
            defined_states[state_name].append(widget_type)

    return dict(defined_roles), dict(defined_states)


class ASTCodeAuditor(ast.NodeVisitor):
    def __init__(self, file_path: str, lines: List[str]):
        self.file_path = file_path
        self.lines = lines
        self.occurrences: List[RoleOccurrence] = []

    def _get_line_text(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "setProperty":
            if len(node.args) >= 2:
                arg0 = node.args[0]
                arg1 = node.args[1]
                if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                    prop_name = arg0.value.lower()
                    if prop_name in ("role", "state"):
                        if isinstance(arg1, ast.Constant) and isinstance(arg1.value, str):
                            val = arg1.value.strip()
                            if val:
                                self.occurrences.append(RoleOccurrence(
                                    role=val,
                                    file_path=self.file_path,
                                    line=node.lineno,
                                    property_type=prop_name,
                                    context=self._get_line_text(node.lineno)
                                ))

        for kw in node.keywords:
            if kw.arg in ("role", "state"):
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    val = kw.value.value.strip()
                    if val:
                        self.occurrences.append(RoleOccurrence(
                            role=val,
                            file_path=self.file_path,
                            line=node.lineno,
                            property_type=kw.arg,
                            context=self._get_line_text(node.lineno)
                        ))

        self.generic_visit(node)


def audit_codebase(root_dir: str = FRONTEND_DIR) -> RoleAuditReport:
    """Scans all python files and builds a comprehensive audit report."""
    defined_roles, defined_states = parse_theme_qss(THEME_PATH)
    report = RoleAuditReport(defined_roles=defined_roles, defined_states=defined_states)

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if not file.endswith(".py"):
                continue

            full_path = os.path.join(root, file)
            if os.path.abspath(full_path) == os.path.abspath(THEME_PATH):
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines()

                tree = ast.parse(content, filename=full_path)
                auditor = ASTCodeAuditor(full_path, lines)
                auditor.visit(tree)

                for occ in auditor.occurrences:
                    if occ.property_type == "role":
                        report.used_roles[occ.role].append(occ)
                    elif occ.property_type == "state":
                        report.used_states[occ.role].append(occ)

            except Exception as e:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                for line_idx, line in enumerate(lines, 1):
                    for m in re.finditer(r'setProperty\s*\(\s*[\"\'](role|state)[\"\']\s*,\s*[\"\']([a-zA-Z0-9_-]+)[\"\']\s*\)', line):
                        prop_type = m.group(1)
                        val = m.group(2)
                        occ = RoleOccurrence(role=val, file_path=full_path, line=line_idx, property_type=prop_type, context=line.strip())
                        if prop_type == "role":
                            report.used_roles[val].append(occ)
                        else:
                            report.used_states[val].append(occ)

    return report


def print_audit_report(report: RoleAuditReport, verbose: bool = False):
    """Formats and prints an elegant terminal report."""
    print("=" * 80)
    print(" 🎨  MINIKICK QSS ROLE & PROPERTY AUDIT REPORT")
    print("=" * 80)
    print(f"🔹 Defined Roles in theme.py  : {len(report.defined_roles)}")
    print(f"🔹 Used Roles in Codebase     : {len(report.used_roles)}")
    print(f"🔹 Defined States in theme.py : {len(report.defined_states)}")
    print(f"🔹 Used States in Codebase    : {len(report.used_states)}")
    print("-" * 80)

    missing_roles = report.missing_roles
    missing_states = report.missing_states

    if not missing_roles and not missing_states:
        print("\n✅ [PASS] All roles and states used in the codebase are validly defined in theme.py!\n")
    else:
        if missing_roles:
            print(f"\n❌ [ERROR] Found {len(missing_roles)} MISSING ROLE(S) (used in code but NOT in theme.py):")
            for role, occurrences in sorted(missing_roles.items()):
                print(f"\n  ➤ Role: '{role}' ({len(occurrences)} occurrence{'s' if len(occurrences) > 1 else ''})")
                for occ in occurrences:
                    rel_path = os.path.relpath(occ.file_path, BASE_DIR)
                    print(f"      • {rel_path}:{occ.line} -> {occ.context}")

        if missing_states:
            print(f"\n⚠️  [WARNING] Found {len(missing_states)} MISSING STATE(S) (used in code but NOT in theme.py):")
            for state, occurrences in sorted(missing_states.items()):
                print(f"\n  ➤ State: '{state}' ({len(occurrences)} occurrence{'s' if len(occurrences) > 1 else ''})")
                for occ in occurrences:
                    rel_path = os.path.relpath(occ.file_path, BASE_DIR)
                    print(f"      • {rel_path}:{occ.line} -> {occ.context}")

    if verbose:
        unused_roles = report.unused_roles
        if unused_roles:
            print(f"\nℹ️  [INFO] Unused Roles in theme.py ({len(unused_roles)}):")
            for r in sorted(unused_roles):
                widgets = ", ".join(report.defined_roles[r])
                print(f"   - {r} (defined for: {widgets})")

    print("\n" + "=" * 80 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit and verify QSS roles in MiniKick.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose details including unused roles")
    args = parser.parse_args()

    report = audit_codebase()

    if args.json:
        data = {
            "summary": {
                "defined_roles_count": len(report.defined_roles),
                "used_roles_count": len(report.used_roles),
                "missing_roles_count": len(report.missing_roles),
                "defined_states_count": len(report.defined_states),
                "used_states_count": len(report.used_states),
                "missing_states_count": len(report.missing_states),
            },
            "defined_roles": report.defined_roles,
            "defined_states": report.defined_states,
            "missing_roles": {
                r: [{"file": os.path.relpath(o.file_path, BASE_DIR), "line": o.line, "context": o.context} for o in occs]
                for r, occs in report.missing_roles.items()
            },
            "missing_states": {
                s: [{"file": os.path.relpath(o.file_path, BASE_DIR), "line": o.line, "context": o.context} for o in occs]
                for s, occs in report.missing_states.items()
            },
            "unused_roles": sorted(list(report.unused_roles)),
            "unused_states": sorted(list(report.unused_states)),
        }
        print(json.dumps(data, indent=2))
    else:
        print_audit_report(report, verbose=args.verbose)

    if report.missing_roles:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
