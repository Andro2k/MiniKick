# tests/tools/i18n_manager.py

"""
MiniKick i18n Toolkit & Manager
Robust AST + Regex scanner for auditing, synchronizing, sorting, and cleaning i18n JSON files.
"""

import ast
import json
import os
import re
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

def set_key_by_path(data_dict, path_parts, value):
    if not path_parts:
        return
    head = path_parts[0]
    if len(path_parts) == 1:
        data_dict[head] = value
    else:
        if head not in data_dict or not isinstance(data_dict[head], dict):
            data_dict[head] = {}
        set_key_by_path(data_dict[head], path_parts[1:], value)

def delete_key_by_path(data_dict, path_parts):
    if not path_parts or not isinstance(data_dict, dict):
        return
    head = path_parts[0]
    if len(path_parts) == 1:
        if head in data_dict:
            del data_dict[head]
    else:
        if head in data_dict and isinstance(data_dict[head], dict):
            delete_key_by_path(data_dict[head], path_parts[1:])
            if len(data_dict[head]) == 0:
                del data_dict[head]

def sort_dict_recursively(d):
    if isinstance(d, dict):
        return {k: sort_dict_recursively(v) for k, v in sorted(d.items())}
    elif isinstance(d, list):
        return [sort_dict_recursively(item) for item in d]
    else:
        return d

def get_all_python_files():
    py_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if file.endswith(".py"):
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, BASE_DIR)
                if rel_p not in (os.path.join("tests", "tools", "i18n_manager.py"), "tests/tools/i18n_manager.py"):
                    py_files.append((full_p, rel_p))
    return py_files

def extract_all_keys_from_code(root_namespaces):
    py_files = get_all_python_files()
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
                static_keys.setdefault(m, []).append((rel_path, 1, "regex_fallback"))
            continue

        for node in ast.walk(tree):
            # 1. AST Method Calls: i18n.get(...) / i18n.t(...)
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
                                static_keys.setdefault(key_val, []).append((rel_path, node.lineno, f"kwarg:{kw.arg}"))

            # 2. String literals matching known root namespaces (e.g. 'dashboard.xxx', 'settings.xxx')
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value.strip()
                if "." in val and any(val.startswith(ns + ".") for ns in root_namespaces):
                    if not val.endswith((".", "_")) and not any(val.lower().endswith(ext) for ext in EXCLUDED_EXTS) and " " not in val and "\n" not in val:
                        static_keys.setdefault(val, []).append((rel_path, node.lineno, "namespace_string"))

    return static_keys, dynamic_patterns

def audit_missing_keys_in_code():
    print("\n--- Auditando Claves Faltantes en JSON (Usadas en Código Python) ---")
    if not os.path.exists(EN_PATH) or not os.path.exists(ES_PATH):
        print("[X] Error: Archivos de traducción no encontrados.")
        return {}, {}

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_dict = json.load(f)
    with open(ES_PATH, "r", encoding="utf-8") as f:
        es_dict = json.load(f)

    en_keys = set(get_flattened_keys(en_dict).keys())
    es_keys = set(get_flattened_keys(es_dict).keys())
    root_namespaces = tuple(en_dict.keys())

    static_keys, dynamic_patterns = extract_all_keys_from_code(root_namespaces)

    missing_in_en = {}
    missing_in_es = {}

    for key, occurrences in sorted(static_keys.items()):
        if key not in en_keys:
            missing_in_en[key] = occurrences
        if key not in es_keys:
            missing_in_es[key] = occurrences

    print(f"📊 Total de claves únicas detectadas en código Python: {len(static_keys)}")
    print(f"🔴 Claves faltantes en en.json: {len(missing_in_en)}")
    print(f"🔴 Claves faltantes en es.json: {len(missing_in_es)}")

    if missing_in_en:
        print("\n[!] Claves faltantes en en.json:")
        for k, occs in missing_in_en.items():
            locs = ", ".join([f"{p}:{ln}" for p, ln, _ in occs[:3]])
            print(f"  ❌ {k}  (en {locs})")

    if missing_in_es:
        print("\n[!] Claves faltantes en es.json:")
        for k, occs in missing_in_es.items():
            locs = ", ".join([f"{p}:{ln}" for p, ln, _ in occs[:3]])
            print(f"  ❌ {k}  (en {locs})")

    unmatched_dynamics = []
    for pat, p, line in set(dynamic_patterns):
        regex_pat = "^" + re.sub(r"\{[^\}]+\}", r"[a-zA-Z0-9_]+", pat) + "$"
        matches = [k for k in en_keys if re.match(regex_pat, k)]
        if not matches:
            unmatched_dynamics.append((pat, p, line))

    if unmatched_dynamics:
        print(f"\n⚠️ Claves Dinámicas (f-strings) sin ninguna coincidencia en JSON ({len(unmatched_dynamics)}):")
        for pat, p, line in sorted(unmatched_dynamics):
            print(f"  ⚠️ f\"{pat}\" (en {p}:{line}) -> ¡No existe ninguna clave con este prefijo!")
    elif dynamic_patterns:
        print(f"\n✅ {len(set(dynamic_patterns))} patrones dinámicos (f-strings) validados correctamente contra el JSON.")

    if not missing_in_en and not missing_in_es and not unmatched_dynamics:
        print("\n[OK] ¡Excelente! Todas las claves i18n usadas en el código existen en ambos archivos JSON.")

    return missing_in_en, missing_in_es

