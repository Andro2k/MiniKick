# resources\tools\project_icon_fetch_tool.py
"""Herramienta de packs de iconos: genera assets/icons/<pack>/ desde Iconify con una tabla de equivalencias."""

import argparse
import contextlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, Iterator, List, Optional, Protocol, Set
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"
BASE_PACK_DIR = "outline"

ICONIFY_API = "https://api.iconify.design"
BATCH_SIZE = 40
REQUEST_TIMEOUT = 20.0

GRID = 24
SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">{body}</svg>'
)
_ALLOWED_ICON_KEYS = {"body", "width", "height", "hidden"}


@dataclass(frozen=True)
class PackSource:
    """Equivalencias de un pack: nombre local (sin .svg) -> icono del set de Iconify."""
    prefix: str
    overrides: Dict[str, str] = field(default_factory=dict)
    skip: FrozenSet[str] = frozenset()

    def iconify_name(self, stem: str) -> Optional[str]:
        """Nombre en Iconify; por defecto el nombre local sin el sufijo -outline. None si el set no lo cubre."""
        if stem in self.skip:
            return None
        return self.overrides.get(stem) or (stem[:-len("-outline")] if stem.endswith("-outline") else stem)


PACKS: Dict[str, PackSource] = {
    "lucide": PackSource(
        prefix="lucide",
        overrides={
            "alarm-outline": "alarm-clock",
            "album-outline": "disc-album",
            "align-left-outline": "text-align-start",
            "angles-left-outline": "chevrons-left",
            "angles-right-outline": "chevrons-right",
            "bolt-circle-outline": "zap",
            "browser-code-outline": "app-window",
            "carousel-h-outline": "gallery-horizontal",
            "carousel-v-outline": "gallery-vertical",
            "circle-info-outline": "info",
            "crosshairs-outline": "crosshair",
            "dialog-outline": "messages-square",
            "dots-horizontal-outline": "ellipsis",
            "element-outline": "layout-dashboard",
            "emoji-circle-outline": "smile",
            "filter-outline": "funnel",
            "gear-outline": "settings",
            "hashtag-outline": "hash",
            "music-notes-outline": "music",
            "prism-outline": "gem",
            "refresh-outline": "refresh-cw",
            "restart-outline": "rotate-cw",
            "skip-next-outline": "skip-forward",
            "squares-outline": "squares-unite",
            "text-outline": "type",
            "textalign-center-outline": "text-align-center",
            "textalign-justifycenter-outline": "text-align-justify",
            "textalign-left-outline": "text-align-start",
            "textalign-right-outline": "text-align-end",
            "transfer-v-outline": "arrow-up-down",
            "treasure-chest-outline": "package-open",
            "volume-up-outline": "volume-2",
            "webhooks-outline": "webhook",
            "widget-add-outline": "blocks",
        },
        # Punto relleno del indicador de QSS: Lucide no tiene equivalente, lo cubre el pack base.
        skip=frozenset({"radio-dot"}),
    ),
}


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
    covered_by_fallback: List[str] = field(default_factory=list)
    unusable: Dict[str, str] = field(default_factory=dict)


def resolve_body(payload: dict, name: str) -> Optional[str]:
    """Cuerpo SVG de un icono siguiendo alias; None si falta, trae transformaciones o no usa la cuadrícula de 24."""
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
    return icon["body"] if size == (GRID, GRID) else None


def list_base_icons(icons_dir: Path = ICONS_DIR) -> List[str]:
    return sorted(path.stem for path in (icons_dir / BASE_PACK_DIR).glob("*.svg"))


def plan_pack(pack: str, icons_dir: Path = ICONS_DIR, only: Optional[Set[str]] = None) -> Dict[str, Optional[str]]:
    """Nombre local -> icono de Iconify (None si el pack no lo cubre), para los iconos del pack base."""
    source = PACKS[pack]
    return {
        stem: source.iconify_name(stem)
        for stem in list_base_icons(icons_dir)
        if not only or stem in only
    }


def _chunks(items: List[str], size: int) -> Iterator[List[str]]:
    for start in range(0, len(items), size):
        yield items[start:start + size]


def fetch_pack(pack: str, client: IconifyClient, icons_dir: Path = ICONS_DIR, only: Optional[Set[str]] = None) -> FetchReport:
    plan = plan_pack(pack, icons_dir, only)
    report = FetchReport(covered_by_fallback=[stem for stem, name in plan.items() if name is None])

    names = sorted({name for name in plan.values() if name})
    bodies: Dict[str, Optional[str]] = {}
    for batch in _chunks(names, BATCH_SIZE):
        payload = client.fetch(PACKS[pack].prefix, batch)
        bodies.update({name: resolve_body(payload, name) for name in batch})

    target_dir = icons_dir / pack
    for stem, name in plan.items():
        if name is None:
            continue
        body = bodies.get(name)
        if body is None:
            report.unusable[stem] = name
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_dir / f"{stem}.svg", "w", encoding="utf-8", newline="") as handle:
            handle.write(SVG_TEMPLATE.format(body=body))
        report.written.append(stem)
    return report


def _print_plan(pack: str, plan: Dict[str, Optional[str]]) -> None:
    print(f"📋 Plan para el pack '{pack}' ({PACKS[pack].prefix}): {len(plan)} iconos")
    for stem, name in plan.items():
        print(f"  {stem:<34} -> {name or '(respaldo: pack base)'}")


def _print_report(pack: str, report: FetchReport) -> None:
    print(f"✅ Iconos generados en assets/icons/{pack}/: {len(report.written)}")
    print(f"🟡 Cubiertos por el pack base: {len(report.covered_by_fallback)}")
    print(f"🔴 Sin equivalente utilizable: {len(report.unusable)}")
    for stem, name in sorted(report.unusable.items()):
        print(f"  ❌ {stem}  (Iconify: '{name}' no existe, trae transformaciones o no usa la cuadrícula de {GRID})")
    if report.unusable:
        print("   Corrige la tabla PACKS de project_icon_fetch_tool.py y vuelve a ejecutarlo; mientras tanto los cubre el pack base.")
    print("➡️  Siguiente paso: python resources/tools/project_icon_grid_tool.py --check")


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un pack de iconos en assets/icons/<pack>/ desde Iconify.")
    parser.add_argument("pack", choices=sorted(PACKS), help="Pack a generar")
    parser.add_argument("--only", help="Lista de nombres locales separados por coma (sin .svg)")
    parser.add_argument("--dry-run", action="store_true", help="Muestra la tabla de equivalencias sin consultar la red")
    parser.add_argument("--api", default=ICONIFY_API, help="URL base de la API de Iconify (espejo o proxy)")
    args = parser.parse_args()

    only = {item.strip() for item in args.only.split(",") if item.strip()} if args.only else None
    if args.dry_run:
        _print_plan(args.pack, plan_pack(args.pack, only=only))
        return 0
    try:
        report = fetch_pack(args.pack, IconifyApiClient(args.api), only=only)
    except (URLError, OSError, ValueError) as exc:
        print(f"❌ No se pudo consultar Iconify: {exc}")
        return 2
    _print_report(args.pack, report)
    return 1 if report.unusable else 0


if __name__ == "__main__":
    sys.exit(main())
