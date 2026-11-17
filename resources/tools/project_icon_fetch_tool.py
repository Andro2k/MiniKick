# resources\tools\project_icon_fetch_tool.py
"""Herramienta de iconos: descarga iconos de Lucide desde Iconify a assets/icons/lucide/ usando sus nombres."""

import argparse
import contextlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Protocol, Set, Tuple
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"
PACK_DIR = "lucide"
ICONIFY_PREFIX = "lucide"

ICONIFY_API = "https://api.iconify.design"
BATCH_SIZE = 40
REQUEST_TIMEOUT = 20.0

GRID = 24
SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">{body}</svg>'
)
_ALLOWED_ICON_KEYS = {"body", "width", "height", "hidden"}


class IconifyClient(Protocol):
    def fetch(self, prefix: str, names: List[str]) -> dict: ...


class IconifyApiClient:
    def __init__(self, api_url: str = ICONIFY_API):
        self._api_url = api_url.rstrip("/")

    def fetch(self, prefix: str, names: List[str]) -> dict:
        url = f"{self._api_url}/{prefix}.json?icons={quote(','.join(names), safe=',')}"
        request = Request(url, headers={"User-Agent": "MiniKick-icon-fetch"})
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.load(response)


@dataclass
class FetchReport:
    written: List[str] = field(default_factory=list)
    renamed: Dict[str, str] = field(default_factory=dict)
    unusable: List[str] = field(default_factory=list)


def resolve_icon(payload: dict, name: str) -> Optional[Tuple[str, str]]:
    """(nombre canónico, cuerpo SVG) siguiendo alias; None si falta, trae transformaciones o no usa la cuadrícula de 24."""
    aliases = payload.get("aliases", {})
    seen: Set[str] = set()
    while name in aliases and name not in seen:
        seen.add(name)
        alias = aliases[name]
        if set(alias) - {"parent"}:
            return None
        name = alias["parent"]
    icon = payload.get("icons", {}).get(name)
    if icon is None or set(icon) - _ALLOWED_ICON_KEYS:
        return None
    size = (icon.get("width", payload.get("width", GRID)), icon.get("height", payload.get("height", GRID)))
    return (name, icon["body"]) if size == (GRID, GRID) else None


def normalize_names(raw_names: List[str]) -> List[str]:
    """Acepta 'check', 'check.svg' o 'icons/check.svg'; devuelve nombres de Lucide sin duplicados."""
    names = (Path(raw.strip()).name.removesuffix(".svg") for raw in raw_names if raw.strip())
    return list(dict.fromkeys(names))


def list_pack_icons(icons_dir: Path = ICONS_DIR) -> List[str]:
    return sorted(path.stem for path in (icons_dir / PACK_DIR).glob("*.svg"))


def _chunks(items: List[str], size: int) -> Iterator[List[str]]:
    for start in range(0, len(items), size):
        yield items[start:start + size]


def fetch_icons(names: List[str], client: IconifyClient, icons_dir: Path = ICONS_DIR) -> FetchReport:
    """Escribe cada icono como assets/icons/lucide/<nombre canónico>.svg con la plantilla única."""
    report = FetchReport()
    resolved: Dict[str, Optional[Tuple[str, str]]] = {}
    for batch in _chunks(names, BATCH_SIZE):
        payload = client.fetch(ICONIFY_PREFIX, batch)
        resolved.update({name: resolve_icon(payload, name) for name in batch})

    target_dir = icons_dir / PACK_DIR
    for name in names:
        icon = resolved.get(name)
        if icon is None:
            report.unusable.append(name)
            continue
        canonical, body = icon
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_dir / f"{canonical}.svg", "w", encoding="utf-8", newline="") as handle:
            handle.write(SVG_TEMPLATE.format(body=body))
        report.written.append(canonical)
        if canonical != name:
            report.renamed[name] = canonical
    return report


def _print_report(report: FetchReport) -> None:
    print(f"✅ Iconos escritos en assets/icons/{PACK_DIR}/: {len(report.written)}")
    for requested, canonical in sorted(report.renamed.items()):
        print(f"  ↪ '{requested}' es un alias; se guardó como '{canonical}.svg'")
    print(f"🔴 Sin equivalente utilizable: {len(report.unusable)}")
    for name in report.unusable:
        print(f"  ❌ {name}  (no existe en Lucide, trae transformaciones o no usa la cuadrícula de {GRID})")
    print("➡️  Siguiente paso: python resources/tools/project_icon_grid_tool.py --check")


def main() -> int:
    parser = argparse.ArgumentParser(description="Descarga iconos de Lucide a assets/icons/lucide/ por su nombre.")
    parser.add_argument("names", nargs="*", help="Nombres de Lucide (ej. check chevron-down); sin nombres, actualiza todo el pack")
    parser.add_argument("--api", default=ICONIFY_API, help="URL base de la API de Iconify (espejo o proxy)")
    args = parser.parse_args()

    names = normalize_names(args.names) or list_pack_icons()
    if not names:
        print(f"⚠️  assets/icons/{PACK_DIR}/ está vacío: indica los nombres de los iconos a descargar.")
        return 2
    try:
        report = fetch_icons(names, IconifyApiClient(args.api))
    except (URLError, OSError, ValueError) as exc:
        print(f"❌ No se pudo consultar Iconify: {exc}")
        return 2
    _print_report(report)
    return 1 if report.unusable else 0


if __name__ == "__main__":
    sys.exit(main())
