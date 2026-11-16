# resources\tests\test_project_icon_grid_tool.py
"""Cuadrícula de iconos: medición del glifo, plan de ajuste, envoltorio idempotente y lienzo estándar."""

import pytest

from resources.tools import project_icon_grid_tool as grid


def _svg(rect: str, size: str = "24") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none"><rect {rect} fill="#000"/></svg>'
    )


CENTERED = _svg('x="4" y="4" width="16" height="16"')
OFF_CENTER = _svg('x="4" y="1" width="16" height="16"')
OVERSIZE = _svg('x="0" y="0" width="24" height="24"')


def test_measure_returns_real_glyph_bounds():
    bounds = grid.measure(OFF_CENTER)
    assert (bounds.x0, bounds.x1, bounds.y0, bounds.y1) == pytest.approx((4, 20, 1, 17), abs=0.2)


def test_plan_adjustment_is_none_when_centered_and_inside_live_area():
    assert grid.plan_adjustment(grid.measure(CENTERED)) is None


def test_plan_adjustment_centers_off_center_glyph():
    adjustment = grid.plan_adjustment(grid.measure(OFF_CENTER))
    assert adjustment.scale == 1.0
    assert adjustment.dy == pytest.approx(3.0, abs=0.2)
    assert adjustment.dx == pytest.approx(0.0, abs=0.2)


def test_plan_adjustment_shrinks_glyph_that_exceeds_live_area():
    adjustment = grid.plan_adjustment(grid.measure(OVERSIZE))
    assert adjustment.scale == pytest.approx(grid.LIVE_AREA / 24, abs=0.01)


def test_apply_adjustment_leaves_glyph_centered_and_is_stable():
    adjusted = grid.apply_adjustment(OFF_CENTER, grid.plan_adjustment(grid.measure(OFF_CENTER)))
    bounds = grid.measure(adjusted)
    assert bounds.center_x == pytest.approx(12, abs=0.2)
    assert bounds.center_y == pytest.approx(12, abs=0.2)
    assert grid.plan_adjustment(bounds) is None


def test_unwrap_restores_original_markup():
    adjusted = grid.apply_adjustment(OFF_CENTER, grid.plan_adjustment(grid.measure(OFF_CENTER)))
    assert grid.unwrap(adjusted) == OFF_CENTER


def test_normalize_canvas_sets_standard_width_and_height():
    original = _svg('x="4" y="4" width="16" height="16"', size="64")
    assert not grid.canvas_is_standard(original)
    normalized = grid.normalize_canvas(original)
    assert grid.canvas_is_standard(normalized)
    assert 'width="64"' not in normalized


def test_fix_icon_normalizes_file_once_and_keeps_it_stable(tmp_path):
    pack = tmp_path / "outline"
    pack.mkdir()
    icon = pack / "box-outline.svg"
    icon.write_text(_svg('x="4" y="1" width="16" height="16"', size="64"), encoding="utf-8")

    report = grid.analyze(icon)
    assert {"DESCENTRADO", "LIENZO"} <= set(report.issues)
    assert grid.fix_icon(report) is True
    assert grid.analyze(icon).issues == []
    assert grid.fix_icon(grid.analyze(icon)) is False


def test_iter_pack_icons_skips_shared_pack(tmp_path):
    for pack in ("outline", grid.SHARED_PACK_DIR):
        (tmp_path / pack).mkdir()
        (tmp_path / pack / "a.svg").write_text(CENTERED, encoding="utf-8")
    assert [p.parent.name for p in grid.iter_pack_icons(tmp_path)] == ["outline"]


def test_optical_center_exempt_icon_keeps_its_offset_but_still_shrinks_when_oversize(tmp_path):
    pack = tmp_path / "outline"
    pack.mkdir()
    icon = pack / "play-outline.svg"
    icon.write_text(OFF_CENTER, encoding="utf-8")
    assert "DESCENTRADO" not in grid.analyze(icon).issues
    assert grid.plan_adjustment(grid.measure(OFF_CENTER), keep_center=True) is None

    shrunk = grid.plan_adjustment(grid.measure(OVERSIZE), keep_center=True)
    assert shrunk.scale < 1.0
    assert shrunk.dx == pytest.approx(12 * (1 - shrunk.scale), abs=0.01)
