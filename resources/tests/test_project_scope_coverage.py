# resources\tests\test_project_scope_coverage.py

from resources.tools import _project_sources as sources
from resources.tools import project_scope_coverage_auditor as coverage


def _make_project(root, files):
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _use_project(monkeypatch, root):
    monkeypatch.setattr(sources, "PROJECT_ROOT", root)
    monkeypatch.setattr(coverage, "PROJECT_ROOT", root)
    monkeypatch.setattr(coverage, "TOOLS_DIR", root / "resources" / "tools")
    monkeypatch.setattr(coverage, "SUITE_FILE", root / "resources" / "tools" / "project_quality_suite.py")


def test_new_and_root_files_are_discovered_and_zones_filter(tmp_path, monkeypatch):
    _make_project(tmp_path, {
        "backend/a.py": "", "frontend/b.py": "", "main.py": "", "plugins/new_feature.py": "",
        "backend/__pycache__/skip.py": "", "docs/walkthroughs/skip.py": "",
    })
    _use_project(monkeypatch, tmp_path)

    names = {p.relative_to(tmp_path).as_posix() for p in sources.iter_python_files()}
    assert names == {"backend/a.py", "frontend/b.py", "main.py", "plugins/new_feature.py"}

    only_backend = sources.iter_python_files(("backend",))
    assert [p.name for p in only_backend] == ["a.py"]
    assert sources.unclassified_zones() == {"plugins": 1}


def test_ignored_dirs_are_matched_relative_to_project_root(tmp_path, monkeypatch):
    project = tmp_path / "build" / "tools" / "MiniKick"
    _make_project(project, {"backend/a.py": ""})
    _use_project(monkeypatch, project)

    assert [p.name for p in sources.iter_python_files()] == ["a.py"]


def test_audit_reports_unclassified_unparsable_stale_and_unregistered(tmp_path, monkeypatch):
    _make_project(tmp_path, {
        "backend/ok.py": "x = 1\n",
        "backend/broken.py": "def (:\n",
        "plugins/new_feature.py": "",
        "resources/tools/project_quality_suite.py": 'tool_filename="registered_auditor.py"\n',
        "resources/tools/registered_auditor.py": 'EXCLUDED = {"ok.py", "ghost.py", "__init__.py", "api_keys.py"}\n',
        "resources/tools/forgotten_auditor.py": "",
    })
    _use_project(monkeypatch, tmp_path)

    issues = {(i.rule, i.location) for i in coverage.audit_scope_coverage()}
    assert issues == {
        ("UNCLASSIFIED_ZONE", "plugins/"),
        ("UNPARSABLE_FILE", "backend/broken.py"),
        ("STALE_FILE_REFERENCE", "resources/tools/registered_auditor.py:1"),
        ("UNREGISTERED_AUDITOR", "resources/tools/forgotten_auditor.py"),
    }


def test_clean_project_has_no_coverage_issues(tmp_path, monkeypatch):
    _make_project(tmp_path, {
        "backend/ok.py": "x = 1\n",
        "resources/tools/project_quality_suite.py": 'tool_filename="a_auditor.py"\n',
        "resources/tools/a_auditor.py": 'SKIP = {"ok.py"}\n',
    })
    _use_project(monkeypatch, tmp_path)

    assert coverage.audit_scope_coverage() == []
