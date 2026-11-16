# resources\tools\project_icon_grid_tool.py
"""Herramienta de cuadrícula de iconos: mide y normaliza el centrado, el área útil y el lienzo de los SVG de cada pack."""

import argparse
import contextlib
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QByteArray, QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICONS_DIR = PROJECT_ROOT / "assets" / "icons"
SHARED_PACK_DIR = "common"

GRID = 24
CANVAS_SIZE = "24"
LIVE_AREA = 22.0
TOLERANCE = 0.5
RENDER_SCALE = 8

WRAPPER_MARK = "data-icon-grid"
_ROOT_TAG_RE = re.compile(r"<svg\b[^>]*>")
_WRAPPER_RE = re.compile(r'<g ' + WRAPPER_MARK + r'="1" transform="[^"]*">(.*)</g>\s*(</svg>)', re.S)
_SIZE_ATTR_RE = re.compile(r'\s(?:width|height)="[^"]*"')

_qt_app: Optional[QGuiApplication] = None


@dataclass(frozen=True)
class Bounds:
    x0: float
    x1: float
    y0: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2


@dataclass(frozen=True)
class Adjustment:
    dx: float
    dy: float
    scale: float


@dataclass
class IconGridReport:
    pack: str
    name: str
    path: Path
    bounds: Optional[Bounds]
    adjustment: Optional[Adjustment]
    canvas_ok: bool
    issues: List[str] = field(default_factory=list)


def _ensure_qt_app() -> None:
    global _qt_app
    if QGuiApplication.instance() is None:
        _qt_app = QGuiApplication([])


def measure(svg_xml: str) -> Optional[Bounds]:
    """Caja real (en unidades de la cuadrícula de 24) que ocupan los píxeles del glifo."""
    _ensure_qt_app()
    renderer = QSvgRenderer(QByteArray(svg_xml.encode("utf-8")))
    if not renderer.isValid():
        return None
    side = GRID * RENDER_SCALE
    image = QImage(side, side, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, side, side))
    painter.end()

    alpha = image.convertToFormat(QImage.Format.Format_Alpha8)
    data = bytes(alpha.constBits())
    stride = alpha.bytesPerLine()
    rows: List[int] = []
    left, right = side, 0
    for y in range(side):
        row = data[y * stride:y * stride + side]
        if row.strip(b"\0"):
            rows.append(y)
            left = min(left, side - len(row.lstrip(b"\0")))
            right = max(right, len(row.rstrip(b"\0")))
    if not rows:
        return None
    return Bounds(left / RENDER_SCALE, right / RENDER_SCALE, rows[0] / RENDER_SCALE, (rows[-1] + 1) / RENDER_SCALE)


def plan_adjustment(bounds: Bounds) -> Optional[Adjustment]:
    """Traslación y escala que dejan el glifo centrado y dentro del área útil; None si ya cumple."""
    scale = min(1.0, LIVE_AREA / max(bounds.width, bounds.height))
    off_center = max(abs(bounds.center_x - GRID / 2), abs(bounds.center_y - GRID / 2)) > TOLERANCE
    if scale == 1.0 and not off_center:
        return None
    return Adjustment(
        dx=round(GRID / 2 - scale * bounds.center_x, 4),
        dy=round(GRID / 2 - scale * bounds.center_y, 4),
        scale=round(scale, 4),
    )


def unwrap(svg_xml: str) -> str:
    return _WRAPPER_RE.sub(r"\1\2", svg_xml)


def apply_adjustment(svg_xml: str, adjustment: Adjustment) -> str:
    """Envuelve el contenido en un <g> con la transformación; la geometría original no se edita."""
    transform = f"translate({adjustment.dx:g} {adjustment.dy:g})"
    if adjustment.scale != 1.0:
        transform += f" scale({adjustment.scale:g})"
    root = _ROOT_TAG_RE.search(svg_xml)
    close = svg_xml.rfind("</svg>")
    if root is None or close == -1:
        return svg_xml
    return (
        svg_xml[:root.end()]
        + f'<g {WRAPPER_MARK}="1" transform="{transform}">'
        + svg_xml[root.end():close]
        + "</g>"
        + svg_xml[close:]
    )


def canvas_is_standard(svg_xml: str) -> bool:
    root = _ROOT_TAG_RE.search(svg_xml)
    if root is None:
        return False
    tag = root.group(0)
    return f'width="{CANVAS_SIZE}"' in tag and f'height="{CANVAS_SIZE}"' in tag and 'viewBox="0 0 24 24"' in tag


