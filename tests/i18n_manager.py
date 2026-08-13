"""
i18n Manager Utility Tool
Provides an interactive menu for auditing, synchronizing, sorting, and cleaning i18n JSON files.
"""

import json
import os
import re
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EN_PATH = os.path.join(BASE_DIR, "locales", "en.json")
ES_PATH = os.path.join(BASE_DIR, "locales", "es.json")

def get_flattened_keys(data_dict, prefix=""):
    keys = {}
    for k, v in data_dict.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(get_flattened_keys(v, full_key))
        else:
            keys[full_key] = v
    return keys

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

def load_codebase_content():
    target_paths = [
        os.path.join(BASE_DIR, "frontend"),
        os.path.join(BASE_DIR, "backend"),
        os.path.join(BASE_DIR, "main.py"),
    ]
    code_contents = []
    for tp in target_paths:
        if os.path.isfile(tp):
            try:
                with open(tp, "r", encoding="utf-8", errors="ignore") as f:
                    code_contents.append(f.read())
            except Exception:
                pass
        elif os.path.isdir(tp):
            for root, _, files in os.walk(tp):
                if any(x in root for x in ["__pycache__", ".venv", "venv"]):
                    continue
                for file in files:
                    if file.endswith(".py"):
                        path = os.path.join(root, file)
                        try:
                            with open(
                                path, "r", encoding="utf-8", errors="ignore"
                            ) as f:
                                code_contents.append(f.read())
                        except Exception:
                            pass
    return "\n".join(code_contents)

def audit_unused_keys():
    print("\n--- Auditando Claves i18n Sin Uso ---")
    if not os.path.exists(EN_PATH):
        print(f"[X] Error: Archivo no encontrado: {EN_PATH}")
        return [], {}

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    all_keys = get_flattened_keys(en_data)
    full_code = load_codebase_content()

    dynamic_patterns = re.findall(
        r'i18n\.(?:get|t)\(\s*f["\']([^"\'\)]+)["\']', full_code
    )
    dynamic_patterns += re.findall(
        r'\.get\(\s*f["\']([^"\'\)]+)["\']', full_code
    )

    truly_unused = []
    dynamically_used = []
    exact_found = []

    for key, val in sorted(all_keys.items()):
        if key in full_code:
            exact_found.append(key)
        else:
            is_dyn = False
            for pat in set(dynamic_patterns):
                regex_pat = (
                    "^" + re.sub(r"\{[^\}]+\}", r"[a-zA-Z0-9_]+", pat) + "$"
                )
                if re.match(regex_pat, key):
                    is_dyn = True
                    break
            if is_dyn:
                dynamically_used.append(key)
            else:
                truly_unused.append(key)

    print(f"Total claves en {os.path.basename(EN_PATH)}: {len(all_keys)}")
    print(f"Claves encontradas exactamente: {len(exact_found)}")
    print(f"Claves usadas dinamicamente: {len(dynamically_used)}")
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
    print("\n--- Ordenando Archivos JSON Alfabeticamente ---")
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

        print(f"[OK] {os.path.basename(path)} ordenado alfabeticamente.")

def auto_clean_unused_and_sync():
    print("\n--- Limpieza Automatica y Sincronizacion ---")
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

    print("\n[OK] Limpieza y sincronizacion completada exitosamente.")

def audit_missing_keys_in_code():
    print("\n--- Auditando Claves Faltantes en JSON (Usadas en Código Python) ---")
    if not os.path.exists(EN_PATH) or not os.path.exists(ES_PATH):
        print("[X] Error: Archivos de traducción no encontrados.")
        return

    with open(ES_PATH, "r", encoding="utf-8") as f:
        es_data = json.load(f)

    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    es_flat = get_flattened_keys(es_data)
    en_flat = get_flattened_keys(en_data)

    target_paths = [
        os.path.join(BASE_DIR, "frontend"),
        os.path.join(BASE_DIR, "backend"),
        os.path.join(BASE_DIR, "main.py"),
    ]

    pattern = re.compile(r'i18n\.(?:get|t)\(\s*["\']([^"\'\)]+)["\']')
    missing_in_es = []
    missing_in_en = []

    for tp in target_paths:
        file_list = []
        if os.path.isfile(tp):
            file_list.append(tp)
        elif os.path.isdir(tp):
            for root, _, files in os.walk(tp):
                if any(x in root for x in ["__pycache__", ".venv", "venv"]):
                    continue
                for file in files:
                    if file.endswith(".py"):
                        file_list.append(os.path.join(root, file))

        for filepath in file_list:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for m in pattern.finditer(content):
                        key = m.group(1)
                        rel_path = os.path.relpath(filepath, BASE_DIR)
                        if key not in es_flat:
                            missing_in_es.append((key, rel_path))
                        if key not in en_flat:
                            missing_in_en.append((key, rel_path))
            except Exception:
                pass

    missing_in_es = sorted(list(set(missing_in_es)))
    missing_in_en = sorted(list(set(missing_in_en)))

    print(f"Claves faltantes en es.json: {len(missing_in_es)}")
    print(f"Claves faltantes en en.json: {len(missing_in_en)}")

    if missing_in_es:
        print("\n[!] Claves faltantes en es.json:")
        for k, p in missing_in_es:
            print(f"  - {k} (en {p})")

    if missing_in_en:
        print("\n[!] Claves faltantes en en.json:")
        for k, p in missing_in_en:
            print(f"  - {k} (en {p})")

    if not missing_in_es and not missing_in_en:
        print("\n[OK] ¡Excelente! Todas las claves i18n usadas en el código existen en ambos archivos JSON.")

def main_menu():
    while True:
        print("\n" + "=" * 50)
        print("     MINI-KICK i18N TOOLKIT & MANAGER")
        print("=" * 50)
        print("1. Auditar claves sin uso en JSON")
        print("2. Auditar claves faltantes en JSON (usadas en codigo Python)")
        print("3. Verificar paridad entre idiomas (en.json vs es.json)")
        print("4. Ordenar alfabeticamente (en.json y es.json)")
        print("5. Limpiar claves sin uso y sincronizar archivos")
        print("6. Salir")
        print("=" * 50)

        try:
            choice = input("Selecciona una opcion (1-6): ").strip()
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
            print("\n ¡Hasta luego!")
            break
        else:
            print("[X] Opcion invalida. Intenta nuevamente.")

if __name__ == "__main__":
    main_menu()

