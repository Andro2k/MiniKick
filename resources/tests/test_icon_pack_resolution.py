# resources\tests\test_icon_pack_resolution.py
"""Resolución de iconos por packs: pack activo -> common -> base -> raíz de icons/."""

import os

import pytest

from frontend.common import icons


@pytest.fixture
def icons_root(tmp_path, monkeypatch):
    monkeypatch.setattr(icons, "get_assets_path", lambda sub="": os.path.join(str(tmp_path), sub))
    return tmp_path


def _touch(root, *parts):
    path = root.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<svg/>", encoding="utf-8")
    return str(path)


def test_real_assets_resolve_from_their_packs():
    assert icons.resolve_icon_path("check-outline.svg").endswith("assets/icons/outline/check-outline.svg")
    assert icons.resolve_icon_path("brand-kick.svg").endswith("assets/icons/common/brand-kick.svg")
    assert icons.resolve_icon_path("icons/chevron-down-outline.svg").endswith("outline/chevron-down-outline.svg")
    assert icons.resolve_icon_path("icon.ico").endswith("assets/icons/icon.ico")


def test_missing_icon_returns_none():
    assert icons.resolve_icon_path("does-not-exist.svg") is None
    assert icons.resolve_icon_path("") is None


def test_active_pack_wins_over_common_and_base(icons_root, monkeypatch):
    monkeypatch.setattr(icons, "ACTIVE_ICON_PACK", "alt")
    _touch(icons_root, "icons", "outline", "a.svg")
    _touch(icons_root, "icons", "common", "a.svg")
    alt = _touch(icons_root, "icons", "alt", "a.svg")
    assert os.path.normpath(icons.resolve_icon_path("a.svg")) == os.path.normpath(alt)


def test_common_comes_before_base_when_active_pack_lacks_the_icon(icons_root, monkeypatch):
    monkeypatch.setattr(icons, "ACTIVE_ICON_PACK", "alt")
    _touch(icons_root, "icons", "outline", "a.svg")
    common = _touch(icons_root, "icons", "common", "a.svg")
    assert os.path.normpath(icons.resolve_icon_path("a.svg")) == os.path.normpath(common)


def test_base_pack_is_the_last_pack_fallback(icons_root, monkeypatch):
    monkeypatch.setattr(icons, "ACTIVE_ICON_PACK", "alt")
    base = _touch(icons_root, "icons", "outline", "a.svg")
    assert os.path.normpath(icons.resolve_icon_path("a.svg")) == os.path.normpath(base)
