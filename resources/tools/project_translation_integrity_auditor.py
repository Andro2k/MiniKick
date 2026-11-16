# resources\tools\project_translation_integrity_auditor.py
"""Auditor de integridad de las traducciones (paridad y limpieza de claves)."""

import ast
import contextlib
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set

from fluent.syntax import FluentParser, ast as fluent_ast

class DataLoader:
    EXCLUDED_EXTS = {".html", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".py", ".json", ".ftl", ".db", ".css", ".js", ".ico", ".txt", ".log", ".md", ".com", ".tv", ".be", ".net", ".org"}
    IGNORED_DIRS = {".venv", "venv", "__pycache__", ".git", ".pytest_cache", ".agents", "build", "dist", "walkthroughs", "tools"}

    @staticmethod
    def load_ftl(path: Path):
        text = path.read_text(encoding="utf-8")
        return text, FluentParser(with_spans=True).parse(text)

    @staticmethod
    def flatten_ftl(resource) -> Dict[str, str]:
        """id `a-b-c` -> clave `a.b.c`; el valor deja las variables como `{nombre}`."""
        return {
            entry.id.name.replace("-", "."): DataLoader._pattern_text(entry.value)
            for entry in resource.body
            if isinstance(entry, fluent_ast.Message) and entry.value is not None
        }

    @staticmethod
    def _pattern_text(pattern) -> str:
        parts = []
        for element in pattern.elements:
            if isinstance(element, fluent_ast.TextElement):
                parts.append(element.value)
            else:
                parts.append(DataLoader._expression_text(element.expression))
        return "".join(parts)

    @staticmethod
    def _expression_text(expression) -> str:
        if isinstance(expression, fluent_ast.VariableReference):
            return "{%s}" % expression.id.name
        if isinstance(expression, fluent_ast.StringLiteral):
            return expression.parse()["value"]
        if isinstance(expression, fluent_ast.SelectExpression):
            default = next(variant for variant in expression.variants if variant.default)
            return DataLoader._pattern_text(default.value)
        if isinstance(expression, fluent_ast.Placeable):
            return DataLoader._expression_text(expression.expression)
        return ""

    @staticmethod
    def remove_ftl_keys(path: Path, text: str, resource, keys: Set[str]) -> None:
        spans = sorted(
            (
                (entry.span.start, entry.span.end)
                for entry in resource.body
                if isinstance(entry, fluent_ast.Message) and entry.id.name.replace("-", ".") in keys
            ),
            reverse=True,
        )
        for start, end in spans:
            end += 1 if text[end:end + 1] == "\n" else 0
            text = text[:start] + text[end:]
        path.write_text(text, encoding="utf-8", newline="\n")

    @staticmethod
    def get_python_files(base_dir: Path) -> List[Tuple[Path, str]]:
        py_files = []
        for file_path in base_dir.rglob("*.py"):
            if any(part in DataLoader.IGNORED_DIRS for part in file_path.parts):
                continue
            if file_path.name != "project_translation_integrity_auditor.py":
                rel_p = file_path.relative_to(base_dir).as_posix()
                py_files.append((file_path, rel_p))
        return py_files


class AuditorService:
    VALID_I18N_OBJECT_NAMES = {"i18n", "i18n_engine", "translation_service", "translator", "_i18n", "trans", "i18n_mgr", "i18n_manager", "parent_i18n"}
    PLACEHOLDER_REGEX = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    @staticmethod
    def is_i18n_var(name_str: str) -> bool:
        s = name_str.lower()
        return s in AuditorService.VALID_I18N_OBJECT_NAMES or s.endswith("_i18n") or s.endswith(".i18n") or s.startswith("i18n_")

    @staticmethod
    def extract_code_keys(py_files: List[Tuple[Path, str]], root_namespaces: Tuple[str, ...]) -> Tuple[Dict[str, List[Tuple[str, int]]], List[Tuple[str, str, int]]]:
        static_keys: Dict[str, List[Tuple[str, int]]] = {}
        dynamic_patterns: List[Tuple[str, str, int]] = []

        for full_path, rel_path in py_files:
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content, filename=str(full_path))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    is_i18n = False
                    if isinstance(func, ast.Attribute) and func.attr in ("get", "t"):
                        val = func.value
                        if isinstance(val, ast.Name) and AuditorService.is_i18n_var(val.id):
                            is_i18n = True
                        elif isinstance(val, ast.Attribute) and AuditorService.is_i18n_var(val.attr):
                            is_i18n = True

                    if is_i18n and node.args:
                        arg0 = node.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            k_val = arg0.value.strip()
                            if k_val and not k_val.endswith((".", "_")):
                                static_keys.setdefault(k_val, []).append((rel_path, node.lineno))
                        elif isinstance(arg0, ast.JoinedStr):
                            parts = [str(v.value) if isinstance(v, ast.Constant) else "{var}" for v in arg0.values]
                            dynamic_patterns.append(("".join(parts), rel_path, node.lineno))

                if isinstance(node, ast.JoinedStr) and node.values and isinstance(node.values[0], ast.Constant):
                    head = str(node.values[0].value)
                    if any(head.startswith(ns + ".") for ns in root_namespaces):
                        pattern = "".join(str(v.value) if isinstance(v, ast.Constant) else "{var}" for v in node.values)
                        dynamic_patterns.append((pattern, rel_path, node.lineno))

                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val = node.value.strip()
                    if "." in val and any(val.startswith(ns + ".") for ns in root_namespaces):
                        if not val.endswith((".", "_")) and " " not in val and "\n" not in val:
                            if not any(val.lower().endswith(ext) for ext in DataLoader.EXCLUDED_EXTS):
                                static_keys.setdefault(val, []).append((rel_path, node.lineno))

        return static_keys, dynamic_patterns

    @staticmethod
    def find_missing_keys(static_keys: Dict[str, List[Tuple[str, int]]], target_keys: Set[str]) -> Dict[str, List[Tuple[str, int]]]:
        return {k: locs for k, locs in static_keys.items() if k not in target_keys}

    @staticmethod
    def find_unused_keys(ftl_keys: Set[str], code_keys: Set[str], dyn_patterns: List[Tuple[str, str, int]]) -> Set[str]:
        regexes = [re.compile("^" + re.sub(r"\{[^\}]+\}", r"[a-zA-Z0-9_]+", pat) + "$") for pat, _, _ in set(dyn_patterns)]
        unused = ftl_keys - code_keys
        return {k for k in unused if not any(rx.match(k) for rx in regexes)}

    @staticmethod
    def find_placeholder_discrepancies(en_flat: Dict[str, Any], es_flat: Dict[str, Any]) -> List[Dict[str, Any]]:
        common = set(en_flat.keys()) & set(es_flat.keys())
        discrepancies = []
        for k in sorted(common):
            p_en = set(AuditorService.PLACEHOLDER_REGEX.findall(str(en_flat[k])))
            p_es = set(AuditorService.PLACEHOLDER_REGEX.findall(str(es_flat[k])))
            if p_en != p_es:
                discrepancies.append({
                    "key": k,
                    "missing_in_es": sorted(list(p_en - p_es)),
                    "missing_in_en": sorted(list(p_es - p_en))
                })
        return discrepancies


