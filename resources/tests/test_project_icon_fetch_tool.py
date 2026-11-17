# resources\tests\test_project_icon_fetch_tool.py
"""Generación de packs desde Iconify: tabla de equivalencias, alias, plantilla SVG y lotes de consulta."""

import pytest

from resources.tools import project_icon_fetch_tool as fetch

PAYLOAD = {
    "width": 24,
    "height": 24,
    "icons": {
        "check": {"body": '<path d="M20 6L9 17l-5-5"/>'},
        "funnel": {"body": '<path d="M3 4h18"/>', "hidden": True},
        "big": {"body": "<path/>", "width": 32, "height": 32},
        "flipped": {"body": "<path/>", "hFlip": True},
    },
    "aliases": {
        "tick": {"parent": "check"},
        "tick-flip": {"parent": "check", "hFlip": True},
    },
}


class FakeClient:
    def __init__(self):
        self.calls = []

    def fetch(self, prefix, names):
        self.calls.append((prefix, list(names)))
        return PAYLOAD


@pytest.fixture
def icons_dir(tmp_path):
    base = tmp_path / fetch.BASE_PACK_DIR
    base.mkdir()
    for stem in ("check-outline", "filter-outline", "radio-dot", "missing-outline"):
        (base / f"{stem}.svg").write_text("<svg/>", encoding="utf-8")
    return tmp_path


@pytest.fixture
def pack(monkeypatch):
    source = fetch.PackSource(prefix="demo", overrides={"filter-outline": "funnel"}, skip=frozenset({"radio-dot"}))
    monkeypatch.setitem(fetch.PACKS, "demo", source)
    return "demo"


def test_iconify_name_uses_override_then_drops_outline_suffix_and_honours_skip():
    source = fetch.PackSource(prefix="x", overrides={"gear-outline": "settings"}, skip=frozenset({"radio-dot"}))
    assert source.iconify_name("gear-outline") == "settings"
    assert source.iconify_name("check-outline") == "check"
    assert source.iconify_name("grip-vertical") == "grip-vertical"
    assert source.iconify_name("radio-dot") is None


def test_resolve_body_follows_alias_and_accepts_hidden_icons():
    assert fetch.resolve_body(PAYLOAD, "tick") == PAYLOAD["icons"]["check"]["body"]
    assert fetch.resolve_body(PAYLOAD, "funnel") == PAYLOAD["icons"]["funnel"]["body"]


@pytest.mark.parametrize("name", ["tick-flip", "flipped", "big", "does-not-exist"])
def test_resolve_body_rejects_transforms_other_grids_and_missing_icons(name):
    assert fetch.resolve_body(PAYLOAD, name) is None


def test_fetch_pack_writes_template_svg_and_reports_every_outcome(icons_dir, pack):
    report = fetch.fetch_pack(pack, FakeClient(), icons_dir)

    assert sorted(report.written) == ["check-outline", "filter-outline"]
    assert report.covered_by_fallback == ["radio-dot"]
    assert report.unusable == {"missing-outline": "missing"}
    svg = (icons_dir / "demo" / "check-outline.svg").read_text(encoding="utf-8")
    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">')
    assert PAYLOAD["icons"]["check"]["body"] in svg
    assert not (icons_dir / "demo" / "radio-dot.svg").exists()


def test_fetch_pack_queries_iconify_in_batches(icons_dir, pack, monkeypatch):
    monkeypatch.setattr(fetch, "BATCH_SIZE", 2)
    client = FakeClient()
    fetch.fetch_pack(pack, client, icons_dir)
    assert [len(names) for _, names in client.calls] == [2, 1]
    assert {prefix for prefix, _ in client.calls} == {"demo"}


def test_plan_pack_can_be_limited_to_some_icons(icons_dir, pack):
    assert fetch.plan_pack(pack, icons_dir, only={"filter-outline"}) == {"filter-outline": "funnel"}


@pytest.mark.parametrize("pack_name", ["lucide"])
def test_equivalence_table_only_mentions_icons_that_exist_in_the_base_pack(pack_name):
    source = fetch.PACKS[pack_name]
    base = set(fetch.list_base_icons())
    assert set(source.overrides) <= base
    assert set(source.skip) <= base
