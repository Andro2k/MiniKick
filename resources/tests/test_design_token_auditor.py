# resources\tests\test_design_token_auditor.py
"""Pruebas de la regla de breakpoints sueltos del auditor de tokens de diseño."""

from pathlib import Path

import pytest

from resources.tools import frontend_design_token_auditor as auditor


def _breakpoints(root: Path, source: str):
    (root / "frontend").mkdir(exist_ok=True)
    (root / "frontend" / "sample_view.py").write_text(source, encoding="utf-8")
    return [v for v in auditor.audit_design_tokens(str(root / "frontend")) if v.violation_type == "HARDCODED_BREAKPOINT"]


def test_repo_no_tiene_breakpoints_sueltos():
    found = [v for v in auditor.audit_design_tokens() if v.violation_type == "HARDCODED_BREAKPOINT"]

    assert found == []


@pytest.mark.parametrize(
    "source, literal",
    [
        ("def f(width):\n    return width < 650\n", "650"),
        ("def f(self):\n    return self.width() >= 950\n", "950"),
        ("def f(w):\n    return 480 > w\n", "480"),
        ("def f(event):\n    return event.size().width() <= 1100\n", "1100"),
    ],
)
def test_detecta_comparaciones_de_ancho_contra_un_entero(tmp_path, monkeypatch, source, literal):
    monkeypatch.setattr(auditor, "PROJECT_ROOT", str(tmp_path))

    found = _breakpoints(tmp_path, source)

    assert [v.detected_value for v in found] == [literal]
    assert "Room" in found[0].suggested_token


@pytest.mark.parametrize(
    "source",
    [
        "def f(room):\n    return room.below(Room.WIDE)\n",
        "def f(width):\n    return width < MARGIN\n",
        "def f(width):\n    return width < 100\n",
        "def f(items):\n    return len(items) > 500\n",
        "def f(count):\n    return count < 1000\n",
    ],
)
def test_ignora_lo_que_no_es_un_breakpoint(tmp_path, monkeypatch, source):
    monkeypatch.setattr(auditor, "PROJECT_ROOT", str(tmp_path))

    assert _breakpoints(tmp_path, source) == []