def audit_unused_keys():
    print("\n--- Auditando Claves i18n Sin Uso en JSON ---")
    if not os.path.exists(EN_PATH):
        print(f"[X] Error: Archivo no encontrado: {EN_PATH}")
        return [], {}

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    all_keys = get_flattened_keys(en_data)
    root_namespaces = tuple(en_data.keys())

    static_keys, dynamic_patterns = extract_all_keys_from_code(root_namespaces)
    code_keys_set = set(static_keys.keys())

    dynamic_regexes = []
    for pat, _, _ in set(dynamic_patterns):
        regex_pat = "^" + re.sub(r"\{[^\}]+\}", r"[a-zA-Z0-9_]+", pat) + "$"
        dynamic_regexes.append(re.compile(regex_pat))

    truly_unused = []
    dynamically_used = []
    exact_found = []

    for key, val in sorted(all_keys.items()):
        if key in code_keys_set:
            exact_found.append(key)
        else:
            is_dyn = False
            for rx in dynamic_regexes:
                if rx.match(key):
                    is_dyn = True
                    break
            if is_dyn:
                dynamically_used.append(key)
            else:
                truly_unused.append(key)

    print(f"Total claves en {os.path.basename(EN_PATH)}: {len(all_keys)}")
    print(f"Claves encontradas exactamente: {len(exact_found)}")
    print(f"Claves usadas dinámicamente: {len(dynamically_used)}")
    print(f"Claves SIN USO detectadas: {len(truly_unused)}")

    if truly_unused:
        print("\nLista de Claves Sin Uso:")
        for k in truly_unused:
            print(f"  [X] {k}: \"{all_keys[k]}\"")
    else:
        print("\n[OK] ¡Excelente! No se encontraron claves sin uso.")

    return truly_unused, all_keys

def check_key_parity():
    print("\n--- Verificando Paridad de Claves (EN vs ES) ---")
    if not os.path.exists(EN_PATH) or not os.path.exists(ES_PATH):
        print("[X] Error: Archivos de traducción no encontrados.")
        return

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_keys = set(get_flattened_keys(json.load(f)).keys())

    with open(ES_PATH, "r", encoding="utf-8") as f:
        es_keys = set(get_flattened_keys(json.load(f)).keys())

    in_en_not_es = sorted(list(en_keys - es_keys))
    in_es_not_en = sorted(list(es_keys - en_keys))

    print(f"Total claves en EN: {len(en_keys)}")
    print(f"Total claves en ES: {len(es_keys)}")

    if not in_en_not_es and not in_es_not_en:
        print("\n[OK] ¡Paridad del 100%! Ambos archivos tienen exactamente las mismas claves.")
    else:
        if in_en_not_es:
            print(f"\nClaves en EN faltantes en ES ({len(in_en_not_es)}):")
            for k in in_en_not_es:
                print(f"  + EN: {k}")
        if in_es_not_en:
            print(f"\nClaves en ES faltantes en EN ({len(in_es_not_en)}):")
            for k in in_es_not_en:
                print(f"  - ES: {k}")