def normalize_canvas(svg_xml: str) -> str:
    def _rewrite(match: re.Match) -> str:
        tag = _SIZE_ATTR_RE.sub("", match.group(0))
        return tag.replace("<svg", f'<svg width="{CANVAS_SIZE}" height="{CANVAS_SIZE}"', 1)
    return _ROOT_TAG_RE.sub(_rewrite, svg_xml, count=1)


def _read(path: Path) -> str:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _write(path: Path, content: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def iter_pack_icons(icons_dir: Path = ICONS_DIR) -> Iterator[Path]:
    """SVG de los packs temáticos; common/ (marcas e ilustraciones) tiene su propio lienzo."""
    for pack_dir in sorted(p for p in icons_dir.iterdir() if p.is_dir() and p.name != SHARED_PACK_DIR):
        yield from sorted(pack_dir.glob("*.svg"))


def analyze(path: Path) -> IconGridReport:
    svg_xml = _read(path)
    bounds = measure(svg_xml)
    adjustment = plan_adjustment(bounds) if bounds else None
    canvas_ok = canvas_is_standard(svg_xml)
    report = IconGridReport(path.parent.name, path.stem, path, bounds, adjustment, canvas_ok)
    if bounds is None:
        report.issues.append("ILEGIBLE")
        return report
    if adjustment and adjustment.scale < 1.0:
        report.issues.append("EXCEDE ÁREA ÚTIL")
    if adjustment and (abs(bounds.center_x - GRID / 2) > TOLERANCE or abs(bounds.center_y - GRID / 2) > TOLERANCE):
        report.issues.append("DESCENTRADO")
    if not canvas_ok:
        report.issues.append("LIENZO")
    return report


def fix_icon(report: IconGridReport) -> bool:
    """Reescribe el SVG para cumplir la cuadrícula; devuelve True si el archivo cambió."""
    original = _read(report.path)
    svg_xml = unwrap(original)
    if not canvas_is_standard(svg_xml):
        svg_xml = normalize_canvas(svg_xml)
    bounds = measure(svg_xml)
    adjustment = plan_adjustment(bounds) if bounds else None
    if adjustment:
        svg_xml = apply_adjustment(svg_xml, adjustment)
    if svg_xml == original:
        return False
    _write(report.path, svg_xml)
    return True


def _format_line(report: IconGridReport) -> str:
    b = report.bounds
    geometry = "sin píxeles" if b is None else (
        f"centro ({b.center_x - GRID / 2:+.2f}, {b.center_y - GRID / 2:+.2f})u  lado {max(b.width, b.height):.2f}u"
    )
    return f"  - {report.pack}/{report.name}.svg  {geometry}  [{', '.join(report.issues)}]"


def run(fix: bool, check: bool) -> int:
    reports = [analyze(path) for path in iter_pack_icons()]
    flagged = [r for r in reports if r.issues]

    print("\n" + "=" * 55)
    print(" AUDITORÍA DE CUADRÍCULA DE ICONOS")
    print("=" * 55)
    print(f"📊 Iconos analizados: {len(reports)} (cuadrícula {GRID}u, área útil {LIVE_AREA:g}u, tolerancia {TOLERANCE}u)")
    print(f"🟡 Iconos fuera de cuadrícula: {len(flagged)}")
    for report in flagged:
        print(_format_line(report))

    if fix and flagged:
        changed = sum(fix_icon(report) for report in flagged)
        remaining = [r for r in (analyze(path) for path in iter_pack_icons()) if r.issues]
        print(f"\n🛠️ Archivos reescritos: {changed}")
        print(f"✅ Iconos fuera de cuadrícula tras normalizar: {len(remaining)}")
        return 1 if remaining else 0
    if not flagged:
        print("\n🎉 Todos los iconos cumplen la cuadrícula.")
    return 1 if (check and flagged) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Mide y normaliza el centrado, el área útil y el lienzo de los iconos SVG.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Sale con código 1 si hay iconos fuera de cuadrícula")
    mode.add_argument("--fix", action="store_true", help="Reescribe los SVG que no cumplen la cuadrícula")
    args = parser.parse_args()
    return run(fix=args.fix, check=args.check)


if __name__ == "__main__":
    sys.exit(main())
