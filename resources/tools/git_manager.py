# resources/tools/git_manager.py

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")


def _resolve_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "backend").exists() and (parent / "frontend").exists():
            return parent
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VERSION_FILE = PROJECT_ROOT / "backend" / "config" / "version.py"
GITHUB_REPO_URL = "https://github.com/Andro2k/MiniKick"
DEFAULT_REMOTE = "origin"
MAIN_BRANCH = "main"
REMOTE_MAIN = f"{DEFAULT_REMOTE}/{MAIN_BRANCH}"
TEST_DIRS = ("tests", "resources/tests")


class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def strip(cls, text: str) -> str:
        return re.sub(r"\033\[[0-9;]*m", "", text)


def confirm(prompt: str, assume_yes: bool = False) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        print(f"  {Colors.YELLOW}(Modo no interactivo: añade --yes para confirmar){Colors.RESET}")
        return False
    try:
        return input(f"{prompt} (s/n) [s]: ").strip().lower() in ("", "s", "si", "y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


class GitRunner:
    DEFAULT_TIMEOUT = 120

    @staticmethod
    def _env() -> Dict[str, str]:
        env = os.environ.copy()
        env.update({
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_EDITOR": "true",
            "GIT_MERGE_AUTOEDIT": "no",
            "LC_ALL": "C",
        })
        return env

    @staticmethod
    def run(args: List[str], cwd: Optional[Path] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        limit = timeout or GitRunner.DEFAULT_TIMEOUT
        target_dir = Path(cwd or PROJECT_ROOT)
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=target_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                env=GitRunner._env(),
                timeout=limit,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", f"Tiempo agotado ({limit}s) ejecutando: git {' '.join(args)}"
        except Exception as ex:
            return -1, "", str(ex)


class VersionManager:
    @staticmethod
    def get_version() -> str:
        vpath = Path(VERSION_FILE)
        if not vpath.is_file():
            return "v1.0.0"
        content = vpath.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r'APP_VERSION\s*=\s*["\'](v?[^"\']+)["\']', content)
        return match.group(1).strip() if match else "v1.0.0"

    @staticmethod
    def set_version(new_version: str) -> bool:
        clean_ver = new_version if new_version.startswith("v") else f"v{new_version}"
        vpath = Path(VERSION_FILE)
        if not vpath.is_file():
            return False
        content = vpath.read_text(encoding="utf-8", errors="ignore")
        new_content = re.sub(
            r'APP_VERSION\s*=\s*["\'][^"\']+["\']',
            f'APP_VERSION = "{clean_ver}"',
            content,
        )
        if new_content == content:
            return False
        vpath.write_text(new_content, encoding="utf-8")
        return True

    @staticmethod
    def bump_semver(current_version: str, bump_type: str = "patch") -> str:
        clean = current_version.lstrip("v")
        nums = [int(n) for n in re.findall(r"\d+", clean)]
        while len(nums) < 3:
            nums.append(0)
        major, minor, patch = nums[:3]

        if bump_type == "major":
            major, minor, patch = major + 1, 0, 0
        elif bump_type == "minor":
            minor, patch = minor + 1, 0
        else:
            patch += 1

        return f"v{major}.{minor}.{patch}"


@dataclass(slots=True)
class ChangeSummary:
    counts: Dict[str, int] = field(default_factory=dict)
    deleted_dirs: List[Tuple[str, int]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


class GitAuditService:
    @staticmethod
    def get_current_branch() -> str:
        code, out, _ = GitRunner.run(["rev-parse", "--abbrev-ref", "HEAD"])
        return out if code == 0 else "unknown"

    @staticmethod
    def ref_exists(ref: str) -> bool:
        code, _, _ = GitRunner.run(["rev-parse", "--verify", "--quiet", ref])
        return code == 0

    @staticmethod
    def get_upstream() -> Optional[str]:
        code, out, _ = GitRunner.run(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        return out if code == 0 and out else None

    @staticmethod
    def ahead_behind(left: str, right: str) -> Tuple[int, int]:
        code, out, _ = GitRunner.run(["rev-list", "--left-right", "--count", f"{left}...{right}"])
        if code != 0 or not out:
            return 0, 0
        parts = out.split()
        return (int(parts[0]), int(parts[1])) if len(parts) == 2 else (0, 0)

    @staticmethod
    def get_main_divergence() -> Tuple[int, int]:
        return GitAuditService.ahead_behind(MAIN_BRANCH, REMOTE_MAIN)

    @staticmethod
    def get_branch_vs_main() -> Tuple[int, int]:
        if not GitAuditService.ref_exists(REMOTE_MAIN):
            return 0, 0
        return GitAuditService.ahead_behind("HEAD", REMOTE_MAIN)

    @staticmethod
    def is_working_tree_clean() -> Tuple[bool, List[str]]:
        code, out, _ = GitRunner.run(["status", "--porcelain"])
        if code != 0 or not out:
            return True, []
        files = [line.strip() for line in out.splitlines() if line.strip()]
        return len(files) == 0, files

    @staticmethod
    def tracked_changes() -> List[str]:
        code, out, _ = GitRunner.run(["status", "--porcelain", "--untracked-files=no"])
        if code != 0 or not out:
            return []
        return [line.strip() for line in out.splitlines() if line.strip()]

    @staticmethod
    def unmerged_files() -> List[str]:
        code, out, _ = GitRunner.run(["diff", "--name-only", "--diff-filter=U"])
        return [line.strip() for line in out.splitlines() if line.strip()] if code == 0 else []

    @staticmethod
    def _git_dir() -> Path:
        code, out, _ = GitRunner.run(["rev-parse", "--git-dir"])
        root_p = Path(PROJECT_ROOT)
        if code != 0 or not out:
            return root_p / ".git"
        p = Path(out)
        return p if p.is_absolute() else root_p / p

    @staticmethod
    def in_progress_operation() -> Optional[str]:
        git_dir = GitAuditService._git_dir()
        markers = (
            ("MERGE_HEAD", "merge"),
            ("rebase-merge", "rebase"),
            ("rebase-apply", "rebase"),
            ("CHERRY_PICK_HEAD", "cherry-pick"),
            ("REVERT_HEAD", "revert"),
        )
        for name, label in markers:
            if (git_dir / name).exists():
                return label
        return None

    @staticmethod
    def has_index_lock() -> bool:
        return (GitAuditService._git_dir() / "index.lock").exists()

    @staticmethod
    def summarize_name_status(text: str) -> ChangeSummary:
        summary = ChangeSummary()
        deleted: Dict[str, int] = {}
        for line in text.splitlines():
            parts = line.split("\t", 1)
            if len(parts) != 2 or not parts[0]:
                continue
            status, path = parts[0][0], parts[1].replace("\\", "/")
            summary.counts[status] = summary.counts.get(status, 0) + 1
            if status == "D":
                segs = path.split("/")
                folder = "/".join(segs[:2]) if len(segs) > 2 else (segs[0] if len(segs) > 1 else "(raíz)")
                deleted[folder] = deleted.get(folder, 0) + 1
        summary.deleted_dirs = sorted(deleted.items(), key=lambda kv: kv[1], reverse=True)[:3]
        return summary

    @staticmethod
    def get_main_only_changes() -> ChangeSummary:
        code, out, _ = GitRunner.run(["diff", "--name-status", "--no-renames", f"HEAD...{REMOTE_MAIN}"])
        return GitAuditService.summarize_name_status(out if code == 0 else "")

    @staticmethod
    def protected_release_branches() -> List[str]:
        return [GitAuditService.get_current_branch(), f"release/{VersionManager.get_version()}"]

    @staticmethod
    def get_merged_release_branches() -> Tuple[List[str], List[str]]:
        local_merged: List[str] = []
        remote_merged: List[str] = []
        protected = set(GitAuditService.protected_release_branches())

        code, out, _ = GitRunner.run(["branch", "--merged", REMOTE_MAIN])
        if code == 0:
            for b in out.splitlines():
                clean_b = b.replace("*", "").strip()
                if clean_b.startswith("release/") and clean_b not in protected:
                    local_merged.append(clean_b)

        code_rem, out_rem, _ = GitRunner.run(["branch", "-r", "--merged", REMOTE_MAIN])
        if code_rem == 0:
            for b in out_rem.splitlines():
                clean_b = b.strip()
                if clean_b.startswith(f"{DEFAULT_REMOTE}/release/"):
                    branch_name = clean_b[len(DEFAULT_REMOTE) + 1:]
                    if branch_name not in protected:
                        remote_merged.append(branch_name)

        return local_merged, remote_merged


@dataclass(slots=True)
class Check:
    name: str
    status: str
    detail: str
    fix: str = ""


class DoctorService:
    @staticmethod
    def venv_python() -> Optional[Path]:
        root_p = Path(PROJECT_ROOT)
        for rel in (Path(".venv/Scripts/python.exe"), Path(".venv/bin/python")):
            path = root_p / rel
            if path.is_file():
                return path
        return None

    @staticmethod
    def project_python() -> str:
        venv = DoctorService.venv_python()
        return str(venv) if venv else sys.executable

    @staticmethod
    def _check_interpreter() -> Check:
        venv = DoctorService.venv_python()
        if not venv:
            return Check("Intérprete", "WARN", "No existe la carpeta .venv del proyecto.", "uv sync   (o crea el entorno virtual)")
        root_p = Path(PROJECT_ROOT)
        venv_dir = (root_p / ".venv").resolve()
        prefix = Path(sys.prefix).resolve()
        if prefix == venv_dir or venv_dir in prefix.parents:
            return Check("Intérprete", "OK", f"Usando el entorno del proyecto ({sys.executable}).")
        return Check(
            "Intérprete", "WARN",
            f"Estás usando {sys.executable}, no el .venv del proyecto (faltarán PySide6 y demás dependencias).",
            r"Activa el entorno: .\.venv\Scripts\Activate.ps1   (o ejecuta con: uv run python ...)",
        )

    @staticmethod
    def _check_pyside() -> Check:
        python = DoctorService.project_python()
        try:
            ok = subprocess.run([python, "-c", "import PySide6"], capture_output=True, timeout=60).returncode == 0
        except Exception:
            ok = False
        if ok:
            return Check("PySide6", "OK", "Importable con el intérprete del proyecto.")
        return Check("PySide6", "FAIL", f"No se puede importar PySide6 con {python}.", "uv sync   (o pip install -r requirements.txt)")

    @staticmethod
    def _check_api_keys() -> Check:
        path = Path(PROJECT_ROOT) / "backend" / "config" / "api_keys.py"
        if path.is_file():
            return Check("api_keys.py", "OK", "Presente (credenciales reales).")
        return Check("api_keys.py", "WARN", "No existe: el backend importa con credenciales vacías y los logins no funcionarán.", "Crea backend/config/api_keys.py con tus claves.")

    @staticmethod
    def _check_operation() -> List[Check]:
        checks: List[Check] = []
        op = GitAuditService.in_progress_operation()
        if op == "merge":
            conflicts = GitAuditService.unmerged_files()
            detail = f"Hay un merge a medias ({len(conflicts)} archivo(s) en conflicto)." if conflicts else "Hay un merge a medias, sin conflictos pendientes."
            fix = "Resuelve los conflictos, git add <archivos> y git commit -m \"Merge origin/main\"; o cancela con: git merge --abort" if conflicts \
                else "git commit -m \"Merge origin/main\"   (o cancela con: git merge --abort)"
            checks.append(Check("Operación en curso", "FAIL", detail, fix))
        elif op:
            checks.append(Check("Operación en curso", "FAIL", f"Hay un {op} a medias.", f"Termínalo o cancélalo (git {op} --abort)."))
        else:
            checks.append(Check("Operación en curso", "OK", "Ningún merge/rebase pendiente."))

        if GitAuditService.has_index_lock():
            checks.append(Check("index.lock", "WARN", "Existe .git/index.lock (otro git/IDE lo está usando, o quedó huérfano).", "Cierra otros programas de git; si no hay ninguno: borra .git/index.lock"))
        return checks

    @staticmethod
    def _check_branch_vs_main() -> List[Check]:
        checks: List[Check] = []
        if not GitAuditService.ref_exists(REMOTE_MAIN):
            return [Check("Rama vs main", "WARN", f"No existe {REMOTE_MAIN} localmente.", "git fetch origin")]
        ahead, behind = GitAuditService.get_branch_vs_main()
        branch = GitAuditService.get_current_branch()
        if behind == 0:
            checks.append(Check("Rama vs main", "OK", f"'{branch}' contiene todo {REMOTE_MAIN} (+{ahead} propios)."))
        else:
            summary = GitAuditService.get_main_only_changes()
            parts = [f"{summary.counts.get(k, 0)} {label}" for k, label in (("A", "nuevos"), ("M", "modificados"), ("D", "eliminados")) if summary.counts.get(k)]
            extra = f" Trae: {', '.join(parts)}." if parts else ""
            if summary.deleted_dirs:
                extra += " Elimina: " + ", ".join(f"{n} de {d}" for d, n in summary.deleted_dirs) + "."
            checks.append(Check(
                "Rama vs main", "WARN",
                f"'{branch}' va {behind} commit(s) por detrás de {REMOTE_MAIN}.{extra}",
                "python resources/tools/git_manager.py update",
            ))

        upstream = GitAuditService.get_upstream()
        if not upstream:
            checks.append(Check("Upstream", "WARN", "La rama actual no tiene upstream configurado.", "git push -u origin <rama>"))
        else:
            u_ahead, u_behind = GitAuditService.ahead_behind("HEAD", upstream)
            if u_ahead or u_behind:
                checks.append(Check("Upstream", "WARN", f"Frente a {upstream}: {u_ahead} sin subir, {u_behind} sin bajar.", "git push / git pull --ff-only"))
            else:
                checks.append(Check("Upstream", "OK", f"Sincronizada con {upstream}."))
        return checks

    @staticmethod
    def _check_repo_hygiene() -> List[Check]:
        checks: List[Check] = []
        root_p = Path(PROJECT_ROOT)
        if (root_p / ".gitattributes").is_file():
            checks.append(Check("Saltos de línea", "OK", ".gitattributes presente."))
        else:
            checks.append(Check(
                "Saltos de línea", "WARN",
                "Sin .gitattributes: en Windows los archivos pueden quedar en CRLF y 'git apply' de parches LF falla.",
                "Añade '* text=auto' en .gitattributes (o usa: git apply --ignore-whitespace).",
            ))

        for target_path in TEST_DIRS:
            target_p = root_p / target_path if not Path(target_path).is_absolute() else Path(target_path)
            if target_p.is_dir():
                try:
                    rel_str = target_p.relative_to(root_p).as_posix()
                except ValueError:
                    rel_str = target_p.as_posix()
                code, _, _ = GitRunner.run(["check-ignore", "-q", rel_str])
                if code == 0:
                    checks.append(Check("Tests en Git", "FAIL", f"'{rel_str}' está ignorado por .gitignore: tus tests no se versionan.", "Quita esa línea de .gitignore."))
                else:
                    checks.append(Check("Tests en Git", "OK", f"'{rel_str}' se versiona."))
        return checks

    @staticmethod
    def _check_version_branch() -> Check:
        branch = GitAuditService.get_current_branch()
        expected = f"release/{VersionManager.get_version()}"
        if branch.startswith("release/") and branch != expected:
            return Check("Versión vs rama", "WARN", f"Estás en {branch} pero version.py indica {expected}.", "Alinea la versión o cambia de rama.")
        return Check("Versión vs rama", "OK", f"{branch} / {VersionManager.get_version()}")

    @staticmethod
    def run_checks(fetch: bool = True) -> List[Check]:
        if fetch:
            GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        checks: List[Check] = [DoctorService._check_interpreter(), DoctorService._check_pyside(), DoctorService._check_api_keys()]
        checks.extend(DoctorService._check_operation())
        checks.append(DoctorService._check_version_branch())
        checks.extend(DoctorService._check_branch_vs_main())
        checks.extend(DoctorService._check_repo_hygiene())
        return checks


class TestRunner:
    __test__ = False

    @staticmethod
    def targets() -> List[Path]:
        root_p = Path(PROJECT_ROOT)
        return [root_p / d if not Path(d).is_absolute() else Path(d) for d in TEST_DIRS if (root_p / d).is_dir() or Path(d).is_dir()]

    @staticmethod
    def run() -> Optional[bool]:
        dirs = TestRunner.targets()
        if not dirs:
            return None
        python = DoctorService.project_python()
        try:
            has_pytest = subprocess.run([python, "-c", "import pytest"], capture_output=True, timeout=60).returncode == 0
        except Exception:
            has_pytest = False

        root_p = Path(PROJECT_ROOT)
        dir_strs = []
        for d in dirs:
            try:
                dir_strs.append(d.relative_to(root_p).as_posix())
            except ValueError:
                dir_strs.append(d.as_posix())

        if has_pytest:
            cmd = [python, "-m", "pytest", *dir_strs, "-q"]
        else:
            modules = []
            for folder in dirs:
                try:
                    rel_p = folder.relative_to(root_p).as_posix()
                except ValueError:
                    rel_p = folder.as_posix()
                prefix = rel_p.replace("/", ".")
                modules.extend(f"{prefix}.{f.stem}" for f in sorted(folder.glob("test_*.py")))
            if not modules:
                return None
            cmd = [python, "-m", "unittest", *modules]

        print(f"  {Colors.DIM}→ {' '.join(cmd)}{Colors.RESET}")
        return subprocess.run(cmd, cwd=root_p).returncode == 0


STATUS_ICON = {"OK": "✅", "WARN": "⚠️ ", "FAIL": "❌"}


class GitReleaseWorkflow:
    @staticmethod
    def _banner(title: str) -> None:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 64}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title.center(64)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 64}{Colors.RESET}\n")

    @staticmethod
    def doctor(as_json: bool = False) -> bool:
        checks = DoctorService.run_checks()
        ok = not any(c.status == "FAIL" for c in checks)
        if as_json:
            print(json.dumps({"ok": ok, "checks": [asdict(c) for c in checks]}, indent=2, ensure_ascii=False))
            return ok

        GitReleaseWorkflow._banner("MINIKICK - DOCTOR (ENTORNO Y REPOSITORIO)")
        for c in checks:
            color = {"OK": Colors.GREEN, "WARN": Colors.YELLOW, "FAIL": Colors.RED}[c.status]
            print(f"  {STATUS_ICON[c.status]} {Colors.BOLD}{c.name}:{Colors.RESET} {color}{c.detail}{Colors.RESET}")
            if c.fix and c.status != "OK":
                print(f"     {Colors.DIM}💡 {c.fix}{Colors.RESET}")
        fails = sum(c.status == "FAIL" for c in checks)
        warns = sum(c.status == "WARN" for c in checks)
        print(f"\n  Resumen: {len(checks) - fails - warns} OK · {warns} avisos · {fails} errores\n")
        return ok

    @staticmethod
    def audit() -> None:
        GitReleaseWorkflow._banner("MINIKICK - AUDITORÍA DE GIT & REPOSITORIO")

        curr_branch = GitAuditService.get_current_branch()
        config_version = VersionManager.get_version()
        expected_branch = f"release/{config_version}"

        print(f"  {Colors.BOLD}Configuración de Versión:{Colors.RESET} {Colors.GREEN}{config_version}{Colors.RESET}")
        print(f"  {Colors.BOLD}Rama Actual (HEAD):{Colors.RESET}       {Colors.YELLOW}{curr_branch}{Colors.RESET}")

        if curr_branch.startswith("release/") and curr_branch != expected_branch:
            print(f"  {Colors.RED}⚠️  Advertencia:{Colors.RESET} Estás en {curr_branch}, pero la versión configurada es {config_version} ({expected_branch}).")
        elif curr_branch == expected_branch:
            print(f"  {Colors.GREEN}✅ Coherencia:{Colors.RESET} La rama activa coincide exactamente con la versión del software.")

        op = GitAuditService.in_progress_operation()
        if op:
            print(f"  {Colors.BOLD}Operación en curso:{Colors.RESET}       {Colors.RED}{op} sin terminar{Colors.RESET}  {Colors.DIM}(ejecuta 'doctor' para ver cómo resolverlo){Colors.RESET}")

        is_clean, dirty_files = GitAuditService.is_working_tree_clean()
        if is_clean:
            print(f"  {Colors.BOLD}Estado de Archivos:{Colors.RESET}       {Colors.GREEN}Limpio (sin cambios pendientes){Colors.RESET}")
        else:
            print(f"  {Colors.BOLD}Estado de Archivos:{Colors.RESET}       {Colors.YELLOW}{len(dirty_files)} archivos con cambios sin commitear{Colors.RESET}")
            for f in dirty_files[:5]:
                print(f"    {Colors.DIM}• {f}{Colors.RESET}")
            if len(dirty_files) > 5:
                print(f"    {Colors.DIM}... y {len(dirty_files) - 5} más{Colors.RESET}")

        GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        ahead, behind = GitAuditService.get_main_divergence()
        if behind > 0:
            print(f"  {Colors.BOLD}Sincronización 'main':{Colors.RESET}    {Colors.RED}Desactualizado ({behind} commits por detrás de origin/main){Colors.RESET}")
            print(f"    {Colors.YELLOW}💡 Sugerencia:{Colors.RESET} Ejecuta la opción 'Sincronizar' para actualizar main.")
        elif ahead > 0:
            print(f"  {Colors.BOLD}Sincronización 'main':{Colors.RESET}    {Colors.BLUE}Tienes {ahead} commits pendientes de subir a origin/main{Colors.RESET}")
        else:
            print(f"  {Colors.BOLD}Sincronización 'main':{Colors.RESET}    {Colors.GREEN}Al día con origin/main{Colors.RESET}")

        if curr_branch != MAIN_BRANCH:
            b_ahead, b_behind = GitAuditService.get_branch_vs_main()
            if b_behind > 0:
                print(f"  {Colors.BOLD}Rama actual vs main:{Colors.RESET}      {Colors.RED}{b_behind} commit(s) de origin/main que tu rama NO tiene{Colors.RESET}  {Colors.DIM}(+{b_ahead} propios){Colors.RESET}")
                print(f"    {Colors.YELLOW}💡 Sugerencia:{Colors.RESET} python resources/tools/git_manager.py update")
            else:
                print(f"  {Colors.BOLD}Rama actual vs main:{Colors.RESET}      {Colors.GREEN}Contiene todo origin/main (+{b_ahead} propios){Colors.RESET}")

        local_merged, remote_merged = GitAuditService.get_merged_release_branches()
        total_stale = len(local_merged) + len(remote_merged)
        if total_stale > 0:
            print(f"  {Colors.BOLD}Ramas Obsoletas:{Colors.RESET}          {Colors.YELLOW}{total_stale} rama(s) ya fusionadas en main detectadas:{Colors.RESET}")
            for b in local_merged:
                print(f"    {Colors.DIM}• [Local]  {b}{Colors.RESET}")
            for b in remote_merged:
                print(f"    {Colors.DIM}• [Remota] origin/{b}{Colors.RESET}")
            print(f"    {Colors.YELLOW}💡 Sugerencia:{Colors.RESET} Ejecuta la opción 'Limpiar ramas' para eliminarlas de forma segura.")
        else:
            print(f"  {Colors.BOLD}Ramas Obsoletas:{Colors.RESET}          {Colors.GREEN}Ninguna (árbol ordenado y limpio){Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'─' * 64}{Colors.RESET}\n")

    @staticmethod
    def sync() -> None:
        print(f"\n{Colors.BLUE}🔄 Sincronizando repositorio con GitHub...{Colors.RESET}")

        print(f"  {Colors.DIM}→ Ejecutando fetch y podando referencias remotas...{Colors.RESET}")
        code, _, err = GitRunner.run(["fetch", "--all", "--tags", "--prune"])
        if code != 0:
            print(f"  {Colors.RED}❌ Falló el fetch: {err}{Colors.RESET}\n")
            return

        curr_branch = GitAuditService.get_current_branch()
        print(f"  {Colors.DIM}→ Verificando rama 'main'...{Colors.RESET}")

        if curr_branch == MAIN_BRANCH:
            code, _, err = GitRunner.run(["pull", "--ff-only", DEFAULT_REMOTE, MAIN_BRANCH])
            if code == 0:
                print(f"  {Colors.GREEN}✅ 'main' actualizado con éxito.{Colors.RESET}")
            else:
                print(f"  {Colors.RED}❌ No se pudo avanzar 'main' (¿divergió de origin/main?): {err}{Colors.RESET}")
        else:
            code, _, err = GitRunner.run(["fetch", DEFAULT_REMOTE, f"{MAIN_BRANCH}:{MAIN_BRANCH}"])
            if code == 0:
                print(f"  {Colors.GREEN}✅ 'main' sincronizado con origin/main en segundo plano.{Colors.RESET}")
            else:
                print(f"  {Colors.YELLOW}ℹ️  No se pudo avanzar 'main' sin cambiarte de rama ({err}).{Colors.RESET}")

        if curr_branch != MAIN_BRANCH:
            _, b_behind = GitAuditService.get_branch_vs_main()
            if b_behind > 0:
                print(f"  {Colors.YELLOW}⚠️  Tu rama '{curr_branch}' va {b_behind} commit(s) por detrás de origin/main. Usa 'update'.{Colors.RESET}")

        print(f"\n{Colors.GREEN}🎉 Sincronización completada.{Colors.RESET}\n")

    @staticmethod
    def update_from_main(assume_yes: bool = False) -> bool:
        curr_branch = GitAuditService.get_current_branch()
        print(f"\n{Colors.BLUE}⬇️  Actualizando '{curr_branch}' con {REMOTE_MAIN}...{Colors.RESET}")

        op = GitAuditService.in_progress_operation()
        if op:
            print(f"  {Colors.RED}❌ Hay un {op} sin terminar. Ejecuta 'doctor' para ver cómo resolverlo.{Colors.RESET}\n")
            return False

        changes = GitAuditService.tracked_changes()
        if changes:
            print(f"  {Colors.RED}❌ Tienes {len(changes)} archivo(s) con cambios sin commitear. Haz commit o stash antes.{Colors.RESET}")
            for f in changes[:5]:
                print(f"    {Colors.DIM}• {f}{Colors.RESET}")
            print()
            return False

        code, _, err = GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        if code != 0:
            print(f"  {Colors.RED}❌ Falló el fetch: {err}{Colors.RESET}\n")
            return False

        if not GitAuditService.ref_exists(REMOTE_MAIN):
            print(f"  {Colors.RED}❌ No existe {REMOTE_MAIN}.{Colors.RESET}\n")
            return False

        ahead, behind = GitAuditService.get_branch_vs_main()
        if behind == 0:
            print(f"  {Colors.GREEN}✅ Ya contienes todo {REMOTE_MAIN}. Nada que hacer.{Colors.RESET}\n")
            return True

        summary = GitAuditService.get_main_only_changes()
        counts = summary.counts
        print(f"  {behind} commit(s) nuevos en {REMOTE_MAIN}: "
              f"{counts.get('A', 0)} archivos nuevos, {counts.get('M', 0)} modificados, {counts.get('D', 0)} eliminados.")
        for folder, n in summary.deleted_dirs:
            print(f"  {Colors.YELLOW}⚠️  Se eliminarán {n} archivo(s) de {folder}{Colors.RESET}")

        if not confirm("¿Continuar con el merge?", assume_yes):
            print("  Operación cancelada.\n")
            return False

        cmd = ["merge", "--ff-only" if curr_branch == MAIN_BRANCH else "--no-edit", REMOTE_MAIN]
        code, _, err = GitRunner.run(cmd)
        if code == 0:
            _, new_behind = GitAuditService.get_branch_vs_main()
            print(f"  {Colors.GREEN}✅ Merge completado. Te faltan {new_behind} commit(s) de {REMOTE_MAIN}.{Colors.RESET}\n")
            return True

        return GitReleaseWorkflow._recover_merge(curr_branch, err)

    @staticmethod
    def _recover_merge(branch: str, err: str) -> bool:
        conflicts = GitAuditService.unmerged_files()
        if conflicts:
            print(f"  {Colors.RED}❌ Conflictos en {len(conflicts)} archivo(s):{Colors.RESET}")
            for f in conflicts:
                print(f"    {Colors.DIM}• {f}{Colors.RESET}")
            print("  Resuélvelos, luego: git add <archivos> && git commit -m \"Merge origin/main\"")
            print("  O cancela todo con: git merge --abort\n")
            return False

        if GitAuditService.in_progress_operation() == "merge":
            msg = f"Merge remote-tracking branch '{REMOTE_MAIN}' into {branch}"
            code, _, commit_err = GitRunner.run(["commit", "-m", msg])
            if code == 0:
                print(f"  {Colors.GREEN}✅ El merge estaba preparado; se confirmó con un mensaje explícito.{Colors.RESET}\n")
                return True
            print(f"  {Colors.RED}❌ No se pudo confirmar el merge: {commit_err}{Colors.RESET}\n")
            return False

        _, behind = GitAuditService.get_branch_vs_main()
        if behind == 0:
            print(f"  {Colors.YELLOW}ℹ️  Git reportó un error ({err}), pero el merge ya se había completado: HEAD contiene {REMOTE_MAIN}.{Colors.RESET}\n")
            return True

        print(f"  {Colors.RED}❌ El merge falló: {err}{Colors.RESET}\n")
        return False

    @staticmethod
    def start_release(target_version: Optional[str] = None) -> None:
        op = GitAuditService.in_progress_operation()
        if op:
            print(f"\n{Colors.RED}❌ Hay un {op} sin terminar. Resuélvelo antes de iniciar una versión.{Colors.RESET}")
            return

        changes = GitAuditService.tracked_changes()
        if changes:
            print(f"\n{Colors.RED}❌ Error: Tienes cambios sin commitear en archivos versionados.{Colors.RESET}")
            print("Por favor, haz commit o stash de tus cambios antes de iniciar una nueva versión.")
            return

        current_ver = VersionManager.get_version()
        if not target_version:
            suggested_patch = VersionManager.bump_semver(current_ver, "patch")
            suggested_minor = VersionManager.bump_semver(current_ver, "minor")
            print(f"\nVersión actual: {Colors.BOLD}{current_ver}{Colors.RESET}")
            print(f"1) Siguiente Patch: {Colors.GREEN}{suggested_patch}{Colors.RESET}")
            print(f"2) Siguiente Minor: {Colors.CYAN}{suggested_minor}{Colors.RESET}")
            print("3) Escribir versión personalizada")
            opt = input(f"\nElige una opción (1-3) [{suggested_patch}]: ").strip()

            if opt == "2":
                target_version = suggested_minor
            elif opt == "3":
                custom = input("Escribe la nueva versión (ej. v1.7.0): ").strip()
                target_version = custom if custom.startswith("v") else f"v{custom}"
            else:
                target_version = suggested_patch

        branch_name = f"release/{target_version}"
        print(f"\n{Colors.BLUE}🚀 Preparando rama de versión: {Colors.BOLD}{branch_name}{Colors.RESET}...")

        print(f"  {Colors.DIM}→ Trayendo los últimos cambios de {DEFAULT_REMOTE}...{Colors.RESET}")
        code, _, err = GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        if code != 0 or not GitAuditService.ref_exists(REMOTE_MAIN):
            print(f"  {Colors.RED}❌ No se pudo actualizar {REMOTE_MAIN}: {err or 'referencia inexistente'}{Colors.RESET}")
            return

        if GitAuditService.ref_exists(f"refs/heads/{branch_name}") or GitAuditService.ref_exists(f"refs/remotes/{DEFAULT_REMOTE}/{branch_name}"):
            print(f"  {Colors.YELLOW}⚠️  La rama '{branch_name}' ya existe (local o remota). No se vuelve a crear.{Colors.RESET}")
            print(f"     Cámbiate a ella con: git checkout {branch_name}   y revisa 'doctor'.")
            return

        print(f"  {Colors.DIM}→ Creando rama '{branch_name}' a partir de {REMOTE_MAIN}...{Colors.RESET}")
        code, _, err = GitRunner.run(["checkout", "-b", branch_name, "--no-track", REMOTE_MAIN])
        if code != 0:
            print(f"  {Colors.RED}❌ No se pudo crear la rama: {err}{Colors.RESET}")
            return

        print(f"  {Colors.DIM}→ Actualizando backend/config/version.py a {target_version}...{Colors.RESET}")
        if VersionManager.set_version(target_version):
            GitRunner.run(["add", "backend/config/version.py"])
            code, _, err = GitRunner.run(["commit", "-m", f"chore(release): bump version to {target_version}"])
            if code != 0:
                print(f"  {Colors.RED}❌ No se pudo confirmar el cambio de versión: {err}{Colors.RESET}")
                return
        else:
            print(f"  {Colors.DIM}   (version.py ya indicaba {target_version}; no hay commit de versión){Colors.RESET}")

        print(f"  {Colors.DIM}→ Publicando rama en GitHub...{Colors.RESET}")
        code, _, err = GitRunner.run(["push", "-u", DEFAULT_REMOTE, branch_name])
        if code != 0:
            print(f"  {Colors.YELLOW}⚠️  La rama '{branch_name}' se creó localmente, pero NO se publicó: {err}{Colors.RESET}")
            return

        print(f"\n{Colors.GREEN}✅ Rama '{branch_name}' creada y publicada con éxito.{Colors.RESET}")
        print(f"Ahora puedes desarrollar las novedades de la versión {target_version} aquí.\n")

    @staticmethod
    def cleanup_merged(assume_yes: bool = False) -> None:
        local_merged, remote_merged = GitAuditService.get_merged_release_branches()
        protected = ", ".join(sorted(set(GitAuditService.protected_release_branches())))
        if not local_merged and not remote_merged:
            print(f"\n{Colors.GREEN}✅ No se encontraron ramas antiguas fusionadas para limpiar.{Colors.RESET}")
            print(f"{Colors.DIM}   (Protegidas: {protected}){Colors.RESET}\n")
            return

        print(f"\n{Colors.YELLOW}Se detectaron las siguientes ramas ya integradas a 'main':{Colors.RESET}")
        for b in local_merged:
            print(f"  • [Local]  {b}")
        for b in remote_merged:
            print(f"  • [Remota] origin/{b}")
        print(f"{Colors.DIM}  (Protegidas, no se tocan: {protected}){Colors.RESET}")

        if not confirm("\n¿Deseas eliminar estas ramas de forma segura?", assume_yes):
            print("\nOperación cancelada.\n")
            return

        for b in local_merged:
            c, _, err = GitRunner.run(["branch", "-D", b])
            print(f"  {Colors.GREEN}✓ Rama local eliminada: {b}{Colors.RESET}" if c == 0 else f"  {Colors.RED}✗ No se pudo eliminar {b}: {err}{Colors.RESET}")

        for b in remote_merged:
            c, _, err = GitRunner.run(["push", DEFAULT_REMOTE, "--delete", b])
            print(f"  {Colors.GREEN}✓ Rama remota eliminada: origin/{b}{Colors.RESET}" if c == 0 else f"  {Colors.RED}✗ No se pudo eliminar origin/{b}: {err}{Colors.RESET}")

        print(f"\n{Colors.GREEN}🎉 Limpieza finalizada.{Colors.RESET}\n")

    @staticmethod
    def finish_check(push: bool = True) -> bool:
        curr_branch = GitAuditService.get_current_branch()
        if not curr_branch.startswith("release/"):
            print(f"\n{Colors.YELLOW}⚠️  Aviso: La rama actual es '{curr_branch}', no parece una rama 'release/vX.Y.Z'.{Colors.RESET}")

        op = GitAuditService.in_progress_operation()
        if op:
            print(f"\n{Colors.RED}❌ Hay un {op} sin terminar. Resuélvelo antes de preparar el PR.{Colors.RESET}\n")
            return False

        GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        _, behind = GitAuditService.get_branch_vs_main()
        if behind > 0:
            print(f"\n{Colors.YELLOW}⚠️  Tu rama va {behind} commit(s) por detrás de {REMOTE_MAIN}: el PR podría tener conflictos."
                  f" Considera ejecutar 'update' primero.{Colors.RESET}")

        print(f"\n{Colors.BLUE}🧪 Ejecutando pruebas del proyecto...{Colors.RESET}")
        result = TestRunner.run()
        if result is None:
            root_p = Path(PROJECT_ROOT)
            dir_names = ", ".join((root_p / d).relative_to(root_p).as_posix() if (root_p / d).is_relative_to(root_p) else str(d) for d in TEST_DIRS)
            print(f"  {Colors.YELLOW}⚠️  No se encontró carpeta de tests ({dir_names}); se omite este paso.{Colors.RESET}")
        elif not result:
            print(f"\n{Colors.RED}❌ Las pruebas no pasaron. Revisa los errores antes de crear el Pull Request.{Colors.RESET}\n")
            return False
        else:
            print(f"\n{Colors.GREEN}✅ Todas las pruebas pasaron satisfactoriamente.{Colors.RESET}")

        if push:
            print(f"  {Colors.DIM}→ Asegurando que los últimos commits estén en GitHub...{Colors.RESET}")
            code, _, err = GitRunner.run(["push", DEFAULT_REMOTE, curr_branch])
            if code != 0:
                print(f"  {Colors.RED}❌ El push falló: {err}{Colors.RESET}\n")
                return False

        pr_url = f"{GITHUB_REPO_URL}/compare/{MAIN_BRANCH}...{curr_branch}?expand=1"
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 64}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}       ¡TODO LISTO PARA CREAR EL PULL REQUEST A MAIN!           {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 64}{Colors.RESET}")
        print("\nAbre este enlace en tu navegador para crear y fusionar el PR:")
        print(f"{Colors.BOLD}{Colors.YELLOW}{pr_url}{Colors.RESET}\n")
        print("Recomendación al fusionar en GitHub:")
        print("  1. Haz clic en 'Merge pull request'.")
        print("  2. Si la versión está terminada, marca 'Delete branch'; si seguirás trabajando en ella, NO la borres.")
        print("  3. Crea el Tag de la versión en GitHub Releases.\n")
        return True


