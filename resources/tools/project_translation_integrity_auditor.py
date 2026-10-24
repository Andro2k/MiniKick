# resources/tools/project_translation_integrity_auditor.py

import argparse
import ast
import contextlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")


def _resolve_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "locales").exists() and (parent / "frontend").exists():
            return parent
    return Path(__file__).resolve().parents[3]


BASE_DIR = _resolve_project_root()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

EN_PATH = BASE_DIR / "locales" / "en.json"
ES_PATH = BASE_DIR / "locales" / "es.json"

EXCLUDED_EXTS = (
    ".html", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".py",
    ".json", ".db", ".css", ".js", ".ico", ".txt", ".log", ".md"
)

IGNORED_DIRS = {
    ".venv", "venv", "__pycache__", ".git", ".pytest_cache",
    ".agents", "build", "dist", "walkthroughs", "tools"
}

VALID_I18N_OBJECT_NAMES = {
    "i18n", "i18n_engine", "translation_service", "translator",
    "_i18n", "trans", "i18n_mgr", "i18n_manager", "parent_i18n"
}

PLACEHOLDER_REGEX = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def is_i18n_variable_name(name_str: str) -> bool:
    s = name_str.lower()
    return s in VALID_I18N_OBJECT_NAMES or s.endswith("_i18n") or s.endswith(".i18n") or s.startswith("i18n_")


def get_flattened_keys(data_dict: dict, prefix: str = "") -> Dict[str, Any]:
    keys = {}
    for k, v in data_dict.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(get_flattened_keys(v, full_key))
        else:
            keys[full_key] = v
    return keys


def set_key_by_path(data_dict: dict, path_parts: List[str], value: Any) -> None:
    if not path_parts:
        return
    head = path_parts[0]
    if len(path_parts) == 1:
        data_dict[head] = value
    else:
        if head not in data_dict or not isinstance(data_dict[head], dict):
            data_dict[head] = {}
        set_key_by_path(data_dict[head], path_parts[1:], value)


def delete_key_by_path(data_dict: dict, path_parts: List[str]) -> None:
    if not path_parts or not isinstance(data_dict, dict):
        return
    head = path_parts[0]
    if len(path_parts) == 1:
        data_dict.pop(head, None)
    else:
        if head in data_dict and isinstance(data_dict[head], dict):
            delete_key_by_path(data_dict[head], path_parts[1:])
            if not data_dict[head]:
                del data_dict[head]


def sort_dict_recursively(d: Any) -> Any:
    if isinstance(d, dict):
        return {k: sort_dict_recursively(v) for k, v in sorted(d.items())}
    if isinstance(d, list):
        return [sort_dict_recursively(item) for item in d]
    return d


def get_all_python_files() -> List[Tuple[Path, str]]:
    py_files = []
    for file_path in BASE_DIR.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue
        rel_p = file_path.relative_to(BASE_DIR).as_posix()
        if file_path.name not in {
            "project_translation_integrity_auditor.py",
            "i18n_manager.py",
        }:
            py_files.append((file_path, rel_p))
    return py_files


def extract_all_keys_from_code(root_namespaces: Tuple[str, ...]) -> Tuple[Dict[str, List[Tuple[str, int, str]]], List[Tuple[str, str, int]]]:
    py_files = get_all_python_files()
    static_keys: Dict[str, List[Tuple[str, int, str]]] = {}
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
                is_i18n_call = False
                if isinstance(func, ast.Attribute) and func.attr in ("get", "t"):
                    val = func.value
                    if isinstance(val, ast.Name) and is_i18n_variable_name(val.id):
                        is_i18n_call = True
                    elif isinstance(val, ast.Attribute) and is_i18n_variable_name(val.attr):
                        is_i18n_call = True

                if is_i18n_call:
                    if node.args:
                        arg0 = node.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            key_val = arg0.value.strip()
                            if key_val and not key_val.endswith((".", "_")):
                                static_keys.setdefault(key_val, []).append((rel_path, node.lineno, "i18n.get()"))
                        elif isinstance(arg0, ast.JoinedStr):
                            parts = [str(v.value) if isinstance(v, ast.Constant) else "{var}" for v in arg0.values]
                            dynamic_patterns.append(("".join(parts), rel_path, node.lineno))

            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value.strip()
                if "." in val and any(val.startswith(ns + ".") for ns in root_namespaces):
                    if not val.endswith((".", "_")) and not any(val.lower().endswith(ext) for ext in EXCLUDED_EXTS) and " " not in val and "\n" not in val:
                        static_keys.setdefault(val, []).append((rel_path, node.lineno, "namespace_string"))

    return static_keys, dynamic_patterns


