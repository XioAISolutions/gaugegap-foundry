#!/usr/bin/env python3
"""Alcubierre warp-drive metric: certify the negative-energy requirement.

Computes the exact Eulerian energy density of the Alcubierre (1994) warp metric,
shows it is negative everywhere the bubble wall has a gradient (the weak energy
condition is violated -- the metric REQUIRES exotic/negative energy, concentrated
in a torus: the "ring of negative energy density"), and emits a discharged Lean 4 /
Coq certificate of rho <= 0. Reports the Ford-Roman quantum-inequality floor as the
standard QFT obstruction.

The GR/QFT sibling of the quantum speed limit: a rigorous bound-from-physics.

CLAIM BOUNDARY: classical-GR + semiclassical-QFT analysis of a toy metric. NOT a
buildable warp drive and NOT a claim that faster-than-light travel is achievable.
The energy-condition violation is exact and machine-checked; the quantum-inequality
obstruction is the standard literature result (Pfenning & Ford 1997).
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.relativity.alcubierre import analyze_warp_bubble, energy_density
from gaugegap.visualization.svg import SVGCanvas


def _plot(path, v_s, R, sigma):
    """Energy-density profile rho(x) at a fixed off-axis offset: two negative wells
    at the front/back bubble walls (contract ahead, expand behind)."""
    W = H = 520; pad = 64
    xs = np.linspace(-(R + 2.0), R + 2.0, 400)
    rho = np.array([float(energy_density(x, 0.35, 0.0, v_s=v_s, R=R, sigma=sigma))
                    for x in xs])
    c = SVGCanvas(W, H)
    xmax = xs.max(); rmin = rho.min() or -1.0
    zero_y = pad + (H - 2 * pad) * 0.15            # zero line near the top
    def tf(x, r):
        px = pad + (x - xs.min()) / (xmax - xs.min()) * (W - 2 * pad)
        py = zero_y + (r / rmin) * (H - pad - zero_y)
        return (px, py)
    c.line(pad, zero_y, W - pad, zero_y, stroke="#8b949e", stroke_width=1.0, opacity=0.6)
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    c.polyline([tf(x, r) for x, r in zip(xs, rho)], stroke="#58a6ff", stroke_width=2.0)
    c.text(W / 2, 28, "Alcubierre energy density  rho(x)  (off-axis)", size=14)
    c.text(W / 2, H - 22, "x along travel direction  -  negative wells = bubble walls",
           size=11, fill="#8b949e")
    c.text(pad + 6, int(zero_y) - 8, "rho = 0", size=10, fill="#8b949e", anchor="start")
    c.text(pad + 6, H - pad - 6, "rho < 0  (WEC violated)", size=10, fill="#f0c674",
           anchor="start")
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--v-s", type=float, default=1.0, help="bubble velocity (c=1)")
    ap.add_argument("--R", type=float, default=1.0, help="bubble radius")
    ap.add_argument("--sigma", type=float, default=8.0, help="wall steepness (1/width)")
    ap.add_argument("--extent", type=float, default=2.5)
    ap.add_argument("--n-grid", type=int, default=70)
    ap.add_argument("--sampling-time", type=float, default=None,
                    help="Ford-Roman sampling time (default: wall thickness 1/sigma)")
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "alcubierre-warp")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    a = analyze_warp_bubble(v_s=args.v_s, R=args.R, sigma=args.sigma,
                            extent=args.extent, n_grid=args.n_grid,
                            sampling_time=args.sampling_time)

    print("=" * 72)
    print("Alcubierre warp metric -- energy-condition analysis")
    print("=" * 72)
    print(f"  v_s={a.v_s}  R={a.R}  sigma={a.sigma} (wall ~ {1/a.sigma:.3g})")
    print(f"  min energy density rho_min : {a.rho_min:.4e}")
    print(f"  weak energy condition      : {'VIOLATED' if a.wec_violated else 'ok'} "
          f"(rho < 0 required -> needs negative energy)")
    print(f"  negative energy concentrates in a ring at radius ~ {a.ring_radius:.3g}")
    print(f"  total negative energy      : {a.total_negative_energy:.4e} (geometric units)")
    print(f"  Ford-Roman allowed |rho|   : {a.ford_roman_allowed_magnitude:.4e} "
          f"(sampling tau={a.ford_roman_sampling_time:.3g})")
    print(f"  required/allowed (toy units): {a.quantum_inequality_violation_factor:.3e}")
    print("  NOTE: the dramatic QI violation is a MACROSCOPIC result (Pfenning-Ford "
          "1997);")
    print("        in these dimensionless units it is illustrative only.")

    rows = []
    for v in (1.0, 2.0, 4.0):
        av = analyze_warp_bubble(v_s=v, R=args.R, sigma=args.sigma,
                                 extent=args.extent, n_grid=args.n_grid)
        rows.append((v, av.total_negative_energy))
    print("  scaling E_neg ~ v_s^2:  " +
          "  ".join(f"v={v}:{e:.2e}" for v, e in rows))

    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    payload = dict(a.to_dict())
    payload["scaling_v_s_total_negative_energy"] = rows
    payload["lean4_certificate"] = a.lean4
    payload["coq_certificate"] = a.coq
    (out / "alcubierre-warp.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    (out / "warp_energy_condition.lean").write_text(a.lean4)
    (out / "warp_energy_condition.coq").write_text(a.coq)
    _plot(out / "energy_density_profile.svg", args.v_s, args.R, args.sigma)

    holes = ("sorry" in a.lean4) or ("Admitted" in a.coq)
    (out / "alcubierre-warp.md").write_text(
        "# Alcubierre warp metric: certified negative-energy requirement\n\n"
        "The Alcubierre (1994) warp bubble contracts space ahead and expands it "
        "behind a craft. Its exact Eulerian energy density is "
        "`rho = -(1/(8 pi)) (v_s^2 (y^2+z^2)/(4 r_s^2)) f'(r_s)^2`, which is "
        "`-(non-negative) x (square)` and therefore **<= 0 everywhere** -- the weak "
        "energy condition is violated for any bubble parameters, so the drive "
        "**requires negative energy**, concentrated in a torus (the \"ring of "
        "negative energy density\"). A discharged Lean 4 / Coq certificate proves "
        "`rho <= 0` from the two non-negativity facts. **Claim boundary:** a "
        "classical-GR + semiclassical-QFT analysis of a toy metric; NOT a buildable "
        "warp drive and NOT a claim that faster-than-light travel is achievable; the "
        "energy-condition violation is exact and machine-checked; the quantum-"
        "inequality obstruction is the standard literature result (Pfenning & Ford "
        "1997). Not a continuum/Millennium claim.\n\n"
        f"- min energy density = **{a.rho_min:.4e}**, WEC violated = "
        f"**{a.wec_violated}**\n"
        f"- negative-energy ring radius ~ **{a.ring_radius:.3g}** (= bubble wall)\n"
        f"- total negative energy = **{a.total_negative_energy:.4e}** (geometric "
        f"units), scales as v_s^2\n"
        f"- Ford-Roman allowed |rho| = {a.ford_roman_allowed_magnitude:.4e} at "
        f"sampling tau = {a.ford_roman_sampling_time:.3g}\n"
        f"- certificate hole-free = **{not holes}**\n\n"
        "![rho(x)](energy_density_profile.svg)\n\n"
        "_Generated by `scripts/run_alcubierre_warp.py`._\n")
    print(f"\nReport: {out / 'alcubierre-warp.json'} (+ .md, .svg, .lean, .coq)")
    print(f"  certificate hole-free: {not holes}")

    if not args.skip_audit:
        import subprocess
        rel = (out / "alcubierre-warp.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if (a.wec_violated and not holes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
