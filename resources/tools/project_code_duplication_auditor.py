# resources/tools/project_code_duplication_auditor.py

import argparse
import ast
import contextlib
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]

COLOR_RESET   = "\033[0m"
COLOR_BOLD    = "\033[1m"
COLOR_GREEN   = "\033[92m"
COLOR_YELLOW  = "\033[93m"
COLOR_CYAN    = "\033[96m"
COLOR_MAGENTA = "\033[95m"
COLOR_GRAY    = "\033[90m"

IGNORED_DIRECTORIES = {
    ".venv", "venv", "__pycache__", ".git", ".pytest_cache",
    ".agents", "build", "dist", "walkthroughs", "locales",
    "scratch", "node_modules", "tools", "tests"
}


@dataclass(slots=True)
class CodeOccurrence:
    file_path: str
    start_line: int
    end_line: int
    function_name: str
    snippet: str

@dataclass(slots=True)
class DuplicateCloneCluster:
    hash_id: str
    statements_count: int
    occurrences: List[CodeOccurrence] = field(default_factory=list)

class ASTNormalizer(ast.NodeTransformer):
    def visit_Name(self, node: ast.Name):
        return ast.copy_location(ast.Name(id="_VAR_", ctx=node.ctx), node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str):
            return ast.copy_location(ast.Constant(value="_STR_"), node)
        if isinstance(node.value, (int, float)):
            return ast.copy_location(ast.Constant(value=0), node)
        return node

class DuplicationScanner:
    def __init__(self, min_statements: int = 5):
        self.min_statements = min_statements
        self.normalizer = ASTNormalizer()
        self.hash_to_occurrences: Dict[str, List[CodeOccurrence]] = defaultdict(list)
        self.scanned_files_count: int = 0
        self.total_functions_count: int = 0

    def _canonical_ast_hash(self, stmts: List[ast.stmt]) -> str:
        normalized = [self.normalizer.visit(ast.fix_missing_locations(stmt)) for stmt in stmts]
        dumped = "".join(ast.dump(s, include_attributes=False) for s in normalized)
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()[:16]

    def scan_file(self, full_path: Path):
        rel_path = full_path.relative_to(PROJECT_ROOT).as_posix()
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            tree = ast.parse(content, filename=str(full_path))
            self.scanned_files_count += 1
        except Exception:
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.total_functions_count += 1
                body = node.body
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                    body = body[1:]

                if len(body) < self.min_statements:
                    continue

                for i in range(len(body) - self.min_statements + 1):
                    window = body[i : i + self.min_statements]
                    if all(isinstance(s, (ast.Pass, ast.Return, ast.Expr)) for s in window):
                        continue

                    h = self._canonical_ast_hash(window)
                    start_l = window[0].lineno
                    end_l = getattr(window[-1], "end_lineno", window[-1].lineno)
                    snippet = "\n".join(lines[max(0, start_l - 1) : min(len(lines), end_l)][:8])

                    self.hash_to_occurrences[h].append(
                        CodeOccurrence(
                            file_path=rel_path,
                            start_line=start_l,
                            end_line=end_l,
                            function_name=node.name,
                            snippet=snippet,
                        )
                    )

    def scan_directory(self, target_dir: Path):
        if not target_dir.exists():
            return
        for file_path in target_dir.rglob("*.py"):
            if not any(part in IGNORED_DIRECTORIES for part in file_path.parts):
                self.scan_file(file_path)

    def get_duplicate_clusters(self) -> List[DuplicateCloneCluster]:
        clusters: List[DuplicateCloneCluster] = []
        for h, occs in self.hash_to_occurrences.items():
            unique_locs: List[CodeOccurrence] = []
            seen: Set[tuple] = set()
            for o in occs:
                key = (o.file_path, o.start_line)
                if key not in seen:
                    seen.add(key)
                    unique_locs.append(o)

            if len(unique_locs) >= 2:
                distinct_funcs = {f"{o.file_path}::{o.function_name}" for o in unique_locs}
                if len(distinct_funcs) >= 2:
                    clusters.append(
                        DuplicateCloneCluster(
                            hash_id=h,
                            statements_count=self.min_statements,
                            occurrences=unique_locs,
                        )
                    )

        clusters.sort(key=lambda c: len(c.occurrences), reverse=True)
        return clusters

