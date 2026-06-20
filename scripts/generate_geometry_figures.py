#!/usr/bin/env python3
"""Generate the "Geometry of GaugeGap" figures: exact 2D projections of
higher-dimensional structures, with an optional (clearly-labelled) sacred-geometry
aesthetic overlay.

Figures:
  * su(3) weight diagrams (fundamental 3, octet 8, decuplet 10) — projections of
    representation space onto the (T3, Y) plane, multiplicities exact (Freudenthal);
  * the su(3) (A2) root system — hexagonal;
  * a Calabi-Yau (Fermat quintic) cross-section — a 2D projection of an exact
    algebraic surface (Hanson construction).

CLAIM BOUNDARY: these are faithful projections of exact mathematical objects
(weight lattices / an algebraic surface). The golden-ratio / Vesica overlays are
DECORATIVE aesthetic motifs, not mathematical claims. Nothing here is physics
beyond standard su(3) representation theory and the Fermat surface.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.visualization.svg import SVGCanvas, golden_overlay, vesica_overlay
from gaugegap.visualization.weight_diagrams import (
    su3_weights, su3_dimension, su3_root_system, NAMED_IRREPS, geometry_dataset,
    su2_weights, suN_root_system_2d,
)
from gaugegap.visualization.cy_projection import fermat_patches, orthographic
from gaugegap.visualization.lattice_projection import (
    cubic_lattice, wilson_loop, project as lattice_project,
)
from gaugegap.visualization.weight_certificate import weight_symmetry_certificate
from gaugegap.visualization.topology import (
    fermat_quintic_hodge, dynkin_diagram_AN, cartan_matrix_AN,
)

_SIZE = 600
_PAD = 70
_ACCENT = "#58a6ff"
_POINT = "#f0c674"


def _fit(points, size=_SIZE, pad=_PAD):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    lo_x, hi_x = min(xs), max(xs)
    lo_y, hi_y = min(ys), max(ys)
    span = max(hi_x - lo_x, hi_y - lo_y) or 1.0
    scale = (size - 2 * pad) / span
    cx_w, cy_w = (lo_x + hi_x) / 2, (lo_y + hi_y) / 2

    def tf(x, y):
        return (size / 2 + (x - cx_w) * scale, size / 2 - (y - cy_w) * scale)
    return tf, scale


def weight_diagram_svg(p: int, q: int, title: str, sacred: bool) -> SVGCanvas:
    ws = su3_weights(p, q)
    pts = [(w["t3"], w["y"]) for w in ws]
    # Pad the fit box a little so points aren't on the edge.
    box = pts + [(0, 0)]
    tf, scale = _fit(box)
    c = SVGCanvas(_SIZE, _SIZE)
    if sacred:
        golden_overlay(c, _SIZE / 2, _SIZE / 2, (_SIZE - 2 * _PAD) / 2)
    # axes
    c.line(_PAD / 2, _SIZE / 2, _SIZE - _PAD / 2, _SIZE / 2, stroke="#30363d")
    c.line(_SIZE / 2, _PAD / 2, _SIZE / 2, _SIZE - _PAD / 2, stroke="#30363d")
    c.text(_SIZE - _PAD / 2, _SIZE / 2 - 8, "T3", size=12, fill="#8b949e")
    c.text(_SIZE / 2 + 14, _PAD / 2 + 4, "Y", size=12, fill="#8b949e")
    # convex-hull-ish outline: connect outer (mult-1 boundary) points by angle
    outer = [(w["t3"], w["y"]) for w in ws]
    outer.sort(key=lambda t: np.arctan2(t[1], t[0]) if (t[0] or t[1]) else -9)
    hull = [tf(x, y) for x, y in outer if (abs(x) + abs(y) > 1e-9)]
    if len(hull) >= 3:
        c.polygon(hull, fill="none", stroke=_ACCENT, stroke_width=1.5, opacity=0.7)
    # weight points sized by multiplicity
    for w in ws:
        X, Y = tf(w["t3"], w["y"])
        for m in range(w["mult"]):
            c.circle(X, Y, 9 - 3 * m, fill=_POINT, stroke="#0b0e14", stroke_width=1.0)
    c.text(_SIZE / 2, _SIZE - 24,
           f"{title}  (Dynkin {p},{q})  dim {su3_dimension(p, q)}", size=15)
    c.text(_SIZE / 2, _SIZE - 8,
           "su(3) weight diagram — 2D projection of representation space",
           size=10, fill="#8b949e")
    return c


def root_system_svg(sacred: bool) -> SVGCanvas:
    roots = su3_root_system()
    pts = [(r["t3"], r["y"]) for r in roots]
    tf, scale = _fit(pts + [(0, 0)])
    c = SVGCanvas(_SIZE, _SIZE)
    if sacred:
        vesica_overlay(c, _SIZE / 2, _SIZE / 2, (_SIZE - 2 * _PAD) / 3)
    ox, oy = tf(0, 0)
    for r in roots:
        X, Y = tf(r["t3"], r["y"])
        c.line(ox, oy, X, Y, stroke=_ACCENT, stroke_width=1.5, opacity=0.6)
        c.circle(X, Y, 7, fill=_POINT, stroke="#0b0e14", stroke_width=1.0)
    c.circle(ox, oy, 4, fill="#e6edf3")
    c.text(_SIZE / 2, _SIZE - 20, "su(3) root system (A2) — 6 roots", size=15)
    return c


def cy_svg(n: int, n_grid: int, sacred: bool) -> SVGCanvas:
    patches = fermat_patches(n=n, n_grid=n_grid)
    proj = [(p, orthographic(p.grid3d)) for p in patches]
    allpts = [tuple(xy) for _, g in proj for row in g for xy in row]
    tf, scale = _fit(allpts)
    c = SVGCanvas(_SIZE, _SIZE)
    if sacred:
        golden_overlay(c, _SIZE / 2, _SIZE / 2, (_SIZE - 2 * _PAD) / 2)
    # colour patches by k1 for a little depth cue
    for patch, g in proj:
        hue = 200 + 24 * patch.k1
        col = f"hsl({hue % 360},70%,62%)"
        gi = g.shape[0]
        for i in range(gi):
            row = [tf(*g[i, j]) for j in range(g.shape[1])]
            c.polyline(row, stroke=col, stroke_width=0.8, opacity=0.55)
        for j in range(g.shape[1]):
            col2 = [tf(*g[i, j]) for i in range(gi)]
            c.polyline(col2, stroke=col, stroke_width=0.8, opacity=0.55)
    c.text(_SIZE / 2, _SIZE - 24,
           f"Calabi-Yau cross-section: Fermat z1^{n}+z2^{n}=1", size=15)
    c.text(_SIZE / 2, _SIZE - 8,
           "2D projection (R^4->R^3->R^2) of an exact algebraic surface",
           size=10, fill="#8b949e")
    return c


def su2_ladder_svg(dim: int, sacred: bool) -> SVGCanvas:
    ws = su2_weights(dim)
    pts = [(w["m"], 0.0) for w in ws]
    tf, scale = _fit(pts + [(0, 0)], pad=120)
    c = SVGCanvas(_SIZE, _SIZE)
    ax_y = _SIZE / 2
    c.line(_PAD, ax_y, _SIZE - _PAD, ax_y, stroke="#30363d")
    for w in ws:
        X, _ = tf(w["m"], 0.0)
        c.circle(X, ax_y, 10, fill=_POINT, stroke="#0b0e14", stroke_width=1.0)
        c.text(X, ax_y - 18, f"{w['m']:+.1f}", size=11, fill="#8b949e")
    c.text(_SIZE / 2, _SIZE - 24, f"su(2) weight ladder — spin j={(dim-1)/2:g} "
           f"(dim {dim})", size=15)
    c.text(_SIZE / 2, _SIZE - 8, "1D weights m = -j..+j", size=10, fill="#8b949e")
    return c


def suN_root_svg(N: int, sacred: bool) -> SVGCanvas:
    roots = suN_root_system_2d(N)
    pts = [(r["x"], r["y"]) for r in roots]
    tf, scale = _fit(pts + [(0, 0)])
    c = SVGCanvas(_SIZE, _SIZE)
    if sacred:
        vesica_overlay(c, _SIZE / 2, _SIZE / 2, (_SIZE - 2 * _PAD) / 3)
    ox, oy = tf(0, 0)
    for r in roots:
        X, Y = tf(r["x"], r["y"])
        c.line(ox, oy, X, Y, stroke=_ACCENT, stroke_width=1.2, opacity=0.5)
        c.circle(X, Y, 6, fill=_POINT, stroke="#0b0e14", stroke_width=1.0)
    c.circle(ox, oy, 4, fill="#e6edf3")
    c.text(_SIZE / 2, _SIZE - 20,
           f"su({N}) root system (A{N-1}) — {N*(N-1)} roots, 2D projection", size=15)
    return c


def lattice_wilson_svg(sacred: bool) -> SVGCanvas:
    lat = cubic_lattice(3, 3, 3)
    loop = wilson_loop(lat, (0, 0, 0), R=2, T=2, plane="xy")
    xy = lattice_project(lat.sites)
    allpts = [tuple(p) for p in xy]
    tf, scale = _fit(allpts)
    c = SVGCanvas(_SIZE, _SIZE)
    for (a, b) in lat.links:
        xa, ya = tf(*xy[a])
        xb, yb = tf(*xy[b])
        c.line(xa, ya, xb, yb, stroke="#30363d", stroke_width=0.8, opacity=0.7)
    loop_xy = [tf(*xy[i]) for i in loop]
    c.polyline(loop_xy, stroke=_POINT, stroke_width=3.0, opacity=0.95)
    for i in set(loop):
        X, Y = tf(*xy[i])
        c.circle(X, Y, 4, fill=_ACCENT, stroke="#0b0e14", stroke_width=1.0)
    c.text(_SIZE / 2, _SIZE - 24,
           "Lattice + Wilson loop — 3D grid projected to 2D", size=15)
    c.text(_SIZE / 2, _SIZE - 8,
           "highlighted closed path = a gauge-invariant Wilson loop (geometry only)",
           size=10, fill="#8b949e")
    return c


def hodge_diamond_svg(diamond, sacred: bool) -> SVGCanvas:
    c = SVGCanvas(_SIZE, _SIZE)
    n = diamond.complex_dim
    dy = (_SIZE - 2 * _PAD) / (2 * n)
    dx = dy
    cx = _SIZE / 2
    top = _PAD
    if sacred:
        golden_overlay(c, cx, top + n * dy, (_SIZE - 2 * _PAD) / 2)
    for (p, q), v in diamond.h.items():
        x = cx + (q - p) * dx
        y = top + (p + q) * dy
        c.circle(x, y, 16, fill="#161b22", stroke=_ACCENT, stroke_width=1.2,
                 opacity=0.9)
        c.text(x, y + 4, str(v), size=13, fill=_POINT)
    chi = diamond.euler_characteristic()
    c.text(cx, _SIZE - 34, f"{diamond.name}  Hodge diamond", size=15)
    c.text(cx, _SIZE - 16, f"Euler characteristic chi = {chi}   (Betti "
           f"{diamond.betti_numbers()})", size=10, fill="#8b949e")
    return c


def dynkin_svg(N: int, sacred: bool) -> SVGCanvas:
    d = dynkin_diagram_AN(N)
    c = SVGCanvas(_SIZE, 280)
    r = N - 1
    y = 140
    xs = [_PAD + i * (_SIZE - 2 * _PAD) / max(1, r - 1) for i in range(r)] if r > 1 \
        else [_SIZE / 2]
    for (a, b) in d["bonds"]:
        c.line(xs[a - 1], y, xs[b - 1], y, stroke=_ACCENT, stroke_width=2.0)
    for i, x in enumerate(xs, start=1):
        c.circle(x, y, 12, fill="#161b22", stroke=_POINT, stroke_width=2.0)
        c.text(x, y + 34, f"a{i}", size=12, fill="#8b949e")
    c.text(_SIZE / 2, 40, f"Dynkin diagram {d['type']} = {d['group']}", size=15)
    c.text(_SIZE / 2, 250, "simple roots chained by single bonds (Cartan A_{N-1})",
           size=10, fill="#8b949e")
    return c


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sacred-overlay", action="store_true",
                    help="add the decorative golden-ratio / Vesica overlay")
    ap.add_argument("--cy-n", type=int, default=5)
    ap.add_argument("--cy-grid", type=int, default=16)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "figures" / "geometry")
    args = ap.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    figs = {
        "su3_fundamental_weight.svg": weight_diagram_svg(1, 0, "fundamental 3", args.sacred_overlay),
        "su3_octet_weight.svg": weight_diagram_svg(1, 1, "octet 8", args.sacred_overlay),
        "su3_decuplet_weight.svg": weight_diagram_svg(3, 0, "decuplet 10", args.sacred_overlay),
        "su3_root_system.svg": root_system_svg(args.sacred_overlay),
        "su2_weight_ladder.svg": su2_ladder_svg(5, args.sacred_overlay),
        "su4_root_system.svg": suN_root_svg(4, args.sacred_overlay),
        "lattice_wilson_loop.svg": lattice_wilson_svg(args.sacred_overlay),
        "calabi_yau_cross_section.svg": cy_svg(args.cy_n, args.cy_grid, args.sacred_overlay),
        "calabi_yau_hodge_diamond.svg": hodge_diamond_svg(fermat_quintic_hodge(), args.sacred_overlay),
        "su4_dynkin_diagram.svg": dynkin_svg(4, args.sacred_overlay),
    }
    for name, canvas in figs.items():
        canvas.write(out / name)
        print(f"  wrote {out / name}")
    # Exact geometry data + verifiable symmetry invariants (Weyl closure, centroid).
    import json
    (out / "geometry_data.json").write_text(
        json.dumps(geometry_dataset(), indent=2, sort_keys=True))
    print(f"  wrote {out / 'geometry_data.json'}")
    # Discharged symmetry-invariant certificates (Lean/Coq) for the named irreps.
    certs = {}
    for nm, (p, q) in NAMED_IRREPS.items():
        cert = weight_symmetry_certificate(p, q)
        (out / f"weight_symmetry_{nm}.lean").write_text(cert.lean4)
        (out / f"weight_symmetry_{nm}.coq").write_text(cert.coq)
        certs[nm] = cert.to_dict()
    (out / "weight_symmetry_certificates.json").write_text(
        json.dumps(certs, indent=2, sort_keys=True))
    print(f"  wrote {len(certs)} symmetry certificates (.lean/.coq) + json")
    # Exact topology: Calabi-Yau Hodge diamond + A_{N-1} Cartan/Dynkin data.
    topo = {
        "calabi_yau_quintic": fermat_quintic_hodge().to_dict(),
        "dynkin": {f"su{N}": dynkin_diagram_AN(N) for N in (2, 3, 4, 5)},
    }
    (out / "topology_data.json").write_text(json.dumps(topo, indent=2, sort_keys=True))
    print(f"  wrote {out / 'topology_data.json'}")
    print(f"\n{len(figs)} figures + data + certificates -> {out}"
          + ("  (with decorative sacred-geometry overlay)" if args.sacred_overlay else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
