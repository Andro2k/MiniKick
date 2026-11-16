# resources\tools\project_locales_ftl_tool.py
"""Convierte assets/locales/<lang>.json en assets/i18n/<lang>/main.ftl (Fluent).

Las claves anidadas `a.b.c` pasan a identificadores planos `a-b-c` y los
marcadores `{nombre}` a variables Fluent `{ $nombre }`. Con --check no escribe
nada: falla si algun .ftl no coincide con lo que generaria el JSON.
"""

import json
import os
import re
import sys
from typing import Dict, Iterator, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCALES_DIR = os.path.join(PROJECT_ROOT, "assets", "locales")
FTL_DIR = os.path.join(PROJECT_ROOT, "assets", "i18n")
FTL_FILENAME = "main.ftl"

_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_FTL_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def ftl_id(dotted_key: str) -> str:
    """`chat.commands_help.sec_chat` -> `chat-commands_help-sec_chat`."""
    return dotted_key.replace(".", "-")


def flatten(tree: Dict, prefix: str = "") -> Iterator[Tuple[str, str]]:
    for key, value in tree.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten(value, path)
        else:
            yield path, str(value)


def _literal(char: str) -> str:
    return '{ "\\u%04X" }' % ord(char)


def ftl_value(text: str) -> str:
    """Escapa un valor de JSON para que Fluent lo lea identico en una sola linea."""
    out: List[str] = []
    last = len(text) - 1
    pos = 0
    for match in _PLACEHOLDER.finditer(text):
        out.append(_escape_plain(text[pos:match.start()], pos, last))
        out.append("{ $%s }" % match.group(1))
        pos = match.end()
    out.append(_escape_plain(text[pos:], pos, last))
    return "".join(out)


def _escape_plain(chunk: str, offset: int, last: int) -> str:
    out = []
    for i, char in enumerate(chunk):
        at_edge = offset + i in (0, last)
        if char in "{}":
            out.append('{ "%s" }' % char)
        elif char.isspace() and (char != " " or at_edge):
            out.append(_literal(char))
        else:
            out.append(char)
    return "".join(out)


def render(tree: Dict) -> str:
    lines: List[str] = ["# Generado por resources/tools/project_locales_ftl_tool.py", ""]
    group = None
    for key, value in flatten(tree):
        name = ftl_id(key)
        if not _FTL_ID.fullmatch(name):
            raise ValueError(f"Clave no valida para Fluent: {key!r}")
        top = key.split(".", 1)[0]
        if top != group:
            group = top
            lines += ["", f"## {top}"]
        lines.append(f"{name} = {ftl_value(value)}")
    return "\n".join(lines) + "\n"


def languages() -> List[str]:
    return sorted(f[:-5] for f in os.listdir(LOCALES_DIR) if f.endswith(".json"))


def source_path(lang: str) -> str:
    return os.path.join(LOCALES_DIR, f"{lang}.json")


def target_path(lang: str) -> str:
    return os.path.join(FTL_DIR, lang, FTL_FILENAME)


def generate(lang: str) -> str:
    with open(source_path(lang), encoding="utf-8") as handle:
        return render(json.load(handle))


def main() -> int:
    check = "--check" in sys.argv[1:]
    stale = 0
    for lang in languages():
        expected = generate(lang)
        path = target_path(lang)
        current = None
        if os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as handle:
                current = handle.read()
        if current == expected:
            continue
        stale += 1
        if check:
            print(f"DESACTUALIZADO: {os.path.relpath(path, PROJECT_ROOT)}")
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(expected)
        print(f"Generado: {os.path.relpath(path, PROJECT_ROOT)}")
    print(f"idiomas: {len(languages())} | desactualizados: {stale}")
    return 1 if (check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
