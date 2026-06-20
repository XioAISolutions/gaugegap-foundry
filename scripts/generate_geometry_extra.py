#!/usr/bin/env python3
"""Deeper geometry figures: animated 'flatten' reels (inline-renderable SMIL SVG),
the full A-G Dynkin atlas, and a Calabi-Yau mirror-pair diamond.

CLAIM BOUNDARY: exact representation-theory / topology objects, faithfully drawn.
The animation is a decorative motion over exact keyframes; no physics claim.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.visualization.svg import SVGCanvas
from gaugegap.visualization.weight_diagrams import su3_weights, su3_root_system
from gaugegap.visualization.topology import (
    dynkin_diagram, fermat_quintic_hodge, mirror_threefold, is_mirror_pair,
)

_SIZE = 600
_PAD = 80
_ACCENT = "#58a6ff"
_POINT = "#f0c674"
_PREC = 2


def _r(x):
    return f"{round(float(x), _PREC):g}"


def _rotate(P, yaw, pitch=0.5):
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return P @ (rx @ ry).T


def animated_flatten_svg(points3d, flat2d, title, frames=36, dur=6.0) -> str:
    """SMIL-animated SVG: rotate the 3D structure and ease it flat to its exact
    2D shadow, looping. ``points3d`` (M,3), ``flat2d`` (M,2)."""
    P = np.asarray(points3d, dtype=float)
    F = np.asarray(flat2d, dtype=float)
    P = P - P.mean(axis=0)
    # precompute per-frame 2D positions
    frame_xy = []
    for k in range(frames):
        t = (1 - np.cos(2 * np.pi * k / frames)) / 2.0   # 0->1->0
        yaw = 2 * np.pi * k / frames
        rot = _rotate(P, yaw)[:, :2]
        xy = (1 - t) * rot + t * F
        frame_xy.append(xy)
    allpts = np.concatenate(frame_xy, axis=0)
    lo = allpts.min(axis=0); hi = allpts.max(axis=0)
    span = max(hi[0] - lo[0], hi[1] - lo[1]) or 1.0
    sc = (_SIZE - 2 * _PAD) / span
    cx, cy = (lo + hi) / 2

    def tf(p):
        return (_SIZE / 2 + (p[0] - cx) * sc, _SIZE / 2 - (p[1] - cy) * sc)

    keytimes = ";".join(_r(k / (frames - 1)) for k in range(frames))
    elems = []
    M = P.shape[0]
    for i in range(M):
        xs = ";".join(_r(tf(frame_xy[k][i])[0]) for k in range(frames))
        ys = ";".join(_r(tf(frame_xy[k][i])[1]) for k in range(frames))
        elems.append(
            f'<circle r="8" fill="{_POINT}" stroke="#0b0e14" stroke-width="1">'
            f'<animate attributeName="cx" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="{keytimes}" values="{xs}"/>'
            f'<animate attributeName="cy" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="{keytimes}" values="{ys}"/></circle>')
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SIZE}" '
            f'height="{_SIZE}" viewBox="0 0 {_SIZE} {_SIZE}">')
    bg = f'<rect width="{_SIZE}" height="{_SIZE}" fill="#0b0e14"/>'
    cap = (f'<text x="{_SIZE/2}" y="{_SIZE-20}" font-size="14" fill="#e6edf3" '
           f'text-anchor="middle" font-family="monospace">{title}</text>'
           f'<text x="{_SIZE/2}" y="{_SIZE-6}" font-size="10" fill="#8b949e" '
           f'text-anchor="middle" font-family="monospace">'
           f'animated flatten to exact 2D shadow (SMIL)</text>')
    return head + bg + "".join(elems) + cap + "</svg>\n"


def _dynkin_positions(typ: str, n: int):
    typ = typ.upper()
    if typ in ("A", "B", "C", "F", "G"):
        return {i: (i, 0) for i in range(n)}
    if typ == "D":
        pos = {i: (i, 0) for i in range(n - 1)}
        pos[n - 1] = (n - 3, 1)   # fork at node n-3
        return pos
    if typ == "E":
        pos = {i: (i, 0) for i in range(n - 1)}
        pos[n - 1] = (2, 1)       # branch above node 2
        return pos
    raise ValueError(typ)


def dynkin_svg(typ: str, n: int) -> SVGCanvas:
    d = dynkin_diagram(typ, n)
    pos = _dynkin_positions(typ, n)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    spanx = (max(xs) - min(xs)) or 1
    spany = (max(ys) - min(ys)) or 1
    scale = min((_SIZE - 2 * _PAD) / spanx, 180 / spany if spany else 180)
    H = 300
    ox = _PAD - min(xs) * scale
    oy = H / 2 + (max(ys) + min(ys)) / 2 * scale

    def tf(node):
        x, y = pos[node]
        return (ox + x * scale, oy - y * scale)

    c = SVGCanvas(_SIZE, H)
    for b in d["bonds"]:
        a, bb, m = b["i"], b["j"], b["mult"]
        xa, ya = tf(a); xb, yb = tf(bb)
        # draw m parallel lines for a multiplicity-m bond
        dx, dy = xb - xa, yb - ya
        ln = (dx * dx + dy * dy) ** 0.5 or 1
        nx, ny = -dy / ln, dx / ln
        for k in range(m):
            off = (k - (m - 1) / 2) * 4
            c.line(xa + nx * off, ya + ny * off, xb + nx * off, yb + ny * off,
                   stroke=_ACCENT, stroke_width=2.0)
        if m > 1:  # arrow (long->short) at the midpoint
            mxp, myp = (xa + xb) / 2, (ya + yb) / 2
            c.polygon([(mxp + dx / ln * 7, myp + dy / ln * 7),
                       (mxp - dx / ln * 3 + nx * 5, myp - dy / ln * 3 + ny * 5),
                       (mxp - dx / ln * 3 - nx * 5, myp - dy / ln * 3 - ny * 5)],
                      fill=_POINT, stroke="none")
    for node in d["nodes"]:
        x, y = tf(node)
        c.circle(x, y, 11, fill="#161b22", stroke=_POINT, stroke_width=2.0)
    c.text(_SIZE / 2, 40, f"Dynkin diagram {d['type']}  "
           f"(det {d['determinant']}, pos-def {d['positive_definite']})", size=15)
    return c


def mirror_diamond_svg(diamond) -> SVGCanvas:
    mir = mirror_threefold(diamond)
    c = SVGCanvas(_SIZE, 380)
    for col, dia, label in [(_SIZE * 0.27, diamond, diamond.name),
                            (_SIZE * 0.73, mir, "mirror")]:
        n = dia.complex_dim
        dy = 46
        top = 70
        for (p, q), v in dia.h.items():
            x = col + (q - p) * 26
            y = top + (p + q) * dy
            c.circle(x, y, 14, fill="#161b22", stroke=_ACCENT, stroke_width=1.2)
            c.text(x, y + 4, str(v), size=12, fill=_POINT)
        c.text(col, top - 24, f"{label}  χ={dia.euler_characteristic()}", size=12)
    c.text(_SIZE / 2, 30, "Calabi-Yau mirror pair  (h11<->h21, χ -> -χ)", size=15)
    c.text(_SIZE / 2, 360,
           f"mirror pair verified: {is_mirror_pair(diamond, mir)}",
           size=11, fill="#8b949e")
    return c


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "figures" / "geometry")
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    # (1) animated flatten reels
    ws = su3_weights(1, 1)
    p3 = np.array([w["r3"] for w in ws])
    f2 = np.array([[w["t3"], w["y"]] for w in ws])
    (out / "octet_flatten_reel.svg").write_text(
        animated_flatten_svg(p3, f2, "su(3) octet"))
    roots = su3_root_system()
    rp3 = np.array([r["r3"] for r in roots])
    rf2 = np.array([[r["t3"], r["y"]] for r in roots])
    (out / "root_flatten_reel.svg").write_text(
        animated_flatten_svg(rp3, rf2, "su(3) root system"))

    # (3) full A-G Dynkin atlas
    atlas = [("A", 4), ("B", 4), ("C", 4), ("D", 5), ("E", 6), ("E", 7),
             ("E", 8), ("F", 4), ("G", 2)]
    for typ, n in atlas:
        dynkin_svg(typ, n).write(out / f"dynkin_{typ}{n}.svg")

    # (2) mirror pair
    mirror_diamond_svg(fermat_quintic_hodge()).write(out / "calabi_yau_mirror_pair.svg")

    # data
    diamonds = fermat_quintic_hodge()
    data = {
        "dynkin_atlas": {f"{t}{n}": dynkin_diagram(t, n) for (t, n) in atlas},
        "mirror_pair": {
            "quintic": diamonds.to_dict(),
            "mirror": mirror_threefold(diamonds).to_dict(),
            "is_mirror_pair": is_mirror_pair(diamonds, mirror_threefold(diamonds)),
        },
    }
    (out / "geometry_atlas.json").write_text(json.dumps(data, indent=2, sort_keys=True))
    print(f"wrote 2 reels + {len(atlas)} Dynkin diagrams + mirror pair + atlas json "
          f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
