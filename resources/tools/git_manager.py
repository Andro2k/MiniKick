# resources\tools\git_manager.py\

import questionary
import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

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

class CLI:
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
    def banner(cls, title: str) -> None:
        width = 64
        print(f"\n{cls.BOLD}{cls.CYAN}╭{'─' * (width - 2)}╮{cls.RESET}")
        print(f"{cls.BOLD}{cls.CYAN}│{title.center(width - 2)}│{cls.RESET}")
        print(f"{cls.BOLD}{cls.CYAN}╰{'─' * (width - 2)}╯{cls.RESET}\n")

    @classmethod
    def ok(cls, msg: str) -> None:
        print(f"  {cls.GREEN}✓{cls.RESET} {msg}")

    @classmethod
    def err(cls, msg: str) -> None:
        print(f"  {cls.RED}✗{cls.RESET} {msg}")

    @classmethod
    def warn(cls, msg: str) -> None:
        print(f"  {cls.YELLOW}!{cls.RESET} {msg}")

    @classmethod
    def info(cls, msg: str) -> None:
        print(f"  {cls.BLUE}ℹ{cls.RESET} {msg}")

    @classmethod
    def step(cls, msg: str) -> None:
        print(f"  {cls.DIM}❯ {msg}{cls.RESET}")

    @classmethod
    def list_item(cls, msg: str, indent: int = 1) -> None:
        space = "    " * indent
        print(f"{space}{cls.DIM}├─ {msg}{cls.RESET}")

    @classmethod
    def confirm(cls, prompt: str, assume_yes: bool = False) -> bool:
        if assume_yes:
            return True
        if not sys.stdin.isatty():
            cls.warn("(Modo no interactivo: añade --yes para confirmar)")
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