def print_report(clusters: List[DuplicateCloneCluster], scanner: DuplicationScanner):
    print(f"\n{COLOR_BOLD}{COLOR_CYAN}{'='*70}{COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}    MINIKICK - AUDITOR DE CÓDIGO DUPLICADO & CLONES AST (DRY)         {COLOR_RESET}")
    print(f"{COLOR_BOLD}{COLOR_CYAN}{'='*70}{COLOR_RESET}\n")

    print(f"Archivos analizados:  {COLOR_BOLD}{scanner.scanned_files_count}{COLOR_RESET}")
    print(f"Funciones evaluadas:  {COLOR_BOLD}{scanner.total_functions_count}{COLOR_RESET}")
    print(f"Umbral de sentencias: {COLOR_BOLD}>= {scanner.min_statements} sentencias consecutivas{COLOR_RESET}\n")

    if not clusters:
        print(f"{COLOR_GREEN}{COLOR_BOLD}✅ ¡EXCELENTE! Cero bloques de lógica duplicados detectados en el codebase.{COLOR_RESET}")
        print(f"{COLOR_GRAY}El código mantiene alta cohesión y cumple los principios DRY y SoR.{COLOR_RESET}\n")
        return

    print(f"{COLOR_BOLD}{COLOR_YELLOW}⚠️ Se detectaron {len(clusters)} clusters de lógica clonada o duplicada:{COLOR_RESET}\n")
    for idx, c in enumerate(clusters[:10], 1):
        print(f"  {COLOR_BOLD}Clon #{idx} [Hash: {c.hash_id}] ({len(c.occurrences)} repeticiones):{COLOR_RESET}")
        for occ in c.occurrences:
            print(f"    • {COLOR_CYAN}{occ.file_path}:{occ.start_line}-{occ.end_line}{COLOR_RESET} en {COLOR_MAGENTA}{occ.function_name}(){COLOR_RESET}")
        print(f"    {COLOR_GRAY}Muestra de código:{COLOR_RESET}")
        for line in occ.snippet.splitlines()[:4]:
            print(f"      {COLOR_GRAY}| {line}{COLOR_RESET}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Busca bloques de sentencias consecutivas duplicados en el código Python del proyecto.")
    parser.add_argument("--min-statements", "-m", type=int, default=5, help="Mínimo de sentencias consecutivas para considerar clon (default: 5)")
    parser.add_argument("--json", action="store_true", help="Exportar resultados en formato JSON por consola")
    parser.add_argument("--output", "-o", type=str, default=None, help="Ruta de archivo para guardar el reporte JSON")
    parser.add_argument("--strict", action="store_true", help="Terminar con código 1 si se detecta cualquier duplicado")

    args = parser.parse_args()

    scanner = DuplicationScanner(min_statements=args.min_statements)
    scanner.scan_directory(PROJECT_ROOT / "backend")
    scanner.scan_directory(PROJECT_ROOT / "frontend")

    clusters = scanner.get_duplicate_clusters()

    if args.json or args.output:
        data = {
            "summary": {
                "scanned_files": scanner.scanned_files_count,
                "total_functions": scanner.total_functions_count,
                "min_statements": args.min_statements,
                "clusters_count": len(clusters),
                "is_clean": len(clusters) == 0,
            },
            "clusters": [
                {
                    "hash": c.hash_id,
                    "statements_count": c.statements_count,
                    "occurrences_count": len(c.occurrences),
                    "occurrences": [
                        {
                            "file": o.file_path,
                            "start_line": o.start_line,
                            "end_line": o.end_line,
                            "function": o.function_name,
                        }
                        for o in c.occurrences
                    ],
                }
                for c in clusters
            ],
        }
        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        if args.output:
            out_path = Path(args.output).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_content, encoding="utf-8")
            print(f"{COLOR_GREEN}✓ Reporte JSON exportado exitosamente en:{COLOR_RESET} {COLOR_CYAN}{out_path}{COLOR_RESET}")

        if args.json and not args.output:
            print(json_content)
        elif not args.json:
            print_report(clusters, scanner)
    else:
        print_report(clusters, scanner)

    if args.strict and clusters:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
