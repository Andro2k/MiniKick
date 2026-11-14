# resources\tests\test_file_naming_auditor.py
"""Pruebas de las reglas de nomenclatura <tema>_<rol>.py del auditor de ubicación."""

from pathlib import Path

from resources.tools import project_file_placement_auditor as auditor


def _touch(root: Path, rel: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def test_repo_cumple_la_convencion_de_nombres():
    assert auditor.audit_naming_convention() == []


def test_detecta_archivos_sin_sufijo_de_rol(tmp_path, monkeypatch):
    monkeypatch.setattr(auditor, "PROJECT_ROOT", str(tmp_path))
    for rel in (
        "backend/interfaces/i_tts.py",
        "backend/services/app/clock.py",
        "backend/utils/perf.py",
        "frontend/window/startup.py",
        "frontend/components/chat/bot_mute.py",
    ):
        _touch(tmp_path, rel)

    flagged = {Path(v.file_path).name for v in auditor.audit_naming_convention()}

    assert flagged == {"i_tts.py", "clock.py", "perf.py", "startup.py", "bot_mute.py"}


def test_acepta_nombres_validos_excepciones_y_subcarpetas(tmp_path, monkeypatch):
    monkeypatch.setattr(auditor, "PROJECT_ROOT", str(tmp_path))
    for rel in (
        "backend/interfaces/tts_interface.py",
        "backend/interfaces/__init__.py",
        "backend/services/app/clock_service.py",
        "backend/services/chat/chat_pipeline.py",
        "backend/services/webhooks/webhook_sender.py",
        "backend/utils/chat_command_config.py",
        "frontend/window/startup_coordinator.py",
        "frontend/window/view_prewarmer.py",
        "frontend/components/chat/bot_mute_panel.py",
        "frontend/dialogs/splash_screen.py",
    ):
        _touch(tmp_path, rel)

    assert auditor.audit_naming_convention() == []


def test_las_reglas_no_miran_subcarpetas_si_no_son_recursivas(tmp_path, monkeypatch):
    monkeypatch.setattr(auditor, "PROJECT_ROOT", str(tmp_path))
    _touch(tmp_path, "backend/utils/extra/sin_sufijo.py")

    assert auditor.audit_naming_convention() == []
