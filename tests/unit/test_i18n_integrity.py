# tests\unit\test_i18n_integrity.py

import ast
import json
import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EN_PATH = os.path.join(BASE_DIR, "locales", "en.json")
ES_PATH = os.path.join(BASE_DIR, "locales", "es.json")

EXCLUDED_EXTS = (
    '.html', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.py',
    '.json', '.db', '.css', '.js', '.ico', '.txt', '.log', '.md'
)

IGNORED_DIRS = {
    '.venv', 'venv', '__pycache__', '.git', '.pytest_cache',
    '.agents', 'build', 'dist', 'walkthroughs'
}

VALID_I18N_OBJECT_NAMES = {
    'i18n', 'i18n_engine', 'translation_service', 'translator',
    '_i18n', 'trans', 'i18n_mgr', 'i18n_manager', 'parent_i18n'
}

def is_i18n_variable_name(name_str: str) -> bool:
    s = name_str.lower()
    if s in VALID_I18N_OBJECT_NAMES:
        return True
    if s.endswith('_i18n') or s.endswith('.i18n') or s.startswith('i18n_'):
        return True
    return False

def get_flattened_keys(data_dict, prefix=""):
    keys = {}
    for k, v in data_dict.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(get_flattened_keys(v, full_key))
        else:
            keys[full_key] = v
    return keys

def test_i18n_files_exist_and_valid_json():
    assert os.path.exists(EN_PATH), f"Missing {EN_PATH}"
    assert os.path.exists(ES_PATH), f"Missing {ES_PATH}"

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    with open(ES_PATH, "r", encoding="utf-8") as f:
        es_data = json.load(f)

    assert isinstance(en_data, dict)
    assert isinstance(es_data, dict)

def test_i18n_key_parity():
    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    with open(ES_PATH, "r", encoding="utf-8") as f:
        es_data = json.load(f)

    en_keys = set(get_flattened_keys(en_data).keys())
    es_keys = set(get_flattened_keys(es_data).keys())

    missing_in_es = en_keys - es_keys
    missing_in_en = es_keys - en_keys

    assert not missing_in_es, f"Keys present in EN but missing in ES: {sorted(list(missing_in_es))}"
    assert not missing_in_en, f"Keys present in ES but missing in EN: {sorted(list(missing_in_en))}"

def test_i18n_keys_used_in_code_exist():
    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_dict = json.load(f)

    en_keys = set(get_flattened_keys(en_dict).keys())
    root_namespaces = tuple(en_dict.keys())

    py_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if file.endswith(".py"):
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, BASE_DIR)
                if rel_p not in (os.path.join("tests", "tools", "i18n_manager.py"), "tests/tools/i18n_manager.py"):
                    py_files.append((full_p, rel_p))

    static_keys = {}
    dynamic_patterns = []

    for full_path, rel_path in py_files:
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        try:
            tree = ast.parse(content, filename=full_path)
        except Exception:
            matches = re.findall(r'(?:i18n|translation_service)\.(?:get|t)\(\s*["\']([^"\'\)]+)["\']', content)
            for m in matches:
                static_keys.setdefault(m, []).append((rel_path, 1))
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
                                static_keys.setdefault(key_val, []).append((rel_path, node.lineno))
                        elif isinstance(arg0, ast.JoinedStr):
                            parts = []
                            for v in arg0.values:
                                if isinstance(v, ast.Constant):
                                    parts.append(str(v.value))
                                else:
                                    parts.append("{var}")
                            dyn_str = "".join(parts)
                            dynamic_patterns.append((dyn_str, rel_path, node.lineno))

                    for kw in node.keywords:
                        if kw.arg in ("key", "k", "msg_key") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            key_val = kw.value.value.strip()
                            if key_val and not key_val.endswith((".", "_")):
                                static_keys.setdefault(key_val, []).append((rel_path, node.lineno))

            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value.strip()
                if "." in val and any(val.startswith(ns + ".") for ns in root_namespaces):
                    if not val.endswith((".", "_")) and not any(val.lower().endswith(ext) for ext in EXCLUDED_EXTS) and " " not in val and "\n" not in val:
                        static_keys.setdefault(val, []).append((rel_path, node.lineno))

    missing_in_en = {k: v for k, v in static_keys.items() if k not in en_keys}

    error_msgs = []
    if missing_in_en:
        for k, occs in sorted(missing_in_en.items()):
            locs = ", ".join([f"{p}:{ln}" for p, ln in occs[:2]])
            error_msgs.append(f"  - '{k}' (used in {locs})")

    unmatched_dynamics = []
    for pat, p, line in set(dynamic_patterns):
        regex_pat = "^" + re.sub(r"\{[^\}]+\}", r"[a-zA-Z0-9_]+", pat) + "$"
        matches = [k for k in en_keys if re.match(regex_pat, k)]
        if not matches:
            unmatched_dynamics.append(f"  - Pattern f'{pat}' (used in {p}:{line})")

    if unmatched_dynamics:
        error_msgs.append("Dynamic f-strings with no matching keys in en.json:\n" + "\n".join(unmatched_dynamics))

    assert not error_msgs, f"Keys used in python code missing from translation files:\n" + "\n".join(error_msgs)