def audit_missing_keys_in_code(quiet: bool = False) -> Tuple[Dict[str, List[Tuple[str, int, str]]], Dict[str, List[Tuple[str, int, str]]]]:
    if not quiet:
        print("\n--- Auditando Claves Faltantes en JSON (Usadas en Código Python) ---")
    if not EN_PATH.exists() or not ES_PATH.exists():
        if not quiet:
            print("[X] Error: Archivos de traducción no encontrados.")
        return {}, {}

    en_dict = json.loads(EN_PATH.read_text(encoding="utf-8"))
    es_dict = json.loads(ES_PATH.read_text(encoding="utf-8"))

    en_keys = set(get_flattened_keys(en_dict).keys())
    es_keys = set(get_flattened_keys(es_dict).keys())
    root_namespaces = tuple(en_dict.keys())

    static_keys, dynamic_patterns = extract_all_keys_from_code(root_namespaces)
    missing_in_en = {k: v for k, v in static_keys.items() if k not in en_keys}
    missing_in_es = {k: v for k, v in static_keys.items() if k not in es_keys}

    if not quiet:
        print(f"📊 Total de claves únicas detectadas en código Python: {len(static_keys)}")
        print(f"🔴 Claves faltantes en en.json: {len(missing_in_en)}")
        print(f"🔴 Claves faltantes en es.json: {len(missing_in_es)}")

        if not (missing_in_en or missing_in_es):
            print("\n[OK] ¡Excelente! Todas las claves i18n usadas en el código existen en ambos archivos JSON.")

    return missing_in_en, missing_in_es


def audit_unused_keys(quiet: bool = False) -> Tuple[List[str], Dict[str, Any]]:
    if not quiet:
        print("\n--- Auditando Claves i18n Sin Uso en JSON ---")
    if not EN_PATH.exists():
        return [], {}

    en_data = json.loads(EN_PATH.read_text(encoding="utf-8"))
    all_keys = get_flattened_keys(en_data)
    root_namespaces = tuple(en_data.keys())

    static_keys, dynamic_patterns = extract_all_keys_from_code(root_namespaces)
    code_keys_set = set(static_keys.keys())

    dynamic_regexes = [re.compile("^" + re.sub(r"\{[^\}]+\}", r"[a-zA-Z0-9_]+", pat) + "$") for pat, _, _ in set(dynamic_patterns)]
    truly_unused = [k for k in sorted(all_keys.keys()) if k not in code_keys_set and not any(rx.match(k) for rx in dynamic_regexes)]

    if not quiet:
        print(f"Total claves en {EN_PATH.name}: {len(all_keys)}")
        print(f"Claves SIN USO detectadas: {len(truly_unused)}")

    return truly_unused, all_keys


def check_key_parity(quiet: bool = False) -> Tuple[List[str], List[str]]:
    if not quiet:
        print("\n--- Verificando Paridad de Claves (EN vs ES) ---")
    if not EN_PATH.exists() or not ES_PATH.exists():
        return [], []

    en_keys = set(get_flattened_keys(json.loads(EN_PATH.read_text(encoding="utf-8"))).keys())
    es_keys = set(get_flattened_keys(json.loads(ES_PATH.read_text(encoding="utf-8"))).keys())

    in_en_not_es = sorted(list(en_keys - es_keys))
    in_es_not_en = sorted(list(es_keys - en_keys))

    if not quiet:
        print(f"Total claves en EN: {len(en_keys)}")
        print(f"Total claves en ES: {len(es_keys)}")
        if not in_en_not_es and not in_es_not_en:
            print("\n[OK] ¡Paridad del 100%! Ambos archivos tienen exactamente las mismas claves.")

    return in_en_not_es, in_es_not_en


def audit_placeholder_parity(quiet: bool = False) -> List[Dict[str, Any]]:
    if not EN_PATH.exists() or not ES_PATH.exists():
        return []

    en_flat = get_flattened_keys(json.loads(EN_PATH.read_text(encoding="utf-8")))
    es_flat = get_flattened_keys(json.loads(ES_PATH.read_text(encoding="utf-8")))

    common_keys = sorted(set(en_flat.keys()) & set(es_flat.keys()))
    discrepancies = []

    for k in common_keys:
        placeholders_en = set(PLACEHOLDER_REGEX.findall(str(en_flat[k])))
        placeholders_es = set(PLACEHOLDER_REGEX.findall(str(es_flat[k])))
        if placeholders_en != placeholders_es:
            discrepancies.append({
                "key": k,
                "missing_in_es": sorted(list(placeholders_en - placeholders_es)),
                "missing_in_en": sorted(list(placeholders_es - placeholders_en)),
            })

    return discrepancies


def run_full_check(strict: bool = False, json_output: bool = False) -> int:
    missing_en, missing_es = audit_missing_keys_in_code(quiet=json_output)
    in_en_not_es, in_es_not_en = check_key_parity(quiet=json_output)
    placeholders = audit_placeholder_parity(quiet=json_output)
    unused_keys, _ = audit_unused_keys(quiet=json_output)

    has_critical = bool(missing_en or missing_es or in_en_not_es or in_es_not_en or placeholders)
    if json_output:
        print(json.dumps({
            "status": "PASS" if not has_critical and (not strict or not unused_keys) else "FAIL",
            "missing_keys_en": len(missing_en),
            "missing_keys_es": len(missing_es),
            "unused_keys": len(unused_keys),
        }, indent=2))

    return 1 if (has_critical or (strict and unused_keys)) else 0


def main():
    parser = argparse.ArgumentParser(description="Audita paridad, placeholders y uso de claves de locales en el proyecto.")
    parser.add_argument("--check", action="store_true", help="Auditoría integral no-bloqueante")
    parser.add_argument("--json", action="store_true", help="Exportar resultados en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Fallar con código 1 ante advertencias")

    args = parser.parse_args()
    if args.check:
        sys.exit(run_full_check(strict=args.strict, json_output=args.json))

    sys.exit(run_full_check(strict=args.strict, json_output=args.json))


if __name__ == "__main__":
    main()
