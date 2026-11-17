# resources\tests\test_project_icon_integrity_tool.py
"""Recolección de iconos por packs: nombres repetidos entre packs y archivos que no son iconos."""

from resources.tools import project_icon_integrity_tool as integrity


def test_collect_icon_files_groups_same_name_across_packs_and_ignores_licenses(tmp_path):
    for pack in ("lucide", "common"):
        (tmp_path / pack).mkdir()
        (tmp_path / pack / "check.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "lucide" / "LICENSE").write_text("ISC", encoding="utf-8")
    (tmp_path / "icon.ico").write_bytes(b"ico")

    found = integrity.collect_icon_files(str(tmp_path))

    assert sorted(found) == ["check.svg", "icon.ico"]
    assert len(found["check.svg"]) == 2
