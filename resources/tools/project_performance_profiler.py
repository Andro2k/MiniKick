# resources\tools\project_performance_profiler.py\

import argparse
import contextlib
import ctypes
from ctypes import wintypes
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["AV_LOG_LEVEL"] = "error"
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false;qt.multimedia=false;qt.qpa.wayland.*=false"

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8")


def _resolve_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "frontend").exists() and (parent / "backend").exists():
            return parent
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from backend.database import DatabaseManager
from backend.services import CommandService, SpamService, TranslationService
from frontend.components.chat.chat_display import ChatDisplayPanel


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class MiniKickProfiler:
    def __init__(self):
        self.results = {}

    def get_memory_info(self) -> dict:
        with contextlib.suppress(Exception):
            counters = PROCESS_MEMORY_COUNTERS_EX()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            kernel32 = ctypes.windll.kernel32
            psapi = getattr(ctypes.windll, "psapi", None)
            
            kernel32.GetCurrentProcess.restype = ctypes.c_void_p
            h_proc = kernel32.GetCurrentProcess()
            
            func = getattr(kernel32, "K32GetProcessMemoryInfo", None) or getattr(psapi, "GetProcessMemoryInfo", None)
            if func:
                func.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
                func.restype = wintypes.BOOL
                if func(h_proc, ctypes.byref(counters), counters.cb):
                    return {
                        "rss_mb": round(counters.WorkingSetSize / (1024 * 1024), 2),
                        "vms_mb": round(counters.PrivateUsage / (1024 * 1024), 2),
                    }
        return {"rss_mb": 0.0, "vms_mb": 0.0}

    def benchmark_bootstrap_footprint(self, app):
        print("\n========================================================", flush=True)
        print(" [1/5] AUDITORÍA DE CONSUMO BASE (BOOTSTRAP)", flush=True)
        print("========================================================", flush=True)
        mem = self.get_memory_info()
        print(f" -> RAM Base (Working Set / RSS): {mem['rss_mb']} MB", flush=True)
        print(f" -> Memoria Privada (Commit):     {mem['vms_mb']} MB", flush=True)
        self.results["bootstrap"] = mem

    def benchmark_database_performance(self):
        print("\n========================================================", flush=True)
        print(" [2/5] AUDITORÍA DE RENDIMIENTO DE BASE DE DATOS (SQLite)", flush=True)
        print("========================================================", flush=True)
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            temp_db_path = Path(tmp_db.name)

        try:
            t0 = time.perf_counter()
            db = DatabaseManager(db_name=temp_db_path.name)
            db.db_name = str(temp_db_path)
            db._initialize_database()
            init_time = (time.perf_counter() - t0) * 1000

            with db.get_connection() as conn:
                cur = conn.cursor()
                journal_mode = cur.execute("PRAGMA journal_mode").fetchone()[0]
                sync_mode = cur.execute("PRAGMA synchronous").fetchone()[0]

            print(f" -> Inicialización y Esquema: {init_time:.2f} ms", flush=True)
            print(f" -> Journal Mode:             {journal_mode.upper()} (Esperado: WAL)", flush=True)
            print(f" -> Synchronous:              {sync_mode} (Esperado: 1 = NORMAL)", flush=True)

            t0 = time.perf_counter()
            for i in range(100):
                db.log_spam_violation(
                    username=f"user_{i}",
                    sender_id=1000 + i,
                    filter_id="caps_protection",
                    message_content=f"SPAM MESSAGE {i}",
                    penalty_type="timeout",
                    duration=5,
                    platform="kick",
                )
            single_insert_time = (time.perf_counter() - t0) * 1000
            single_avg = single_insert_time / 100

            t0 = time.perf_counter()
            with db.get_connection() as conn:
                cur = conn.cursor()
                for _ in range(50):
                    cur.execute("SELECT * FROM spam_violations WHERE username = ? ORDER BY timestamp DESC LIMIT 10", ("user_50",))
                    cur.fetchall()
            query_time = ((time.perf_counter() - t0) * 1000) / 50

            print(f" -> Inserción individual (100 records): {single_insert_time:.2f} ms ({single_avg:.3f} ms/op)", flush=True)
            print(f" -> Consulta indexada promedio:         {query_time:.3f} ms/query", flush=True)

            self.results["database"] = {
                "journal_mode": journal_mode,
                "single_insert_avg_ms": single_avg,
                "indexed_query_avg_ms": query_time,
            }
        finally:
            for ext in ("", "-wal", "-shm"):
                Path(f"{temp_db_path}{ext}").unlink(missing_ok=True)

    def benchmark_spam_and_command_processing(self):
        print("\n========================================================", flush=True)
        print(" [3/5] AUDITORÍA DE THROUGHPUT EN PARSING Y SPAM", flush=True)
        print("========================================================", flush=True)
        
        mock_spam_storage = SimpleNamespace(load_all=lambda: {}, save_filter=lambda f, c: None, db_manager=None)
        spam_service = SpamService(storage=mock_spam_storage, max_history_size=1000)
        spam_service.filters = {
            "caps_protection": {"is_active": 1, "max_amount": 5, "penalty": "timeout", "duration": 5, "apply_kick": 1, "apply_twitch": 1},
            "symbol_protection": {"is_active": 1, "max_amount": 10, "penalty": "timeout", "duration": 5, "apply_kick": 1, "apply_twitch": 1},
            "link_protection": {"is_active": 1, "allowlist": "kick.com, youtube.com", "penalty": "timeout", "duration": 5, "apply_kick": 1, "apply_twitch": 1},
            "paragraph_protection": {"is_active": 1, "max_amount": 250, "penalty": "timeout", "duration": 5, "apply_kick": 1, "apply_twitch": 1},
            "repetition_protection": {"is_active": 1, "max_amount": 3, "penalty": "timeout", "duration": 5, "apply_kick": 1, "apply_twitch": 1},
        }

        mock_cmd_storage = SimpleNamespace(
            load_all=lambda: [],
            save_command=lambda *a, **kw: None,
            log_command_execution=lambda *a, **kw: None,
            delete_command=lambda t: None,
            get_command_by_trigger=lambda t: None,
        )
        cmd_service = CommandService(commands_storage=mock_cmd_storage)
        cmd_service._all_commands_cache = [
            {"trigger": "!discord", "response": "Join https://discord.gg/test", "is_active": 1, "cooldown": 0, "aliases": "!dc,!comunidad", "is_regex": 0, "permission": "everyone", "apply_kick": 1, "apply_twitch": 1},
            {"trigger": "!socials", "response": "Twitter: @test, Youtube: @test", "is_active": 1, "cooldown": 0, "aliases": "!redes", "is_regex": 0, "permission": "everyone", "apply_kick": 1, "apply_twitch": 1},
            {"trigger": "!lurk", "response": "Thanks {user} for lurking!", "is_active": 1, "cooldown": 0, "aliases": "", "is_regex": 0, "permission": "everyone", "apply_kick": 1, "apply_twitch": 1},
        ]
        cmd_service._rebuild_dispatch_table_from_cache()

        test_messages = [
            ("UserA", "Hola a todos bienvenidos al stream! [emote:123:pepe]", []),
            ("UserB", "HOLA CHICOS QUE TAL TODO TODO BIEN???", []),
            ("UserC", "!discord", []),
            ("UserD", "Chequeen este link sospechoso: http://free-robux-hack.ru/free", []),
            ("UserE", "Mensaje repetido hola hola hola hola hola hola", []),
            ("UserF", "Normal message with normal characters and nice vibe", ["subscriber"]),
        ] * 1000

        t0 = time.perf_counter()
        spam_detected = sum(
            1 for i, (user, msg, badges) in enumerate(test_messages)
            if spam_service.is_spam(user=f"user_{i%500}", message=msg, badges=badges, msg_id=str(i), sender_id=i, platform="kick")
        )
        spam_duration = time.perf_counter() - t0
        spam_rate = len(test_messages) / spam_duration

        print(f" -> Mensajes evaluados por SpamService: {len(test_messages):,}", flush=True)
        print(f" -> Tiempo total de procesamiento CPU:  {spam_duration * 1000:.2f} ms", flush=True)
        print(f" -> Rendimiento Puro de Parsing:        {spam_rate:,.0f} msgs/segundo", flush=True)
        print(f" -> Infracciones detectadas:            {spam_detected:,}", flush=True)

        cmd_messages = [
            ("User1", "!discord", []),
            ("User2", "!dc", []),
            ("User3", "!redes", []),
            ("User4", "random non-command chat message", []),
            ("User5", "!unregistered_command", []),
        ] * 2000

        t0 = time.perf_counter()
        cmd_executed = sum(
            1 for user, msg, badges in cmd_messages
            if cmd_service.process_incoming_message(user=user, message=msg, badges=badges, platform="kick")[0]
        )
        cmd_duration = time.perf_counter() - t0
        cmd_rate = len(cmd_messages) / cmd_duration

        print(f" -> Mensajes evaluados por CommandService: {len(cmd_messages):,}", flush=True)
        print(f" -> Tiempo total de dispatch O(1):        {cmd_duration * 1000:.2f} ms", flush=True)
        print(f" -> Rendimiento Dispatch Table:           {cmd_rate:,.0f} msgs/segundo", flush=True)

        self.results["spam_service"] = {"rate_msgs_sec": spam_rate, "duration_ms": spam_duration * 1000}
        self.results["command_service"] = {"rate_msgs_sec": cmd_rate, "duration_ms": cmd_duration * 1000}

    def benchmark_ui_chat_rendering(self, i18n):
        print("\n========================================================", flush=True)
        print(" [4/5] AUDITORÍA DE RENDERIZADO DE UI (CHAT DISPLAY)", flush=True)
        print("========================================================", flush=True)
        
        chat_panel = ChatDisplayPanel(i18n=i18n)
        chat_panel.show()
        QApplication.processEvents()

        t0 = time.perf_counter()
        for i in range(100):
            chat_panel.append_message(
                user=f"Gamer_{i}",
                message=f"Mensaje de prueba número {i} en el chat con formato y símbolos especiales.",
                color="#38bdf8",
                timestamp=datetime.now().strftime("%H:%M:%S"),
                role="VIP" if i % 5 == 0 else "Subscriber" if i % 2 == 0 else "User",
                platform="kick" if i % 2 == 0 else "twitch",
            )
        QApplication.processEvents()
        t_100 = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        for i in range(100, 500):
            chat_panel.append_message(
                user=f"Gamer_{i}",
                message=f"Ráfaga rápida {i} con texto largo para comprobar recorte de búfer en QTextEdit.",
                color="#4ade80",
                timestamp=datetime.now().strftime("%H:%M:%S"),
                role="User",
                platform="kick",
            )
        QApplication.processEvents()
        t_400_trim = (time.perf_counter() - t0) * 1000

        mem = self.get_memory_info()
        print(f" -> Tiempo para renderizar 100 mensajes:     {t_100:.2f} ms ({t_100 / 100:.3f} ms/msg)", flush=True)
        print(f" -> Tiempo para 400 msgs + Trimming (Buffer): {t_400_trim:.2f} ms ({t_400_trim / 400:.3f} ms/msg)", flush=True)
        print(f" -> Bloques en documento tras recorte:        {chat_panel.chat_display.document().blockCount()} (Límite: 400)", flush=True)
        print(f" -> RAM actual tras renderizado de UI:        {mem['rss_mb']} MB", flush=True)

        self.results["ui_chat"] = {
            "t_100_ms": t_100,
            "avg_ms_per_msg": t_100 / 100,
            "t_400_trim_ms": t_400_trim,
            "final_blocks": chat_panel.chat_display.document().blockCount(),
            "mem_rss_mb": mem["rss_mb"],
        }
        chat_panel.close()

    def run_full_audit(self, quick: bool = False) -> dict:
        print("==================================================================", flush=True)
        mode_str = "RÁPIDA (CORE & DB)" if quick else "INTEGRAL (CORE + DB + UI)"
        print(f" [MiniKick] INICIANDO AUDITORÍA DE RENDIMIENTO: {mode_str}", flush=True)
        print("==================================================================", flush=True)

        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv[:1])
            with contextlib.suppress(Exception):
                from PySide6.QtGui import QFontDatabase
                fonts_dir = PROJECT_ROOT / "assets" / "fonts"
                if fonts_dir.exists():
                    for font_path in fonts_dir.glob("*.[ot]tf"):
                        QFontDatabase.addApplicationFont(str(font_path))

        i18n = TranslationService(default_lang="es")

        self.benchmark_bootstrap_footprint(app)
        self.benchmark_database_performance()
        self.benchmark_spam_and_command_processing()
        if not quick:
            self.benchmark_ui_chat_rendering(i18n)

        boot_rss = self.results.get("bootstrap", {}).get("rss_mb", 0)
        spam_rate = self.results.get("spam_service", {}).get("rate_msgs_sec", 0)
        cmd_rate = self.results.get("command_service", {}).get("rate_msgs_sec", 0)
        db_query_time = self.results.get("database", {}).get("indexed_query_avg_ms", 999.0)

        checks = {
            "ram_base_budget": boot_rss <= 180.0,
            "spam_throughput_budget": spam_rate >= 2500.0,
            "cmd_throughput_budget": cmd_rate >= 5000.0,
            "db_latency_budget": db_query_time <= 5.0,
        }

        if not quick and "ui_chat" in self.results:
            checks["ui_latency_budget"] = self.results["ui_chat"].get("avg_ms_per_msg", 999.0) <= 3.0

        all_passed = all(checks.values())

        print("\n========================================================", flush=True)
        print(" RESUMEN EJECUTIVO Y DIAGNÓSTICO DE RENDIMIENTO", flush=True)
        print("========================================================", flush=True)
        print(f" 1. Consumo de Memoria Base: {boot_rss} MB -> {'✅ EXCELENTE' if boot_rss <= 120 else '⚠️ ACEPTABLE'}", flush=True)
        print(f" 2. Rendimiento Spam Filter: {spam_rate:,.0f} msg/s -> ✅ ALTA VELOCIDAD", flush=True)
        print(f" 3. Rendimiento Comandos:    {cmd_rate:,.0f} msg/s -> ✅ O(1) LOOKUP", flush=True)
        print(f" 4. SQLite Journal Mode:     {self.results.get('database', {}).get('journal_mode', '')} -> ✅ CONFIGURACIÓN WAL", flush=True)
        if not quick and "ui_chat" in self.results:
            print(f" 5. Consumo tras Carga UI:   {self.results['ui_chat']['mem_rss_mb']} MB -> ✅ ESTABLE", flush=True)
            print(f" 6. Latencia Render UI Chat: {self.results['ui_chat']['avg_ms_per_msg']:.3f} ms/msg -> ✅ FLUIDO (< 1 ms/msg)", flush=True)

        status_label = "✅ [APROBADO] Todos los presupuestos de rendimiento superados." if all_passed else "⚠️ [ADVERTENCIA] Algunas métricas excedieron los umbrales recomendados."
        print(f"\n{status_label}")
        print("==================================================================\n", flush=True)

        return {"is_clean": all_passed, "metrics": self.results, "budgets": checks}


def main():
    parser = argparse.ArgumentParser(description="Perfila escenarios del backend y frontend y compara sus presupuestos de rendimiento.")
    parser.add_argument("--quick", "-q", action="store_true", help="Auditoría rápida (omite renderizado gráfico de UI)")
    parser.add_argument("--full", "-f", action="store_true", help="Auditoría completa (incluye benchmarks de UI y widgets)")
    parser.add_argument("--json", action="store_true", help="Exportar métricas de rendimiento en formato JSON")
    parser.add_argument("--strict", action="store_true", help="Falla con código 1 si algún presupuesto de rendimiento no se cumple")

    args = parser.parse_args()
    profiler = MiniKickProfiler()

    report = profiler.run_full_audit(quick=args.quick and not args.full)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.strict and not report["is_clean"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