class GitAuditService:
    @staticmethod
    def get_current_branch() -> str:
        code, out, _ = GitRunner.run(["rev-parse", "--abbrev-ref", "HEAD"])
        return out if code == 0 else "unknown"
        
    @staticmethod
    def get_local_branches() -> List[str]:
        code, out, _ = GitRunner.run(["branch", "--format=%(refname:short)"])
        if code != 0 or not out:
            return []
        return [b.strip() for b in out.splitlines() if b.strip()]

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
    def protected_release_branches() -> Set[str]:
        return {GitAuditService.get_current_branch(), f"release/{VersionManager.get_version()}"}

    @staticmethod
    def get_merged_release_branches() -> Tuple[List[str], List[str]]:
        local_merged: List[str] = []
        remote_merged: List[str] = []
        protected = GitAuditService.protected_release_branches()

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
    def run_checks(fetch: bool = True) -> List[Check]:
        if fetch:
            GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        checks: List[Check] = [
            DoctorService._check_interpreter(), 
            DoctorService._check_pyside(), 
            DoctorService._check_api_keys()
        ]
        checks.extend(DoctorService._check_operation())
        checks.append(DoctorService._check_version_branch())
        checks.extend(DoctorService._check_branch_vs_main())
        checks.extend(DoctorService._check_repo_hygiene())
        return checks

    @staticmethod
    def _check_interpreter() -> Check:
        venv = DoctorService.venv_python()
        if not venv:
            return Check("Intérprete", "WARN", "No existe la carpeta .venv del proyecto.", "uv sync (o crea el entorno virtual)")
        root_p = Path(PROJECT_ROOT)
        venv_dir = (root_p / ".venv").resolve()
        prefix = Path(sys.prefix).resolve()
        if prefix == venv_dir or venv_dir in prefix.parents:
            return Check("Intérprete", "OK", f"Usando el entorno del proyecto ({sys.executable}).")
        return Check(
            "Intérprete", "WARN",
            f"Estás usando {sys.executable}, no el .venv.",
            r"Activa el entorno: .\.venv\Scripts\Activate.ps1"
        )

    @staticmethod
    def _check_pyside() -> Check:
        python = DoctorService.project_python()
        try:
            ok = subprocess.run([python, "-c", "import PySide6"], capture_output=True, timeout=60).returncode == 0
        except Exception:
            ok = False
        return Check("PySide6", "OK", "Importable correctamente.") if ok else Check("PySide6", "FAIL", "Falla importación.", "uv sync")

    @staticmethod
    def _check_api_keys() -> Check:
        path = Path(PROJECT_ROOT) / "backend" / "config" / "api_keys.py"
        return Check("api_keys.py", "OK", "Presente.") if path.is_file() else Check("api_keys.py", "WARN", "No existe.", "Crea el archivo.")

    @staticmethod
    def _check_operation() -> List[Check]:
        checks: List[Check] = []
        op = GitAuditService.in_progress_operation()
        if op == "merge":
            conflicts = GitAuditService.unmerged_files()
            detail = f"Merge a medias ({len(conflicts)} en conflicto)." if conflicts else "Merge a medias, sin conflictos."
            fix = "Resuelve y git commit" if conflicts else "git commit -m 'Merge'"
            checks.append(Check("Operación en curso", "FAIL", detail, fix))
        elif op:
            checks.append(Check("Operación en curso", "FAIL", f"{op} a medias.", f"git {op} --abort"))
        else:
            checks.append(Check("Operación en curso", "OK", "Sin operaciones pendientes."))

        if GitAuditService.has_index_lock():
            checks.append(Check("index.lock", "WARN", "Existe .git/index.lock", "Cierra otros programas o borra el archivo"))
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
                
            checks.append(Check("Rama vs main", "WARN", f"'{branch}' va {behind} por detrás de {REMOTE_MAIN}.{extra}", "git_manager.py update"))

        upstream = GitAuditService.get_upstream()
        if not upstream:
            checks.append(Check("Upstream", "WARN", "Sin upstream configurado.", "git push -u origin <rama>"))
        else:
            u_ahead, u_behind = GitAuditService.ahead_behind("HEAD", upstream)
            if u_ahead or u_behind:
                checks.append(Check("Upstream", "WARN", f"{u_ahead} sin subir, {u_behind} sin bajar.", "git push / pull"))
            else:
                checks.append(Check("Upstream", "OK", f"Sincronizada con {upstream}."))
        return checks

    @staticmethod
    def _check_repo_hygiene() -> List[Check]:
        checks: List[Check] = []
        root_p = Path(PROJECT_ROOT)
        checks.append(Check("Saltos de línea", "OK", ".gitattributes presente.") if (root_p / ".gitattributes").is_file() else Check("Saltos de línea", "WARN", "Falta .gitattributes.", "Añade '* text=auto'"))

        for target_path in TEST_DIRS:
            target_p = root_p / target_path if not Path(target_path).is_absolute() else Path(target_path)
            if target_p.is_dir():
                try:
                    rel_str = target_p.relative_to(root_p).as_posix()
                except ValueError:
                    rel_str = target_p.as_posix()
                code, _, _ = GitRunner.run(["check-ignore", "-q", rel_str])
                checks.append(Check("Tests en Git", "FAIL", f"Ignorado en .gitignore: {rel_str}", "Quita la línea") if code == 0 else Check("Tests en Git", "OK", f"'{rel_str}' se versiona."))
        return checks

    @staticmethod
    def _check_version_branch() -> Check:
        branch = GitAuditService.get_current_branch()
        expected = f"release/{VersionManager.get_version()}"
        if branch.startswith("release/") and branch != expected:
            return Check("Versión vs rama", "WARN", f"En {branch} pero version indica {expected}.", "Alinea la versión.")
        return Check("Versión vs rama", "OK", f"{branch} / {VersionManager.get_version()}")


class TestRunner:
    @staticmethod
    def run() -> Optional[bool]:
        root_p = Path(PROJECT_ROOT)
        dirs = [root_p / d if not Path(d).is_absolute() else Path(d) for d in TEST_DIRS if (root_p / d).is_dir() or Path(d).is_dir()]
        if not dirs:
            return None
        python = DoctorService.project_python()
        has_pytest = subprocess.run([python, "-c", "import pytest"], capture_output=True, timeout=60).returncode == 0
        dir_strs = [d.relative_to(root_p).as_posix() if d.is_relative_to(root_p) else d.as_posix() for d in dirs]

        if has_pytest:
            cmd = [python, "-m", "pytest", *dir_strs, "-q"]
        else:
            modules = [f"{d.relative_to(root_p).as_posix().replace('/', '.')}.{f.stem}" for d in dirs for f in sorted(d.glob("test_*.py")) if d.is_relative_to(root_p)]
            if not modules: return None
            cmd = [python, "-m", "unittest", *modules]

        CLI.step(f"{' '.join(cmd)}")
        return subprocess.run(cmd, cwd=root_p).returncode == 0

