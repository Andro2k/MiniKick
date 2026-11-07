from pathlib import Path

from frontend.common.icons import (
    _colorize_svg,
    get_icon_colored,
    get_pixmap_colored,
    get_qss_colored_icon,
)


def test_colored_icon_and_pixmap_share_rendered_icon(qapp):
    icon = get_icon_colored("circle-info-filled.svg", "#ABCDEF", size=24, dpr=1)
    pixmap = get_pixmap_colored("circle-info-filled.svg", "#ABCDEF", size=24, dpr=1)

    assert not icon.isNull()
    assert not pixmap.isNull()
    assert pixmap.size().width() == 24
    assert pixmap.size().height() == 24


def test_svg_colorization_preserves_none_and_recolors_explicit_attributes():
    svg = '<svg><path fill="currentColor"/><path fill="#fff" stroke="#000"/><path fill="none"/></svg>'

    result = _colorize_svg(svg, "#ABCDEF", force_explicit=True)

    assert result == '<svg><path fill="#ABCDEF"/><path fill="#ABCDEF" stroke="#ABCDEF"/><path fill="none"/></svg>'


def test_qss_colored_icon_uses_shared_svg_colorization(tmp_path, monkeypatch):
    from frontend.common import icons

    monkeypatch.setattr(icons, "_QSS_ICON_CACHE_DIR", tmp_path)
    get_qss_colored_icon.cache_clear()
    try:
        path = get_qss_colored_icon("circle-info-filled.svg", "#ABCDEF")
        svg = Path(path).read_text(encoding="utf-8")
    finally:
        get_qss_colored_icon.cache_clear()

    assert "#ABCDEF" in svg
    assert "currentColor" not in svg
