#!/usr/bin/env python3
"""Lieb-Robinson light cone: a certified many-body speed limit for information.

Evolves a centre excitation on a hopping chain (a continuous-time quantum walk on a
path graph), measures the information front vs time, confirms it respects the linear
light cone x(t) <= v_LR t + xi (v_LR = e|J| for tight binding), and emits a discharged
Lean 4 / Coq certificate. Also cross-checks the evolution against the (previously
dormant) quantum_walks CTQW.

CLAIM BOUNDARY: a finite, exact lattice demonstration for a free-hopping model (where
v_LR = e|J| is the rigorous Bessel-bound velocity); not the general interacting LR
constant. Dependency-light (numpy core; optional SciPy cross-check).
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.lieb_robinson import analyze_lieb_robinson
from gaugegap.visualization.svg import SVGCanvas


def _plot(path, r):
    W = H = 520; pad = 60
    c = SVGCanvas(W, H)
    tmax = max(r.times) or 1.0
    xmax = max(max(r.fronts), r.v_lr * tmax) * 1.1 or 1.0
    def tf(t, x):
        return (pad + t / tmax * (W - 2 * pad), (H - pad) - x / xmax * (H - 2 * pad))
    c.line(pad, H - pad, W - pad, H - pad, stroke="#30363d")
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    # the LR cone v_LR * t and the group-velocity line 2J t
    c.line(*tf(0, 0), *tf(tmax, r.v_lr * tmax), stroke="#f0c674", stroke_width=1.6,
           opacity=0.9)
    c.line(*tf(0, 0), *tf(tmax, r.group_velocity * tmax), stroke="#8b949e",
           stroke_width=1.0, opacity=0.6)
    c.polyline([tf(t, x) for t, x in zip(r.times, r.fronts)], stroke="#58a6ff",
               stroke_width=2.0)
    for t, x in zip(r.times, r.fronts):
        c.circle(*tf(t, x), 3.0, fill="#58a6ff")
    c.text(W / 2, 26, "Lieb-Robinson light cone", size=14)
    c.text(W / 2, H - 20, "blue: info front   gold: v_LR t   grey: group 2J t",
           size=11, fill="#8b949e")
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-sites", type=int, default=41)
    ap.add_argument("--J", type=float, default=1.0, help="hopping amplitude")
    ap.add_argument("--threshold", type=float, default=1e-3)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "lieb-robinson")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    r = analyze_lieb_robinson(n_sites=args.n_sites, J=args.J, threshold=args.threshold)
    print("=" * 72)
    print("Lieb-Robinson light cone — many-body speed limit for information")
    print("=" * 72)
    print(f"  chain sites / hopping J   : {r.n_sites} / {r.J}")
    print(f"  group velocity 2J         : {r.group_velocity:.3f}")
    print(f"  Lieb-Robinson v_LR = eJ   : {r.v_lr:.3f}")
    print(f"  fitted front velocity     : {r.front_velocity:.3f}  (<= v_LR)")
    print(f"  respects linear cone      : {r.respects_cone}")
    xc = r.crosscheck_error
    print(f"  quantum_walks cross-check : "
          f"{'max|diff|=%.1e' % xc if xc is not None else 'skipped (no SciPy)'}")

    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    payload = dict(r.to_dict())
    payload["times"] = r.times
    payload["fronts"] = r.fronts
    payload["lean4_certificate"] = r.lean4
    payload["coq_certificate"] = r.coq
    (out / "lieb-robinson.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    (out / "light_cone.lean").write_text(r.lean4)
    (out / "light_cone.coq").write_text(r.coq)
    _plot(out / "light_cone.svg", r)

    holes = ("sorry" in r.lean4) or ("Admitted" in r.coq)
    (out / "lieb-robinson.md").write_text(
        "# Lieb-Robinson light cone\n\n"
        "A many-body speed limit: with local interactions, information stays inside a "
        "linear light cone `x(t) <= v_LR t + xi`. On a hopping chain (a continuous-time "
        "quantum walk on a path graph) the rigorous tight-binding velocity is "
        f"`v_LR = e|J| = {r.v_lr:.3f}` (it bounds even the leading Bessel tail; the "
        f"visible group front moves at `2J = {r.group_velocity}`). The measured front "
        f"velocity is **{r.front_velocity:.3f}** and respects the cone "
        f"(**{r.respects_cone}**); the evolution is cross-checked against the "
        "(previously dormant) `quantum_walks` CTQW to "
        f"{('%.0e' % r.crosscheck_error) if r.crosscheck_error is not None else 'n/a'}. "
        "A discharged Lean 4 / Coq certificate proves the linear cone "
        "`vf <= v_LR, t >= 0 => vf t <= v_LR t`. **Claim boundary:** a finite exact "
        "lattice demo for a free-hopping model (v_LR = e|J| exact); not the general "
        "interacting LR constant. Not a continuum/Millennium claim.\n\n"
        f"- v_LR = e|J| = **{r.v_lr:.3f}**, group 2J = {r.group_velocity}, fitted front "
        f"= **{r.front_velocity:.3f}**\n"
        f"- respects linear cone = **{r.respects_cone}**, certificate hole-free = "
        f"**{not holes}**\n\n"
        "![light cone](light_cone.svg)\n\n"
        "_Generated by `scripts/run_lieb_robinson.py`._\n")
    print(f"\nReport: {out / 'lieb-robinson.json'} (+ .md, .svg, .lean, .coq)")
    print(f"  certificate hole-free: {not holes}")

    if not args.skip_audit:
        import subprocess
        rel = (out / "lieb-robinson.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if (r.respects_cone and not holes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