class GitReleaseWorkflow:
    @staticmethod
    def switch_branch() -> None:
        CLI.banner("CAMBIAR DE RAMA")
        branches = GitAuditService.get_local_branches()
        curr_branch = GitAuditService.get_current_branch()
        
        if not branches:
            CLI.err("No se encontraron ramas locales.")
            return

        print(f"  {CLI.BOLD}Ramas disponibles:{CLI.RESET}")
        for idx, b in enumerate(branches, 1):
            marker = f"{CLI.CYAN}★{CLI.RESET}" if b == curr_branch else " "
            print(f"    {marker} {CLI.BOLD}{idx}){CLI.RESET} {b}")

        try:
            choice = input(f"\n  {CLI.BOLD}Selecciona el número de la rama (0 para cancelar):{CLI.RESET} ").strip()
            if not choice or choice == "0":
                return
            
            idx = int(choice) - 1
            if 0 <= idx < len(branches):
                target = branches[idx]
                if target == curr_branch:
                    CLI.info("Ya estás en esta rama.")
                    return
                
                is_clean, _ = GitAuditService.is_working_tree_clean()
                if not is_clean:
                    if not CLI.confirm("Tienes cambios sin commitear. Git podría transferirlos o bloquear el cambio. ¿Continuar?"):
                        return

                code, _, err = GitRunner.run(["checkout", target])
                if code == 0:
                    CLI.ok(f"Cambiado a la rama '{target}'")
                else:
                    CLI.err(f"No se pudo cambiar de rama:\n{err}")
            else:
                CLI.err("Selección inválida.")
        except ValueError:
            CLI.err("Entrada inválida.")

    @staticmethod
    def doctor(as_json: bool = False) -> bool:
        checks = DoctorService.run_checks()
        ok = not any(c.status == "FAIL" for c in checks)
        if as_json:
            print(json.dumps({"ok": ok, "checks": [asdict(c) for c in checks]}, indent=2, ensure_ascii=False))
            return ok

        CLI.banner("DOCTOR (ENTORNO Y REPOSITORIO)")
        status_icons = {"OK": f"{CLI.GREEN}✓{CLI.RESET}", "WARN": f"{CLI.YELLOW}!{CLI.RESET}", "FAIL": f"{CLI.RED}✗{CLI.RESET}"}
        
        for c in checks:
            color = {"OK": CLI.GREEN, "WARN": CLI.YELLOW, "FAIL": CLI.RED}[c.status]
            print(f"  {status_icons[c.status]} {CLI.BOLD}{c.name}:{CLI.RESET} {color}{c.detail}{CLI.RESET}")
            if c.fix and c.status != "OK":
                CLI.list_item(f"Solución: {c.fix}")
                
        fails, warns = sum(c.status == "FAIL" for c in checks), sum(c.status == "WARN" for c in checks)
        print(f"\n  {CLI.DIM}Resumen: {len(checks) - fails - warns} OK · {warns} Avisos · {fails} Errores{CLI.RESET}\n")
        return ok

    @staticmethod
    def audit() -> None:
        CLI.banner("AUDITORÍA DE GIT & REPOSITORIO")
        curr_branch = GitAuditService.get_current_branch()
        config_version = VersionManager.get_version()
        expected_branch = f"release/{config_version}"

        print(f"  {CLI.BOLD}Versión:{CLI.RESET} {CLI.CYAN}{config_version}{CLI.RESET} │ {CLI.BOLD}Rama (HEAD):{CLI.RESET} {CLI.CYAN}{curr_branch}{CLI.RESET}")

        if curr_branch.startswith("release/") and curr_branch != expected_branch:
            CLI.warn(f"Estás en {curr_branch}, pero la versión configurada es {config_version}.")
        elif curr_branch == expected_branch:
            CLI.ok("La rama activa coincide con la versión del software.")

        if op := GitAuditService.in_progress_operation():
            CLI.err(f"Operación '{op}' sin terminar. Ejecuta 'doctor'.")

        is_clean, dirty_files = GitAuditService.is_working_tree_clean()
        if is_clean:
            CLI.ok("Árbol de trabajo limpio.")
        else:
            CLI.warn(f"{len(dirty_files)} archivos con cambios sin commitear.")
            for f in dirty_files[:3]: CLI.list_item(f)
            if len(dirty_files) > 3: CLI.list_item(f"... y {len(dirty_files) - 3} más")

        GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        ahead, behind = GitAuditService.get_main_divergence()
        if behind > 0:
            CLI.err(f"Desactualizado ({behind} commits por detrás de origin/main). Usa 'Sync'.")
        elif ahead > 0:
            CLI.info(f"Tienes {ahead} commits pendientes de subir a origin/main.")
        else:
            CLI.ok("Al día con origin/main.")

        local_merged, remote_merged = GitAuditService.get_merged_release_branches()
        if total_stale := len(local_merged) + len(remote_merged):
            CLI.warn(f"{total_stale} rama(s) fusionadas detectadas. Ejecuta 'Limpiar ramas'.")
        else:
            CLI.ok("Sin ramas obsoletas pendientes de limpiar.")
        print()

    @staticmethod
    def sync() -> None:
        CLI.info("Sincronizando repositorio con GitHub...")
        CLI.step("Ejecutando fetch y podando referencias remotas...")
        if GitRunner.run(["fetch", "--all", "--tags", "--prune"])[0] != 0:
            return CLI.err("Falló el fetch.")

        curr_branch = GitAuditService.get_current_branch()
        CLI.step("Verificando rama 'main'...")

        if curr_branch == MAIN_BRANCH:
            code, _, err = GitRunner.run(["pull", "--ff-only", DEFAULT_REMOTE, MAIN_BRANCH])
            CLI.ok("'main' actualizado.") if code == 0 else CLI.err(f"No se pudo avanzar 'main': {err}")
        else:
            code, _, err = GitRunner.run(["fetch", DEFAULT_REMOTE, f"{MAIN_BRANCH}:{MAIN_BRANCH}"])
            CLI.ok("'main' sincronizado en segundo plano.") if code == 0 else CLI.warn(f"No se pudo avanzar 'main' directamente.")

        if curr_branch != MAIN_BRANCH and GitAuditService.get_branch_vs_main()[1] > 0:
            CLI.warn("Tu rama actual va por detrás de origin/main. Usa 'Update'.")
        print()

    @staticmethod
    def update_from_main(assume_yes: bool = False) -> bool:
        curr_branch = GitAuditService.get_current_branch()
        CLI.info(f"Actualizando '{curr_branch}' con {REMOTE_MAIN}...")

        if op := GitAuditService.in_progress_operation():
            CLI.err(f"Hay un {op} sin terminar. Resuélvelo primero."); return False

        if changes := GitAuditService.tracked_changes():
            CLI.err(f"Tienes {len(changes)} archivo(s) con cambios sin commitear."); return False

        GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])
        if GitAuditService.get_branch_vs_main()[1] == 0:
            CLI.ok(f"Ya contienes todo {REMOTE_MAIN}. Nada que hacer."); return True

        if not CLI.confirm("¿Continuar con el merge?", assume_yes):
            return False

        code, _, err = GitRunner.run(["merge", "--ff-only" if curr_branch == MAIN_BRANCH else "--no-edit", REMOTE_MAIN])
        if code == 0:
            CLI.ok(f"Merge completado. Te faltan {GitAuditService.get_branch_vs_main()[1]} commit(s) de {REMOTE_MAIN}.")
            return True

        return GitReleaseWorkflow._recover_merge(curr_branch, err)

    @staticmethod
    def _recover_merge(branch: str, err: str) -> bool:
        conflicts = GitAuditService.unmerged_files()
        if conflicts:
            CLI.err(f"Conflictos en {len(conflicts)} archivo(s):")
            for f in conflicts:
                CLI.list_item(f)
            CLI.info("Resuélvelos, luego: git add <archivos> && git commit")
            return False

        if GitAuditService.in_progress_operation() == "merge":
            msg = f"Merge remote-tracking branch '{REMOTE_MAIN}' into {branch}"
            code, _, commit_err = GitRunner.run(["commit", "-m", msg])
            if code == 0:
                CLI.ok("El merge estaba preparado; se confirmó con un mensaje explícito.")
                return True
            CLI.err(f"No se pudo confirmar el merge: {commit_err}")
            return False

        if GitAuditService.get_branch_vs_main()[1] == 0:
            CLI.warn(f"Git reportó un error, pero el merge ya se había completado: HEAD contiene {REMOTE_MAIN}.")
            return True

        CLI.err(f"El merge falló: {err}")
        return False

    @staticmethod
    def start_release(target_version: Optional[str] = None) -> None:
        if GitAuditService.in_progress_operation() or GitAuditService.tracked_changes():
            CLI.err("Asegúrate de no tener cambios sin commitear ni operaciones pendientes."); return

        current_ver = VersionManager.get_version()
        if not target_version:
            suggested_patch = VersionManager.bump_semver(current_ver, "patch")
            print(f"\n  Versión actual: {CLI.BOLD}{current_ver}{CLI.RESET}")
            print(f"  1) Patch: {CLI.CYAN}{suggested_patch}{CLI.RESET}")
            print(f"  2) Minor: {CLI.CYAN}{VersionManager.bump_semver(current_ver, 'minor')}{CLI.RESET}")
            print(f"  3) Personalizada")
            opt = input(f"\n  Elige opción [1]: ").strip()
            
            target_version = VersionManager.bump_semver(current_ver, 'minor') if opt == "2" else (
                input("  Nueva versión: ").strip() if opt == "3" else suggested_patch
            )
            target_version = target_version if target_version.startswith("v") else f"v{target_version}"

        branch_name = f"release/{target_version}"
        CLI.info(f"Preparando rama: {branch_name}")
        GitRunner.run(["fetch", DEFAULT_REMOTE, "--prune"])

        if GitAuditService.ref_exists(f"refs/heads/{branch_name}"):
            return CLI.warn("La rama ya existe. Cámbiate a ella usando 'Cambiar de rama'.")

        CLI.step("Creando rama...")
        if GitRunner.run(["checkout", "-b", branch_name, "--no-track", REMOTE_MAIN])[0] != 0:
            return CLI.err("No se pudo crear la rama.")

        CLI.step("Actualizando version.py...")
        if VersionManager.set_version(target_version):
            GitRunner.run(["add", "backend/config/version.py"])
            GitRunner.run(["commit", "-m", f"chore(release): bump version to {target_version}"])

        CLI.step("Publicando rama...")
        GitRunner.run(["push", "-u", DEFAULT_REMOTE, branch_name])
        CLI.ok(f"Rama '{branch_name}' lista.")

    @staticmethod
    def cleanup_merged(assume_yes: bool = False) -> None:
        local_merged, remote_merged = GitAuditService.get_merged_release_branches()
        if not local_merged and not remote_merged:
            return CLI.ok("No hay ramas fusionadas para limpiar.")

        CLI.info("Ramas detectadas listas para eliminar:")
        for b in local_merged: CLI.list_item(f"[Local]  {b}")
        for b in remote_merged: CLI.list_item(f"[Remota] origin/{b}")

        if not CLI.confirm("\n¿Eliminar estas ramas de forma segura?", assume_yes):
            return

        for b in local_merged:
            c, _, _ = GitRunner.run(["branch", "-D", b])
            CLI.ok(f"Rama local {b}") if c == 0 else CLI.err(f"Error {b}")
        for b in remote_merged:
            c, _, _ = GitRunner.run(["push", DEFAULT_REMOTE, "--delete", b])
            CLI.ok(f"Rama remota origin/{b}") if c == 0 else CLI.err(f"Error origin/{b}")

    @staticmethod
    def finish_check(push: bool = True) -> bool:
        curr_branch = GitAuditService.get_current_branch()
        if GitAuditService.in_progress_operation():
            CLI.err("Hay una operación sin terminar."); return False

        CLI.info("Ejecutando pruebas...")
        res = TestRunner.run()
        if res is False:
            CLI.err("Pruebas fallidas."); return False
        elif res is True:
            CLI.ok("Pruebas exitosas.")

        if push:
            CLI.step("Subiendo últimos commits...")
            if GitRunner.run(["push", DEFAULT_REMOTE, curr_branch])[0] != 0:
                CLI.err("El push falló."); return False

        CLI.banner("¡LISTO PARA EL PULL REQUEST!")
        print(f"  {CLI.BOLD}URL:{CLI.RESET} {CLI.BLUE}{GITHUB_REPO_URL}/compare/{MAIN_BRANCH}...{curr_branch}?expand=1{CLI.RESET}\n")
        return True


