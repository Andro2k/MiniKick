# resources\tools\build_manager.py

import os
import re
import sys
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VERSION_PY_PATH = os.path.join(BASE_DIR, "backend", "config", "version.py")
VERSION_INFO_PATH = os.path.join(BASE_DIR, "version_info.txt")
PYPROJECT_PATH = os.path.join(BASE_DIR, "pyproject.toml")
INNO_SETUP_PATH = os.path.join(BASE_DIR, "instalador.iss")
SPEC_PATH = os.path.join(BASE_DIR, "MiniKick.spec")

def get_current_app_version() -> str:
    if not os.path.exists(VERSION_PY_PATH):
        raise FileNotFoundError(f"No se encontró el archivo {VERSION_PY_PATH}")
    
    with open(VERSION_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r'APP_VERSION\s*=\s*["\']v?([^"\']+)["\']', content)
    if not match:
        raise ValueError("No se pudo extraer APP_VERSION de backend/config/version.py")
    
    return match.group(1).strip()

def generate_version_info() -> str:
    version_clean = get_current_app_version()
    parts = [int(p) for p in re.findall(r"\d+", version_clean)]
    while len(parts) < 4:
        parts.append(0)
    
    v_tuple = tuple(parts[:4])
    v_str = f"{v_tuple[0]}.{v_tuple[1]}.{v_tuple[2]}.{v_tuple[3]}"
    v_short = f"{v_tuple[0]}.{v_tuple[1]}.{v_tuple[2]}"
    
    version_info_content = f"""# UTF-8
# Windows Version Info Resource file for PyInstaller

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({v_tuple[0]}, {v_tuple[1]}, {v_tuple[2]}, {v_tuple[3]}),
    prodvers=({v_tuple[0]}, {v_tuple[1]}, {v_tuple[2]}, {v_tuple[3]}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'Andro2k'),
            StringStruct('FileDescription', 'MiniKick - Centro de control modular para streamers en Kick.com'),
            StringStruct('FileVersion', '{v_str}'),
            StringStruct('InternalName', 'MiniKick'),
            StringStruct('LegalCopyright', 'Copyright (C) 2026 Andro2k'),
            StringStruct('OriginalFilename', 'MiniKick.exe'),
            StringStruct('ProductName', 'MiniKick'),
            StringStruct('ProductVersion', '{v_str}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    with open(VERSION_INFO_PATH, "w", encoding="utf-8") as f:
        f.write(version_info_content)
    print(f"[OK] version_info.txt generado con version {v_str}")

    if os.path.exists(PYPROJECT_PATH):
        with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
            pyproject_text = f.read()
        pyproject_text = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{v_short}"', pyproject_text, count=1)
        with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
            f.write(pyproject_text)
        print(f"[OK] pyproject.toml sincronizado a version {v_short}")

    if os.path.exists(INNO_SETUP_PATH):
        with open(INNO_SETUP_PATH, "r", encoding="utf-8") as f:
            inno_text = f.read()
        inno_text = re.sub(r'#define MyAppVersion\s+"[^"]+"', f'#define MyAppVersion "{v_short}"', inno_text, count=1)
        with open(INNO_SETUP_PATH, "w", encoding="utf-8") as f:
            f.write(inno_text)
        print(f"[OK] instalador.iss sincronizado a MyAppVersion {v_short}")

    return v_str

def run_cmd(cmd_list: list[str], desc: str) -> bool:
    print(f"\n>>> {desc}...")
    print(f"Ejecutando: {' '.join(cmd_list)}")
    res = subprocess.run(cmd_list, cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"[ERROR] Falló: {desc} (Código de salida: {res.returncode})")
        return False
    print(f"[OK] Completado: {desc}")
    return True

def install_venv():
    print("\n--- Instalación y Sincronización del Entorno Virtual (.venv) ---")
    if not os.path.exists(os.path.join(BASE_DIR, ".venv")):
        if not run_cmd(["uv", "venv"], "Creando entorno virtual .venv"):
            return False
    return run_cmd(["uv", "sync"], "Sincronizando dependencias en el entorno virtual")

def upgrade_dependencies():
    print("\n--- Actualización de Dependencias ---")
    if not run_cmd(["uv", "lock", "--upgrade"], "Actualizando lockfile (uv lock --upgrade)"):
        return False
    return run_cmd(["uv", "sync"], "Instalando paquetes actualizados (uv sync)")

def build_executable():
    print("\n--- Compilación de Ejecutable con PyInstaller ---")
    generate_version_info()
    return run_cmd(["uv", "run", "python", "-m", "PyInstaller", "--clean", "--noconfirm", "MiniKick.spec"], "Compilando MiniKick con PyInstaller")

def full_pipeline():
    print("\n=======================================================")
    print("      PIPELINE COMPLETO DE ACTUALIZACIÓN Y COMPILACIÓN")
    print("=======================================================")
    if not upgrade_dependencies():
        return
    if not build_executable():
        return
    print("\n[ÉXITO] ¡Pipeline completado con éxito! Ejecutable listo en dist/MiniKick/MiniKick.exe")

def check_build_prerequisites() -> dict:
    try:
        ver = get_current_app_version()
        ver_ok = True
    except Exception as ex:
        ver = str(ex)
        ver_ok = False

    spec_exists = os.path.exists(SPEC_PATH)
    vinfo_exists = os.path.exists(VERSION_INFO_PATH)
    inno_exists = os.path.exists(INNO_SETUP_PATH)
    pyproject_exists = os.path.exists(PYPROJECT_PATH)
    venv_exists = os.path.exists(os.path.join(BASE_DIR, ".venv"))
    assets_dir = os.path.join(BASE_DIR, "assets")
    icon_ico = os.path.join(assets_dir, "icons", "icon.ico")
    assets_ok = os.path.isdir(assets_dir) and os.path.exists(icon_ico)

    dist_exe = os.path.join(BASE_DIR, "dist", "MiniKick", "MiniKick.exe")
    dist_exists = os.path.exists(dist_exe)
    dist_size_mb = round(os.path.getsize(dist_exe) / (1024 * 1024), 2) if dist_exists else 0.0

    all_ready = ver_ok and spec_exists and venv_exists and assets_ok

    report = {
        "app_version": ver,
        "is_ready_to_build": all_ready,
        "checks": {
            "version_py": ver_ok,
            "minikick_spec": spec_exists,
            "version_info_txt": vinfo_exists,
            "inno_setup_iss": inno_exists,
            "pyproject_toml": pyproject_exists,
            "venv_installed": venv_exists,
            "assets_and_icon": assets_ok,
        },
        "dist_binary": {
            "exists": dist_exists,
            "path": os.path.relpath(dist_exe, BASE_DIR) if dist_exists else None,
            "size_mb": dist_size_mb
        }
    }
    return report

def print_check_report(report: dict):
    print("\n=======================================================")
    print("      MINIKICK - VERIFICACIÓN PRE-FLIGHT DE BUILD")
    print("=======================================================")
    print(f"🔹 Versión Actual : v{report['app_version']}")
    print("-------------------------------------------------------")
    for key, val in report["checks"].items():
        status = "✅ OK" if val else "❌ FALTANTE"
        print(f"  • {key.replace('_', ' ').title():<22}: {status}")
    print("-------------------------------------------------------")
    if report["dist_binary"]["exists"]:
        print(f"📦 Ejecutable en dist/: SÍ ({report['dist_binary']['size_mb']} MB)")
    else:
        print("📦 Ejecutable en dist/: NO generado aún")
    print("-------------------------------------------------------")
    if report["is_ready_to_build"]:
        print("🎉 [APROBADO] ¡El entorno está listo para compilar!")
    else:
        print("⚠️ [ADVERTENCIA] Faltan prerrequisitos antes de compilar.")
    print("=======================================================\n")

def show_menu():
    if not sys.stdin.isatty():
        print("[Modo No-Interactivo detectado] Ejecutando verificación de build...")
        rep = check_build_prerequisites()
        print_check_report(rep)
        return

    while True:
        try:
            ver = get_current_app_version()
        except Exception:
            ver = "Desconocida"

        print("\n=======================================================")
        print(f"       MINIKICK BUILD & DEPENDENCY MANAGER (v{ver})")
        print("=======================================================")
        print("1. Generar / Sincronizar version_info.txt (desde version.py)")
        print("2. Verificar prerrequisitos de compilación (Pre-Flight)")
        print("3. Instalar / Sincronizar entorno virtual (uv sync)")
        print("4. Actualizar todas las librerías (uv lock --upgrade + uv sync)")
        print("5. Compilar ejecutable (PyInstaller MiniKick.spec)")
        print("6. Pipeline completo (Actualizar + Versionar + Compilar)")
        print("7. Salir")
        print("=======================================================")
        try:
            choice = input("Selecciona una opción (1-7): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break

        if choice == "1":
            generate_version_info()
        elif choice == "2":
            rep = check_build_prerequisites()
            print_check_report(rep)
        elif choice == "3":
            install_venv()
        elif choice == "4":
            upgrade_dependencies()
        elif choice == "5":
            build_executable()
        elif choice == "6":
            full_pipeline()
        elif choice in ("7", "q", "exit"):
            print("Saliendo...")
            break
        else:
            print("Opción inválida. Intenta nuevamente.")

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="MiniKick Build, Dependency & Packaging Manager")
    parser.add_argument("--version-info", "-v", action="store_true", help="Generar y sincronizar version_info.txt")
    parser.add_argument("--check", "-c", action="store_true", help="Verificar prerrequisitos de compilación (Pre-Flight Check)")
    parser.add_argument("--install-venv", "-i", action="store_true", help="Instalar y sincronizar .venv con uv sync")
    parser.add_argument("--upgrade", "-u", action="store_true", help="Actualizar dependencias con uv lock --upgrade")
    parser.add_argument("--build", "-b", action="store_true", help="Compilar ejecutable con PyInstaller")
    parser.add_argument("--all", "-a", action="store_true", help="Ejecutar pipeline completo de build")
    parser.add_argument("--json", action="store_true", help="Exportar reporte de verificación en formato JSON")

    args = parser.parse_args()

    if args.json:
        rep = check_build_prerequisites()
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return

    if args.check:
        rep = check_build_prerequisites()
        print_check_report(rep)
        sys.exit(0 if rep["is_ready_to_build"] else 1)
    elif args.version_info:
        generate_version_info()
    elif args.install_venv:
        install_venv()
    elif args.upgrade:
        upgrade_dependencies()
    elif args.build:
        build_executable()
    elif args.all:
        full_pipeline()
    else:
        show_menu()

if __name__ == "__main__":
    main()
