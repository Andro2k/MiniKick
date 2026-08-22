# tests\run_tests.py

import os
import sys
import subprocess
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_unit_tests(extra_args=None):
    print("\n🚀 [MiniKick] Ejecutando suite de pruebas unitarias automatizadas con pytest...")
    cmd = [sys.executable, "-m", "pytest", "tests/unit"]
    if extra_args:
        cmd.extend(extra_args)
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return res.returncode

def run_i18n_test():
    print("\n🌐 [MiniKick] Ejecutando verificación de integridad i18n...")
    cmd = [sys.executable, "-m", "pytest", "tests/unit/test_i18n_integrity.py", "-v"]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return res.returncode

def run_live_kick(extra_args=None):
    print("\n🟢 [MiniKick] Iniciando Inspector en Vivo de Kick WebSocket...")
    cmd = [sys.executable, os.path.join(PROJECT_ROOT, "tests", "live", "kick_websocket_live.py")]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, cwd=PROJECT_ROOT).returncode

def run_live_twitch(extra_args=None):
    print("\n🟣 [MiniKick] Iniciando Inspector en Vivo de Twitch WebSocket...")
    cmd = [sys.executable, os.path.join(PROJECT_ROOT, "tests", "live", "twitch_websocket_live.py")]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, cwd=PROJECT_ROOT).returncode

def run_live_benchmark(extra_args=None):
    print("\n📊 [MiniKick] Iniciando Benchmark de Rendimiento en Vivo (Kick vs Twitch)...")
    cmd = [sys.executable, os.path.join(PROJECT_ROOT, "tests", "live", "chat_benchmark_live.py")]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, cwd=PROJECT_ROOT).returncode

def run_tts_benchmark(extra_args=None):
    print("\n🎙️ [MiniKick] Iniciando Benchmark de Voces Locales (Piper vs Kokoro vs pyttsx3)...")
    cmd = [sys.executable, os.path.join(PROJECT_ROOT, "tests", "live", "tts_benchmark_local.py")]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, cwd=PROJECT_ROOT).returncode

def run_i18n_toolkit():
    print("\n🛠️ [MiniKick] Abriendo i18n Manager Toolkit...")
    cmd = [sys.executable, os.path.join(PROJECT_ROOT, "tests", "tools", "i18n_manager.py")]
    return subprocess.run(cmd, cwd=PROJECT_ROOT).returncode

def interactive_menu():
    while True:
        print("\n" + "=" * 65)
        print("           MINIKICK UNIFIED TEST SUITE & RUNNER")
        print("=" * 65)
        print("  1. Ejecutar Pruebas Unitarias Automatizadas (pytest unit)")
        print("  2. Ejecutar Auditoría e Integridad i18n (en.json vs es.json)")
        print("  3. Ejecutar Inspector en Vivo de Kick WebSocket")
        print("  4. Ejecutar Inspector en Vivo de Twitch WebSocket")
        print("  5. Ejecutar Benchmark Multi-Plataforma en Vivo (Kick vs Twitch)")
        print("  6. Ejecutar Benchmark de Voces Locales (Piper vs Kokoro vs pyttsx3)")
        print("  7. Abrir Toolkit Interactivo de i18n (i18n Manager)")
        print("  8. Salir")
        print("=" * 65)

        try:
            choice = input("Selecciona una opción (1-8): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[!] Saliendo...")
            break

        if choice == "1":
            run_unit_tests()
        elif choice == "2":
            run_i18n_test()
        elif choice == "3":
            slug = input("Ingresa slug del canal de Kick [xqc]: ").strip() or "xqc"
            run_live_kick(["--slug", slug])
        elif choice == "4":
            channel = input("Ingresa canal de Twitch [xqc]: ").strip() or "xqc"
            run_live_twitch(["--channel", channel])
        elif choice == "5":
            dur = input("Duración en segundos (0 para indefinido) [15]: ").strip() or "15"
            run_live_benchmark(["--duration", dur])
        elif choice == "6":
            run_tts_benchmark()
        elif choice == "7":
            run_i18n_toolkit()
        elif choice == "8":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("[X] Opción inválida. Intenta nuevamente.")

def main():
    parser = argparse.ArgumentParser(description="MiniKick Unified Test Suite & Runner")
    parser.add_argument("--unit", "-u", action="store_true", help="Ejecutar todas las pruebas unitarias con pytest")
    parser.add_argument("--i18n", action="store_true", help="Ejecutar verificación de integridad i18n")
    parser.add_argument("--live-kick", action="store_true", help="Ejecutar inspector de Kick WebSocket en vivo")
    parser.add_argument("--live-twitch", action="store_true", help="Ejecutar inspector de Twitch WebSocket en vivo")
    parser.add_argument("--benchmark", action="store_true", help="Ejecutar benchmark multi-plataforma en vivo")
    parser.add_argument("--tts-benchmark", action="store_true", help="Ejecutar benchmark de voces locales TTS")
    parser.add_argument("--tool-i18n", action="store_true", help="Abrir toolkit interactivo de i18n")

    args, unknown = parser.parse_known_args()

    if args.unit:
        sys.exit(run_unit_tests(unknown))
    elif args.i18n:
        sys.exit(run_i18n_test())
    elif args.live_kick:
        sys.exit(run_live_kick(unknown))
    elif args.live_twitch:
        sys.exit(run_live_twitch(unknown))
    elif args.benchmark:
        sys.exit(run_live_benchmark(unknown))
    elif args.tts_benchmark:
        sys.exit(run_tts_benchmark(unknown))
    elif args.tool_i18n:
        sys.exit(run_i18n_toolkit())
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
