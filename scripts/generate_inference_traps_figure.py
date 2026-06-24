#!/usr/bin/env python3
"""Generate the diagram for the web of inference traps (deterministic, dependency-free SVG).

Two families of decision-theory / statistics traps -- heavy-tail (the mean misleads) and
selection/conditioning (the wrong conditioning flips the conclusion) -- with Bayes as the
corrective framework. Mirrors the style of the physical-limits web figures.

CLAIM BOUNDARY: an explanatory figure for exact, closed-form decision-theory vignettes;
no new claims; not physical bounds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from gaugegap.visualization.svg import SVGCanvas

C_TXT = "#e6edf3"
C_MUTED = "#8b949e"
C_TAIL = "#f0c674"     # heavy-tail family (gold)
C_SEL = "#58a6ff"      # selection family (blue)
C_FIX = "#7ee787"      # Bayes (green)
C_CARD = "#11151c"
C_EDGE = "#222831"

HEAVY_TAIL = [
    ("St. Petersburg paradox", "naive EV = ∞, but bounded-utility value = $4"),
    ("Power law", "scale-free tail; E[X^m]=∞ iff m≥α"),
]
SELECTION = [
    ("Survivorship bias (Wald)", "armor the holes you DON'T see on survivors"),
    ("Berkson's paradox", "selection makes independent traits anti-correlate (−½)"),
    ("Simpson's paradox", "every subgroup favours A, the aggregate favours B"),
    ("Regression to the mean", "extremes are followed by E[Y|X=x]=ρx, closer in"),
]


def _card(c, x, y, w, h, color, title, members):
    c.polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
              fill=C_CARD, stroke=color, stroke_width=2.0)
    c.text(x + 18, y + 30, title, size=17, fill=color, anchor="start")
    yy = y + 64
    for name, core in members:
        c.circle(x + 24, yy - 5, 4.5, fill=color, stroke="none")
        c.text(x + 38, yy, name, size=14, fill=C_TXT, anchor="start")
        c.text(x + 38, yy + 18, core, size=11, fill=C_MUTED, anchor="start")
        yy += 52


def build(path: Path):
    W, H = 940, 620
    c = SVGCanvas(W, H)
    c.text(W / 2, 46, "The web of inference traps", size=23, fill=C_TXT)
    c.text(W / 2, 72, "viral statistics 'mind-benders', each reduced to an exact, "
           "certifiable core", size=13, fill=C_MUTED)

    _card(c, 40, 110, 420, 200, C_TAIL,
          "Heavy-tail traps  ·  the mean misleads", HEAVY_TAIL)
    _card(c, 480, 110, 420, 360, C_SEL,
          "Selection / conditioning traps", SELECTION)

    # Bayes corrective bar spanning the bottom of the heavy-tail column
    by = 350
    c.polygon([(40, by), (460, by), (460, by + 120), (40, by + 120)],
              fill=C_CARD, stroke=C_FIX, stroke_width=2.0)
    c.text(40 + 18, by + 30, "Bayes' theorem  ·  the corrective", size=17, fill=C_FIX,
           anchor="start")
    c.text(40 + 38, by + 60, "force the base rate into the calculation:", size=12,
           fill=C_MUTED, anchor="start")
    c.text(40 + 38, by + 82, "99%-accurate test, 0.1% prevalence", size=13, fill=C_TXT,
           anchor="start")
    c.text(40 + 38, by + 102, "⇒ P(disease | +) ≈ 1.9%", size=14, fill=C_FIX,
           anchor="start")

    c.text(W / 2, H - 26, "exact closed forms, each with a claim boundary — "
           "companion to the physical-limits web", size=12, fill=C_MUTED)
    c.text(W / 2, H - 10, "decision theory & statistics — NOT physical bounds", size=10,
           fill=C_MUTED)
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "figures" / "inference-traps")
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    build(out / "web.svg")
    print(f"Wrote web.svg to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