class ConsoleReporter:
    @staticmethod
    def print_missing(missing: Dict[str, List[Tuple[str, int]]], lang: str):
        if not missing:
            print(f"[OK] No hay claves faltantes en {lang}.")
            return
        print(f"\n🔴 Claves faltantes en {lang} ({len(missing)}):")
        for key, locations in missing.items():
            print(f"  - Clave i18n: '{key}'")
            for path, line in sorted(set(locations)): 
                print(f"    -> Archivo: {path} | Línea: {line}")

    @staticmethod
    def print_unused(unused: Set[str]):
        if not unused:
            return
        print(f"\n🟡 Claves SIN USO en los archivos .ftl ({len(unused)}):")
        for k in sorted(unused):
            print(f"  - '{k}'")

    @staticmethod
    def print_discrepancies(discrepancies: List[Dict[str, Any]]):
        if not discrepancies:
            return
        print(f"\n🟠 Diferencias en Placeholders ({len(discrepancies)}):")
        for d in discrepancies:
            print(f"  - Clave '{d['key']}':")
            if d['missing_in_es']:
                print(f"    -> Faltan variables en ES: {d['missing_in_es']}")
            if d['missing_in_en']:
                print(f"    -> Faltan variables en EN: {d['missing_in_en']}")


def _resolve_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "assets" / "i18n").exists() and (parent / "frontend").exists():
            return parent
    return Path(__file__).resolve().parents[3]

def main():
    base_dir = _resolve_project_root()
    en_path = base_dir / "assets" / "i18n" / "en" / "main.ftl"
    es_path = base_dir / "assets" / "i18n" / "es" / "main.ftl"

    if not en_path.exists() or not es_path.exists():
        print("Error: No se encontraron los archivos (en/main.ftl / es/main.ftl).")
        sys.exit(1)

    en_text, en_resource = DataLoader.load_ftl(en_path)
    es_text, es_resource = DataLoader.load_ftl(es_path)
    en_flat = DataLoader.flatten_ftl(en_resource)
    es_flat = DataLoader.flatten_ftl(es_resource)

    en_keys_set = set(en_flat.keys())
    es_keys_set = set(es_flat.keys())
    root_namespaces = tuple(sorted({key.split(".", 1)[0] for key in en_flat}))

    py_files = DataLoader.get_python_files(base_dir)

    static_keys, dynamic_patterns = AuditorService.extract_code_keys(py_files, root_namespaces)
    code_keys_set = set(static_keys.keys())

    missing_in_en = AuditorService.find_missing_keys(static_keys, en_keys_set)
    missing_in_es = AuditorService.find_missing_keys(static_keys, es_keys_set)
    unused_keys = AuditorService.find_unused_keys(en_keys_set, code_keys_set, dynamic_patterns)
    placeholders = AuditorService.find_placeholder_discrepancies(en_flat, es_flat)

    print("\n=== REPORTE DE AUDITORÍA I18N ===")
    ConsoleReporter.print_missing(missing_in_en, "en/main.ftl")
    ConsoleReporter.print_missing(missing_in_es, "es/main.ftl")
    ConsoleReporter.print_unused(unused_keys)
    ConsoleReporter.print_discrepancies(placeholders)

    if unused_keys:
        print("\n=== MENÚ DE ACCIONES ===")
        try:
            opcion = input("¿Deseas eliminar las claves sobrantes (sin uso) de los archivos .ftl? (s/n): ").strip().lower()
            if opcion in ['s', 'si', 'sí', 'y', 'yes']:
                DataLoader.remove_ftl_keys(en_path, en_text, en_resource, unused_keys)
                DataLoader.remove_ftl_keys(es_path, es_text, es_resource, unused_keys)
                print("[OK] Claves sobrantes eliminadas y archivos actualizados correctamente.")
            else:
                print("[INFO] No se realizaron cambios en los archivos .ftl.")
        except KeyboardInterrupt:
            print("\n[INFO] Operación cancelada por el usuario.")

    if missing_in_en or missing_in_es or placeholders:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")
    main()