def interactive_menu() -> None:
    if not sys.stdin.isatty():
        return GitReleaseWorkflow.doctor()

    options_map = {
        "🔍 Auditar estado del repositorio y ramas": GitReleaseWorkflow.audit,
        "🔀 Cambiar de rama": GitReleaseWorkflow.switch_branch,
        "🚀 Iniciar nueva versión / release": GitReleaseWorkflow.start_release,
        "🔄 Sincronizar 'main' y GitHub": GitReleaseWorkflow.sync,
        "⬇️  Traer origin/main aquí (update)": GitReleaseWorkflow.update_from_main,
        "🧹 Limpiar ramas antiguas fusionadas": GitReleaseWorkflow.cleanup_merged,
        "🧪 Verificar tests y preparar PR": GitReleaseWorkflow.finish_check,
        "🩺 Doctor (diagnóstico de entorno)": GitReleaseWorkflow.doctor,
        "🚪 Salir": None
    }

    cli_style = questionary.Style([
        ('qmark', 'fg:cyan bold'),
        ('question', 'bold'),
        ('answer', 'fg:green bold'),
        ('pointer', 'fg:cyan bold'),
        ('highlighted', 'fg:cyan bold'),
        ('selected', 'fg:green'),        
    ])

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        curr = GitAuditService.get_current_branch()
        ver = VersionManager.get_version()
        
        CLI.banner("GIT RELEASE MANAGER")
        print(f"  {CLI.BOLD}Rama:{CLI.RESET} {CLI.CYAN}{curr}{CLI.RESET} │ {CLI.BOLD}Versión:{CLI.RESET} {CLI.CYAN}{ver}{CLI.RESET}\n")
        
        choice = questionary.select(
            "Selecciona una acción (usa las flechas ↑/↓ y presiona Enter):",
            choices=list(options_map.keys()),
            pointer="❯",
            use_indicator=True,
            style=cli_style
        ).ask()

        if choice == "🚪 Salir" or choice is None:
            print(f"\n  {CLI.DIM}¡Hasta luego!{CLI.RESET}\n")
            break
            
        print()
        action = options_map[choice]
        if action:
            action()
            
        input(f"\n  {CLI.DIM}Presiona Enter para continuar...{CLI.RESET}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Git Release Manager")
    parser.add_argument("command", nargs="?", choices=["audit", "doctor", "update", "sync", "start", "cleanup", "check", "switch"])
    parser.add_argument("--version", "-v", dest="target_version")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--yes", "-y", action="store_true")
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if not args.command: interactive_menu()
    elif args.command == "doctor": sys.exit(0 if GitReleaseWorkflow.doctor(as_json=args.json) else 1)
    elif args.command == "audit": GitReleaseWorkflow.audit()
    elif args.command == "switch": GitReleaseWorkflow.switch_branch()
    elif args.command == "update": sys.exit(0 if GitReleaseWorkflow.update_from_main(assume_yes=args.yes) else 1)
    elif args.command == "sync": GitReleaseWorkflow.sync()
    elif args.command == "start": GitReleaseWorkflow.start_release(args.target_version)
    elif args.command == "cleanup": GitReleaseWorkflow.cleanup_merged(assume_yes=args.yes)
    elif args.command == "check": sys.exit(0 if GitReleaseWorkflow.finish_check(push=not args.no_push) else 1)


if __name__ == "__main__":
    main()