def interactive_menu() -> None:
    if not sys.stdin.isatty():
        print(f"{Colors.YELLOW}[Modo No-Interactivo detectado] Ejecutando diagnóstico de Git...{Colors.RESET}")
        GitReleaseWorkflow.doctor()
        return

    while True:
        curr_branch = GitAuditService.get_current_branch()
        version = VersionManager.get_version()

        print(f"\n{Colors.BOLD}{Colors.MAGENTA}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}║               MINIKICK - GIT RELEASE MANAGER                 ║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print(f" Rama: {Colors.YELLOW}{curr_branch}{Colors.RESET} | Versión: {Colors.GREEN}{version}{Colors.RESET}\n")
        print(f"  {Colors.BOLD}1){Colors.RESET} 🔍 Auditar estado del repositorio y ramas")
        print(f"  {Colors.BOLD}2){Colors.RESET} 🚀 Iniciar nueva versión / release")
        print(f"  {Colors.BOLD}3){Colors.RESET} 🔄 Sincronizar 'main' y podar ramas remotas")
        print(f"  {Colors.BOLD}4){Colors.RESET} 🧹 Limpiar ramas antiguas ya fusionadas")
        print(f"  {Colors.BOLD}5){Colors.RESET} 🧪 Verificar tests y preparar Pull Request")
        print(f"  {Colors.BOLD}6){Colors.RESET} 🩺 Doctor (entorno, merge, ramas, .gitignore)")
        print(f"  {Colors.BOLD}7){Colors.RESET} ⬇️  Traer origin/main a esta rama (update)")
        print(f"  {Colors.BOLD}0){Colors.RESET} 🚪 Salir")

        try:
            choice = input(f"\n{Colors.BOLD}Selecciona una opción [1-7, 0]:{Colors.RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break

        if choice == "1":
            GitReleaseWorkflow.audit()
        elif choice == "2":
            GitReleaseWorkflow.start_release()
        elif choice == "3":
            GitReleaseWorkflow.sync()
        elif choice == "4":
            GitReleaseWorkflow.cleanup_merged()
        elif choice == "5":
            GitReleaseWorkflow.finish_check()
        elif choice == "6":
            GitReleaseWorkflow.doctor()
        elif choice == "7":
            GitReleaseWorkflow.update_from_main()
        elif choice in ("0", "q", "exit"):
            print(f"\n{Colors.DIM}¡Hasta luego!{Colors.RESET}\n")
            break
        else:
            print(f"{Colors.RED}Opción no válida.{Colors.RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MiniKick Git Release & Branch Manager")
    parser.add_argument("command", nargs="?", choices=["audit", "doctor", "update", "sync", "start", "cleanup", "check"],
                        help="Comando a ejecutar. Si se omite, abre el menú interactivo.")
    parser.add_argument("--version", "-v", dest="target_version", help="Versión objetivo para 'start' (ej. v1.7.0)")
    parser.add_argument("--no-push", action="store_true", help="Para el comando 'check', omite hacer git push")
    parser.add_argument("--yes", "-y", action="store_true", help="No pedir confirmación (update, cleanup)")
    parser.add_argument("--json", action="store_true", help="Exportar diagnóstico en formato JSON")

    args = parser.parse_args()

    if args.command == "doctor":
        sys.exit(0 if GitReleaseWorkflow.doctor(as_json=args.json) else 1)

    if args.json:
        data = {
            "current_branch": GitAuditService.get_current_branch(),
            "version": VersionManager.get_version(),
            "is_working_tree_clean": GitAuditService.is_working_tree_clean()[0],
            "uncommitted_files": GitAuditService.is_working_tree_clean()[1],
            "in_progress_operation": GitAuditService.in_progress_operation(),
            "upstream": GitAuditService.get_upstream(),
            "main_divergence": dict(zip(["ahead", "behind"], GitAuditService.get_main_divergence())),
            "branch_vs_main": dict(zip(["ahead", "behind"], GitAuditService.get_branch_vs_main())),
            "merged_branches": dict(zip(["local", "remote"], GitAuditService.get_merged_release_branches())),
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not args.command:
        interactive_menu()
    elif args.command == "audit":
        GitReleaseWorkflow.audit()
    elif args.command == "update":
        sys.exit(0 if GitReleaseWorkflow.update_from_main(assume_yes=args.yes) else 1)
    elif args.command == "sync":
        GitReleaseWorkflow.sync()
    elif args.command == "start":
        GitReleaseWorkflow.start_release(args.target_version)
    elif args.command == "cleanup":
        GitReleaseWorkflow.cleanup_merged(assume_yes=args.yes)
    elif args.command == "check":
        sys.exit(0 if GitReleaseWorkflow.finish_check(push=not args.no_push) else 1)


if __name__ == "__main__":
    main()
