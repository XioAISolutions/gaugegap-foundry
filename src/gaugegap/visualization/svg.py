"""Tiny dependency-free SVG canvas for reproducible figures.

Coordinates are rounded to a fixed precision so the same inputs always produce
byte-identical SVG (reproducibility, matching the repo's hashed-artifact ethos).
No external plotting dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple
from xml.sax.saxutils import escape

_PREC = 3


def _f(x: float) -> str:
    return f"{round(float(x), _PREC):g}"


@dataclass
class SVGCanvas:
    width: int = 600
    height: int = 600
    background: str = "#0b0e14"
    _elems: List[str] = field(default_factory=list)

    def circle(self, x: float, y: float, r: float, fill: str = "#e6edf3",
               stroke: str = "none", stroke_width: float = 0.0, opacity: float = 1.0):
        self._elems.append(
            f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{_f(stroke_width)}" opacity="{_f(opacity)}"/>'
        )

    def line(self, x1: float, y1: float, x2: float, y2: float,
             stroke: str = "#8b949e", stroke_width: float = 1.0, opacity: float = 1.0):
        self._elems.append(
            f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
            f'stroke="{stroke}" stroke-width="{_f(stroke_width)}" opacity="{_f(opacity)}"/>'
        )

    def polyline(self, pts: Sequence[Tuple[float, float]], stroke: str = "#58a6ff",
                 stroke_width: float = 1.0, opacity: float = 1.0, fill: str = "none"):
        d = " ".join(f"{_f(x)},{_f(y)}" for x, y in pts)
        self._elems.append(
            f'<polyline points="{d}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{_f(stroke_width)}" opacity="{_f(opacity)}"/>'
        )

    def polygon(self, pts: Sequence[Tuple[float, float]], fill: str = "none",
                stroke: str = "#58a6ff", stroke_width: float = 1.0, opacity: float = 1.0):
        d = " ".join(f"{_f(x)},{_f(y)}" for x, y in pts)
        self._elems.append(
            f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{_f(stroke_width)}" opacity="{_f(opacity)}"/>'
        )

    def text(self, x: float, y: float, s: str, size: float = 12.0,
             fill: str = "#e6edf3", anchor: str = "middle"):
        self._elems.append(
            f'<text x="{_f(x)}" y="{_f(y)}" font-size="{_f(size)}" fill="{fill}" '
            f'text-anchor="{anchor}" font-family="monospace">{escape(s)}</text>'
        )

    def to_svg(self) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
                f'height="{self.height}" viewBox="0 0 {self.width} {self.height}">')
        bg = f'<rect width="{self.width}" height="{self.height}" fill="{self.background}"/>'
        return head + bg + "".join(self._elems) + "</svg>\n"

    def write(self, path) -> None:
        from pathlib import Path
        Path(path).write_text(self.to_svg(), encoding="utf-8")


def golden_overlay(canvas: SVGCanvas, cx: float, cy: float, r0: float,
                   n: int = 6, stroke: str = "#d4a017", opacity: float = 0.18) -> None:
    """Aesthetic-only overlay: concentric circles scaled by the golden ratio.

    INSPIRATIONAL / DECORATIVE: this is a visual motif, not a mathematical claim.
    """
    phi = (1 + 5 ** 0.5) / 2
    r = r0
    for _ in range(n):
        canvas.circle(cx, cy, r, fill="none", stroke=stroke, stroke_width=1.0,
                      opacity=opacity)
        r /= phi


def vesica_overlay(canvas: SVGCanvas, cx: float, cy: float, r: float,
                   stroke: str = "#d4a017", opacity: float = 0.18) -> None:
    """Aesthetic-only Vesica Piscis (two overlapping circles) for duality motifs.

    INSPIRATIONAL / DECORATIVE: not a mathematical claim.
    """
    canvas.circle(cx - r / 2, cy, r, fill="none", stroke=stroke, stroke_width=1.0,
                  opacity=opacity)
    canvas.circle(cx + r / 2, cy, r, fill="none", stroke=stroke, stroke_width=1.0,
                  opacity=opacity)
