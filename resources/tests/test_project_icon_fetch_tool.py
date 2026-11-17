# resources\tests\test_project_icon_fetch_tool.py
"""Descarga de iconos de Lucide por nombre: alias, plantilla SVG, lotes y nombres de entrada."""

import pytest

from resources.tools import project_icon_fetch_tool as fetch

PAYLOAD = {
    "width": 24,
    "height": 24,
    "icons": {
        "check": {"body": '<path d="M20 6L9 17l-5-5"/>'},
        "square-pen": {"body": '<path d="M12 3H5"/>'},
        "smile": {"body": '<circle cx="12" cy="12" r="10"/>', "hidden": True},
        "big": {"body": "<path/>", "width": 32, "height": 32},
        "flipped": {"body": "<path/>", "hFlip": True},
    },
    "aliases": {
        "tick": {"parent": "check"},
        "edit": {"parent": "square-pen"},
        "tick-flip": {"parent": "check", "hFlip": True},
    },
}


class FakeClient:
    def __init__(self):
        self.calls = []

    def fetch(self, prefix, names):
        self.calls.append((prefix, list(names)))
        return PAYLOAD


def test_resolve_icon_returns_canonical_name_and_body_following_aliases():
    assert fetch.resolve_icon(PAYLOAD, "edit") == ("square-pen", PAYLOAD["icons"]["square-pen"]["body"])
    assert fetch.resolve_icon(PAYLOAD, "check") == ("check", PAYLOAD["icons"]["check"]["body"])


def test_resolve_icon_accepts_hidden_icons():
    assert fetch.resolve_icon(PAYLOAD, "smile")[0] == "smile"


@pytest.mark.parametrize("name", ["tick-flip", "flipped", "big", "does-not-exist"])
def test_resolve_icon_rejects_transforms_other_grids_and_missing_icons(name):
    assert fetch.resolve_icon(PAYLOAD, name) is None


def test_normalize_names_accepts_file_names_paths_and_drops_duplicates():
    assert fetch.normalize_names(["check", "check.svg", " icons/lucide/chevron-down.svg ", ""]) == ["check", "chevron-down"]


def test_fetch_icons_writes_template_svg_under_the_canonical_name(tmp_path):
    report = fetch.fetch_icons(["check", "edit", "nope"], FakeClient(), tmp_path)

    assert report.written == ["check", "square-pen"]
    assert report.renamed == {"edit": "square-pen"}
    assert report.unusable == ["nope"]
    svg = (tmp_path / "lucide" / "check.svg").read_text(encoding="utf-8")
    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">')
    assert PAYLOAD["icons"]["check"]["body"] in svg
    assert (tmp_path / "lucide" / "square-pen.svg").exists()
    assert not (tmp_path / "lucide" / "edit.svg").exists()


def test_fetch_icons_queries_iconify_in_batches(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "BATCH_SIZE", 2)
    client = FakeClient()
    fetch.fetch_icons(["check", "edit", "smile"], client, tmp_path)
    assert [len(names) for _, names in client.calls] == [2, 1]
    assert {prefix for prefix, _ in client.calls} == {fetch.ICONIFY_PREFIX}


def test_list_pack_icons_returns_the_names_already_in_the_pack(tmp_path):
    pack = tmp_path / "lucide"
    pack.mkdir()
    for name in ("b", "a"):
        (pack / f"{name}.svg").write_text("<svg/>", encoding="utf-8")
    (pack / "LICENSE").write_text("ISC", encoding="utf-8")
    assert fetch.list_pack_icons(tmp_path) == ["a", "b"]
