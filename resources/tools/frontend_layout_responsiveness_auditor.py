# resources/tools/frontend_layout_responsiveness_auditor.py

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")


def _resolve_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "frontend").exists() and (parent / "backend").exists():
            return parent
    return Path(__file__).resolve().parents[3]


PROJECT_ROOT = _resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QSize
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from backend.services.system.translation_service import TranslationService
from frontend.common import get_global_qss

DEFAULT_WIDTHS = [1400, 1200, 1000, 850, 750, 700, 680, 600, 550]

VIEW_REGISTRY: Dict[str, Tuple[str, str, Dict[str, Any]]] = {
    "dashboard": ("frontend.views.dashboard_view", "DashboardView", {}),
    "chat": ("frontend.views.chat_view", "ChatView", {}),
    "alerts": ("frontend.views.alerts_view", "AlertsView", {"alerts_overlay_url": "http://localhost:8090/alerts?token=audit"}),
    "widgets": ("frontend.views.widgets_view", "WidgetsView", {}),
    "settings": ("frontend.views.settings_view", "SettingsView", {}),
    "schedule": ("frontend.views.schedule_view", "ScheduleView", {}),
    "commands": ("frontend.views.commands_view", "CommandView", {}),
    "timers": ("frontend.views.timers_view", "TimersView", {}),
    "music": ("frontend.views.music_view", "MusicView", {}),
    "rewards": ("frontend.views.rewards_view", "RewardsView", {}),
    "logs": ("frontend.views.logs_view", "LogView", {}),
}


class ViewFixtureFactory:
    @staticmethod
    def create_view(key: str, i18n: TranslationService) -> Optional[QWidget]:
        if key not in VIEW_REGISTRY:
            return None
        mod_path, cls_name, extra_kwargs = VIEW_REGISTRY[key]
        try:
            mod = __import__(mod_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            kwargs = {"i18n": i18n, **extra_kwargs}
            try:
                return cls(**kwargs)
            except TypeError:
                return cls(i18n, MagicMock(), **extra_kwargs)
        except Exception as e:
            print(f"⚠️ Error instanciando vista '{key}' ({cls_name}): {e}", file=sys.stderr)
            return None


def inspect_view_responsiveness(
    view_key: str,
    view: QWidget,
    widths: Optional[List[int]] = None,
) -> Tuple[bool, List[Dict[str, Any]]]:
    widths = widths or DEFAULT_WIDTHS
    app = QApplication.instance()
    win = QMainWindow()
    win.setCentralWidget(view)
    win.show()

    all_passed = True
    results: List[Dict[str, Any]] = []

    for w in widths:
        win.resize(w, 800)
        view.resize(w, 800)
        event = QResizeEvent(QSize(w, 800), QSize(w, 800))
        view.resizeEvent(event)
        if view.layout():
            view.layout().activate()

        for _ in range(3):
            app.processEvents()

        vp_w = view.scroll_area.viewport().width() if hasattr(view, "scroll_area") else w
        sc_w = view.scroll_content.width() if hasattr(view, "scroll_content") else w
        min_w = view.scroll_content.minimumSizeHint().width() if hasattr(view, "scroll_content") else view.minimumSizeHint().width()

        clipped = sc_w > vp_w or (not hasattr(view, "scroll_area") and min_w > w)
        if clipped:
            all_passed = False

        results.append({
            "width": w, "viewport_w": vp_w, "content_w": sc_w,
            "min_hint_w": min_w, "clipped": clipped, "status": "FAIL" if clipped else "PASS"
        })

    win.close()
    return all_passed, results


def print_matrix_summary(all_results: Dict[str, Tuple[bool, List[Dict[str, Any]]]], widths: List[int]):
    print("\n" + "=" * 90)
    print(" 📊 MATRIZ RESUMEN DE RESPONSIVIDAD FLEX (TODAS LAS VISTAS)")
    print("=" * 90)
    header = f"{'Vista':<16} | " + " | ".join(f"{w}px" for w in widths) + " | Status"
    print(header)
    print("-" * 90)

    for key, (passed, results) in all_results.items():
        row_statuses = [" ✅ " if not r["clipped"] else " ❌ " for r in results]
        view_label = f"{key.capitalize():<16}"
        overall = "PASS" if passed else "FAIL"
        print(f"{view_label} | " + " | ".join(row_statuses) + f" | {overall}")

    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Audita flexibilidad, clipping y dimensiones de las vistas del frontend.")
    parser.add_argument("--view", "-v", default="all", choices=["all"] + list(VIEW_REGISTRY.keys()))
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setStyleSheet(get_global_qss())

    i18n = TranslationService(default_lang="es")
    widths = DEFAULT_WIDTHS
    target_keys = list(VIEW_REGISTRY.keys()) if args.view == "all" else [args.view]
    all_results: Dict[str, Tuple[bool, List[Dict[str, Any]]]] = {}
    overall_ok = True

    for key in target_keys:
        view = ViewFixtureFactory.create_view(key, i18n)
        if view is None:
            all_results[key] = (False, [])
            overall_ok = False
            continue

        passed, res = inspect_view_responsiveness(key, view, widths)
        all_results[key] = (passed, res)
        if not passed:
            overall_ok = False

    if args.json:
        print(json.dumps({"overall_status": "PASS" if overall_ok else "FAIL", "views": {k: {"passed": v[0], "steps": v[1]} for k, v in all_results.items()}}, indent=2))
    else:
        print_matrix_summary(all_results, widths)

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