def sort_json_files():
    print("\n--- Ordenando Archivos JSON Alfabéticamente ---")
    for path in [EN_PATH, ES_PATH]:
        if not os.path.exists(path):
            print(f"[!] Salteando (no existe): {path}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sorted_data = sort_dict_recursively(data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, indent=4, ensure_ascii=False)
            f.write("\n")

        print(f"[OK] {os.path.basename(path)} ordenado alfabéticamente.")

def auto_clean_unused_and_sync():
    print("\n--- Limpieza Automática y Sincronización ---")
    unused_keys, _ = audit_unused_keys()

    if not os.path.exists(EN_PATH) or not os.path.exists(ES_PATH):
        print("[X] Error: Archivos locales no encontrados.")
        return

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    with open(ES_PATH, "r", encoding="utf-8") as f:
        es_data = json.load(f)

    en_keys = set(get_flattened_keys(en_data).keys())
    es_keys = set(get_flattened_keys(es_data).keys())

    keys_to_remove_es = set(unused_keys) | (es_keys - en_keys)

    for key in unused_keys:
        delete_key_by_path(en_data, key.split("."))

    for key in keys_to_remove_es:
        delete_key_by_path(es_data, key.split("."))

    en_sorted = sort_dict_recursively(en_data)
    es_sorted = sort_dict_recursively(es_data)

    with open(EN_PATH, "w", encoding="utf-8") as f:
        json.dump(en_sorted, f, indent=4, ensure_ascii=False)
        f.write("\n")

    with open(ES_PATH, "w", encoding="utf-8") as f:
        json.dump(es_sorted, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print("\n[OK] Limpieza y sincronización completada exitosamente.")

def auto_add_missing_keys():
    print("\n--- Auto-Agregar Claves Faltantes a JSONs ---")
    missing_in_en, missing_in_es = audit_missing_keys_in_code()

    all_missing = set(missing_in_en.keys()) | set(missing_in_es.keys())
    if not all_missing:
        print("\n[OK] No hay claves faltantes que agregar.")
        return

    print(f"\nSe encontraron {len(all_missing)} claves faltantes para agregar.")
    confirm = input("¿Deseas agregarlas automáticamente como placeholders a en.json y es.json? (s/n): ").strip().lower()
    if confirm not in ("s", "si", "y", "yes"):
        print("[!] Operación cancelada.")
        return

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    with open(ES_PATH, "r", encoding="utf-8") as f:
        es_data = json.load(f)

    for k in sorted(all_missing):
        parts = k.split(".")
        last_name = parts[-1].replace("_", " ").title()
        set_key_by_path(en_data, parts, last_name)
        set_key_by_path(es_data, parts, last_name)

    en_sorted = sort_dict_recursively(en_data)
    es_sorted = sort_dict_recursively(es_data)

    with open(EN_PATH, "w", encoding="utf-8") as f:
        json.dump(en_sorted, f, indent=4, ensure_ascii=False)
        f.write("\n")

    with open(ES_PATH, "w", encoding="utf-8") as f:
        json.dump(es_sorted, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"\n[OK] Se agregaron {len(all_missing)} claves exitosamente en ambos archivos.")

def main_menu():
    while True:
        print("\n" + "=" * 55)
        print("         MINI-KICK i18N TOOLKIT & MANAGER")
        print("=" * 55)
        print("1. Auditar claves sin uso en JSON")
        print("2. Auditar claves faltantes en JSON (usadas en código)")
        print("3. Verificar paridad entre idiomas (en.json vs es.json)")
        print("4. Ordenar alfabéticamente (en.json y es.json)")
        print("5. Limpiar claves sin uso y sincronizar archivos")
        print("6. Auto-agregar claves faltantes detectadas en código")
        print("7. Salir")
        print("=" * 55)

        try:
            choice = input("Selecciona una opción (1-7): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Saliendo...")
            break

        if choice == "1":
            audit_unused_keys()
        elif choice == "2":
            audit_missing_keys_in_code()
        elif choice == "3":
            check_key_parity()
        elif choice == "4":
            sort_json_files()
        elif choice == "5":
            auto_clean_unused_and_sync()
        elif choice == "6":
            auto_add_missing_keys()
        elif choice == "7":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("[X] Opción inválida. Intenta nuevamente.")

if __name__ == "__main__":
    main_menu()
