# resources\tests\test_git_manager.py

import contextlib
import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def _find_tool() -> Path:
    for candidate in Path(__file__).resolve().parents:
        tool = candidate / "resources" / "tools" / "git_manager.py"
        if tool.is_file():
            return tool
    raise FileNotFoundError("No se encontró resources/tools/git_manager.py")

TOOL_PATH = _find_tool()
def _load_tool():
    spec = importlib.util.spec_from_file_location("git_manager_under_test", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        yield buf

class GitManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.gm = _load_tool()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.origin = root / "origin.git"
        self.work = root / "work"
        subprocess.run(["git", "init", "-q", "--bare", str(self.origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.work)], check=True, capture_output=True)
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "Tester")
        self.git("checkout", "-q", "-b", "main")

        version = self.work / "backend" / "config" / "version.py"
        version.parent.mkdir(parents=True)
        version.write_bytes(b'APP_VERSION = "v1.0.0"\r\n')
        (self.work / "a.txt").write_text("base\n", encoding="utf-8")
        old = self.work / "docs" / "old"
        old.mkdir(parents=True)
        (old / "x.md").write_text("x\n", encoding="utf-8")
        (old / "y.md").write_text("y\n", encoding="utf-8")
        self.commit_all("base")
        self.git("push", "-q", "-u", "origin", "main")

        self.git("checkout", "-q", "-b", "release/v1.0.0")
        (self.work / "r.txt").write_text("release\n", encoding="utf-8")
        self.commit_all("release work")
        self.git("push", "-q", "-u", "origin", "release/v1.0.0")

        self.git("checkout", "-q", "main")
        (self.work / "m.txt").write_text("main\n", encoding="utf-8")
        self.git("rm", "-q", "-r", "docs/old")
        self.commit_all("main moves on")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "release/v1.0.0")

        self.gm.PROJECT_ROOT = str(self.work)
        self.gm.VERSION_FILE = str(version)
        self.gm.GitRunner.run(["fetch", "origin", "--prune"])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def git(self, *args: str) -> str:
        res = subprocess.run(["git", *args], cwd=self.work, check=True, capture_output=True, text=True)
        return res.stdout.strip()

    def commit_all(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def test_branch_vs_main_counts_ahead_and_behind(self) -> None:
        self.assertEqual(self.gm.GitAuditService.get_branch_vs_main(), (1, 1))

    def test_main_only_summary_reports_deleted_folder(self) -> None:
        summary = self.gm.GitAuditService.get_main_only_changes()
        self.assertEqual(summary.counts.get("A"), 1)
        self.assertEqual(summary.counts.get("D"), 2)
        self.assertEqual(summary.deleted_dirs, [("docs/old", 2)])

    def test_runner_environment_is_non_interactive(self) -> None:
        env = self.gm.GitRunner._env()
        self.assertEqual(env["GIT_EDITOR"], "true")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(env["GIT_MERGE_AUTOEDIT"], "no")

    def test_update_merges_cleanly(self) -> None:
        with quiet():
            self.assertTrue(self.gm.GitReleaseWorkflow.update_from_main(assume_yes=True))
        self.assertEqual(self.gm.GitAuditService.get_branch_vs_main()[1], 0)
        parents = self.git("rev-list", "--parents", "-n", "1", "HEAD").split()
        self.assertEqual(len(parents), 3, "HEAD debe ser un commit de merge (2 padres)")
        self.assertFalse((self.work / "docs" / "old").exists())

    def test_update_refuses_dirty_tracked_tree(self) -> None:
        (self.work / "a.txt").write_text("cambio local\n", encoding="utf-8")
        with quiet():
            self.assertFalse(self.gm.GitReleaseWorkflow.update_from_main(assume_yes=True))
        self.assertEqual(self.gm.GitAuditService.get_branch_vs_main()[1], 1)

    def test_update_conflict_is_reported_and_merge_left_open(self) -> None:
        self.git("checkout", "-q", "main")
        (self.work / "a.txt").write_text("version main\n", encoding="utf-8")
        self.commit_all("main edits a")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "release/v1.0.0")
        (self.work / "a.txt").write_text("version release\n", encoding="utf-8")
        self.commit_all("release edits a")
        with quiet() as out:
            self.assertFalse(self.gm.GitReleaseWorkflow.update_from_main(assume_yes=True))
        self.assertIn("a.txt", out.getvalue())
        self.assertEqual(self.gm.GitAuditService.in_progress_operation(), "merge")
        self.assertEqual(self.gm.GitAuditService.unmerged_files(), ["a.txt"])

    def test_recovers_merge_when_merge_msg_is_missing(self) -> None:
        subprocess.run(["git", "merge", "--no-commit", "--no-ff", "origin/main"], cwd=self.work, capture_output=True)
        merge_msg = self.work / ".git" / "MERGE_MSG"
        self.assertTrue(merge_msg.exists())
        merge_msg.unlink()
        with quiet():
            ok = self.gm.GitReleaseWorkflow._recover_merge("release/v1.0.0", "fatal: Could not read from '.git/MERGE_MSG'")
        self.assertTrue(ok)
        self.assertIsNone(self.gm.GitAuditService.in_progress_operation())
        self.assertEqual(self.gm.GitAuditService.get_branch_vs_main()[1], 0)

    def test_recover_accepts_merge_that_already_completed(self) -> None:
        with quiet():
            self.assertTrue(self.gm.GitReleaseWorkflow.update_from_main(assume_yes=True))
            self.assertTrue(self.gm.GitReleaseWorkflow._recover_merge("release/v1.0.0", "fatal: MERGE_MSG"))

    def _make_release_merged_into_main(self) -> None:
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "PR merged", "release/v1.0.0")
        self.git("branch", "release/v0.9.0", "main")
        self.git("push", "-q", "origin", "main", "release/v0.9.0")
        self.git("checkout", "-q", "release/v1.0.0")
        self.gm.GitRunner.run(["fetch", "origin", "--prune"])

    def test_cleanup_never_lists_active_or_version_branch(self) -> None:
        self._make_release_merged_into_main()
        local, remote = self.gm.GitAuditService.get_merged_release_branches()
        self.assertEqual(local, ["release/v0.9.0"])
        self.assertEqual(remote, ["release/v0.9.0"])

    def test_cleanup_without_confirmation_deletes_nothing(self) -> None:
        self._make_release_merged_into_main()
        with mock.patch("sys.stdin") as fake_stdin, quiet():
            fake_stdin.isatty.return_value = False
            self.gm.GitReleaseWorkflow.cleanup_merged(assume_yes=False)
        self.assertIn("release/v0.9.0", self.git("branch", "--list", "release/v0.9.0"))

    def test_cleanup_with_yes_deletes_only_stale_branches(self) -> None:
        self._make_release_merged_into_main()
        with quiet():
            self.gm.GitReleaseWorkflow.cleanup_merged(assume_yes=True)
        self.assertEqual(self.git("branch", "--list", "release/v0.9.0"), "")
        self.assertIn("release/v1.0.0", self.git("branch", "--list", "release/v1.0.0"))
        remote_heads = subprocess.run(["git", "ls-remote", "--heads", str(self.origin)], capture_output=True, text=True).stdout
        self.assertIn("refs/heads/release/v1.0.0", remote_heads)
        self.assertNotIn("refs/heads/release/v0.9.0", remote_heads)

    def test_start_release_branches_from_origin_main_and_keeps_crlf(self) -> None:
        with quiet():
            self.gm.GitReleaseWorkflow.start_release("v1.1.0")
        self.assertEqual(self.gm.GitAuditService.get_current_branch(), "release/v1.1.0")
        self.assertEqual(self.git("rev-parse", "HEAD~1"), self.git("rev-parse", "origin/main"))
        content = (self.work / "backend" / "config" / "version.py").read_bytes()
        self.assertEqual(content, b'APP_VERSION = "v1.1.0"\r\n')
        heads = subprocess.run(["git", "ls-remote", "--heads", str(self.origin)], capture_output=True, text=True).stdout
        self.assertIn("refs/heads/release/v1.1.0", heads)

    def test_start_release_does_not_recreate_existing_branch(self) -> None:
        head_before = self.git("rev-parse", "HEAD")
        with quiet() as out:
            self.gm.GitReleaseWorkflow.start_release("v1.0.0")
        self.assertIn("ya existe", out.getvalue())
        self.assertEqual(self.git("rev-parse", "HEAD"), head_before)

    def test_doctor_fails_while_merge_is_open(self) -> None:
        subprocess.run(["git", "merge", "--no-commit", "--no-ff", "origin/main"], cwd=self.work, capture_output=True)
        checks = {c.name: c for c in self.gm.DoctorService.run_checks(fetch=False)}
        self.assertEqual(checks["Operación en curso"].status, "FAIL")

    def test_doctor_flags_ignored_tests_folder(self) -> None:
        (self.work / "tests").mkdir()
        (self.work / "tests" / "test_x.py").write_text("x = 1\n", encoding="utf-8")
        (self.work / ".gitignore").write_text("tests\n", encoding="utf-8")
        checks = {c.name: c for c in self.gm.DoctorService.run_checks(fetch=False)}
        self.assertEqual(checks["Tests en Git"].status, "FAIL")

    def test_doctor_warns_when_branch_is_behind_main(self) -> None:
        checks = {c.name: c for c in self.gm.DoctorService.run_checks(fetch=False)}
        self.assertEqual(checks["Rama vs main"].status, "WARN")
        self.assertIn("docs/old", checks["Rama vs main"].detail)

if __name__ == "__main__":
    unittest.main()
