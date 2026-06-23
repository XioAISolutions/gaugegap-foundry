#!/usr/bin/env python3
"""Cherenkov radiation: the certified "local speed limit" and its cone.

A charged particle faster than light-in-medium (beta > 1/n) outruns the spherical
wavefronts it emits; they pile into a cone with cos(theta_c) = 1/(n beta). This
simulates the wavefront pile-up, recovers the cone angle from the point cloud, verifies
the closed form, and emits a discharged Lean 4 / Coq certificate that the cone cosine
is valid at/above threshold.

CLAIM BOUNDARY: a finite, exact EM/geometry demonstration of the Cherenkov principle;
NOT a detector reproduction; the spectral "blue" weighting is not modelled. The cone
relation and threshold are exact theorems.
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.cherenkov import analyze_cherenkov, cone_angle
from gaugegap.visualization.svg import SVGCanvas


def _plot_cone(path, n, beta, t_obs=1.0, n_sources=24):
    """The wavefront pile-up: emitted spheres (circles) + the Cherenkov cone."""
    W = H = 520; pad = 50
    c = SVGCanvas(W, H)
    x_apex = beta * t_obs
    span = max(x_apex, (t_obs) / n) * 1.1 or 1.0
    def tf(x, y):
        sx = pad + (x / span) * (W - 2 * pad)
        sy = H / 2 - (y / span) * (W - 2 * pad)
        return sx, sy
    # wavefront circles
    for tk in np.linspace(0, t_obs, n_sources):
        r = (t_obs - tk) / n
        if r <= 0:
            continue
        xc = beta * tk
        pts = [tf(xc + r * np.cos(a), r * np.sin(a))
               for a in np.linspace(0, 2 * np.pi, 80)]
        c.polyline(pts, stroke="#58a6ff", stroke_width=0.8, opacity=0.5)
    # cone lines from apex
    theta = cone_angle(n, beta)
    if theta is not None:
        alpha = np.pi / 2 - theta  # half-angle from axis
        L = span
        for sgn in (+1, -1):
            x2 = x_apex - L * np.cos(alpha)
            y2 = sgn * L * np.sin(alpha)
            ax, ay = tf(x_apex, 0.0); bx, by = tf(x2, y2)
            c.line(ax, ay, bx, by, stroke="#f0c674", stroke_width=2.0)
    c.circle(*tf(x_apex, 0.0), 4.0, fill="#f0c674")
    c.text(W / 2, 26, f"Cherenkov cone  n={n}  beta={beta}", size=14)
    c.text(W / 2, H - 16, f"cos(theta_c)=1/(n beta)={1/(n*beta):.3f}", size=11,
           fill="#8b949e")
    c.write(path)


def _plot_angle_vs_beta(path, n):
    W = H = 480; pad = 60
    c = SVGCanvas(W, H)
    betas = np.linspace(1.0 / n, 1.0, 200)
    angs = np.array([np.degrees(cone_angle(n, b) or 0.0) for b in betas])
    amax = angs.max() or 1.0
    def tf(b, a):
        x = pad + (b - 1.0 / n) / (1.0 - 1.0 / n) * (W - 2 * pad)
        return x, (H - pad) - a / amax * (H - 2 * pad)
    c.line(pad, H - pad, W - pad, H - pad, stroke="#30363d")
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    c.polyline([tf(b, a) for b, a in zip(betas, angs)], stroke="#7ee787",
               stroke_width=2.0)
    c.text(W / 2, 26, f"Cherenkov angle vs beta  (n={n})", size=14)
    c.text(W / 2, H - 20, "beta from threshold 1/n -> 1   (theta_c grows)", size=11,
           fill="#8b949e")
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=float, default=1.33, help="refractive index")
    ap.add_argument("--beta", type=float, default=0.9, help="particle speed (v/c)")
    ap.add_argument("--n-sources", type=int, default=400)
    ap.add_argument("--n-phi", type=int, default=720)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "cherenkov")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    r = analyze_cherenkov(args.n, args.beta, n_sources=args.n_sources, n_phi=args.n_phi)
    print("=" * 72)
    print("Cherenkov radiation — local speed limit & cone geometry")
    print("=" * 72)
    print(f"  medium index n            : {r.n}")
    print(f"  particle speed beta       : {r.beta} (threshold 1/n = {r.threshold_beta:.3f})")
    print(f"  emits Cherenkov light     : {r.emits}")
    print(f"  cos(theta_c) = 1/(n beta) : {r.cos_theta_c:.4f}  -> theta_c = "
          f"{r.theta_c_deg:.2f} deg")
    print(f"  recovered from wavefronts : {r.cos_theta_c_recovered:.4f}  "
          f"(err {r.recovery_error:.1e})")
    print(f"  cone cosine valid         : {r.cone_valid}")

    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    payload = dict(r.to_dict())
    payload["lean4_certificate"] = r.lean4
    payload["coq_certificate"] = r.coq
    (out / "cherenkov.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    (out / "cherenkov_cone.lean").write_text(r.lean4)
    (out / "cherenkov_cone.coq").write_text(r.coq)
    _plot_cone(out / "cherenkov_cone.svg", args.n, args.beta)
    _plot_angle_vs_beta(out / "angle_vs_beta.svg", args.n)

    holes = ("sorry" in r.lean4) or ("Admitted" in r.coq)
    (out / "cherenkov.md").write_text(
        "# Cherenkov radiation: local speed limit & cone\n\n"
        "A charged particle faster than light-in-medium (`beta > 1/n`) outruns the "
        "spherical wavefronts it emits, which pile into a cone with "
        "`cos(theta_c) = 1/(n beta)` -- the velocity<->geometry edge of the "
        "physical-limits web (a local speed limit c/n with an exact geometric "
        "signature). The wavefront pile-up is simulated and the cone angle recovered "
        f"from the point cloud to err {r.recovery_error:.1e}; a discharged Lean 4 / Coq "
        "certificate proves the cone cosine is valid (`0 < cos theta_c <= 1`) at/above "
        "threshold. **Claim boundary:** a finite exact EM/geometry demo; NOT a detector "
        "reproduction (RICH / Super-Kamiokande) and the spectral 'blue' weighting is "
        "not modelled; the cone relation and threshold are exact theorems. Not a "
        "continuum/Millennium claim.\n\n"
        f"- threshold beta = 1/n = **{r.threshold_beta:.3f}**; emits = **{r.emits}**\n"
        f"- cos(theta_c) = 1/(n beta) = **{r.cos_theta_c:.4f}** -> theta_c = "
        f"**{r.theta_c_deg:.2f} deg**\n"
        f"- recovered from wavefronts = **{r.cos_theta_c_recovered:.4f}** "
        f"(err {r.recovery_error:.1e}); certificate hole-free = **{not holes}**\n\n"
        "![cherenkov cone](cherenkov_cone.svg)\n\n"
        "![angle vs beta](angle_vs_beta.svg)\n\n"
        "_Generated by `scripts/run_cherenkov.py`._\n")
    print(f"\nReport: {out / 'cherenkov.json'} (+ .md, .svg, .lean, .coq)")
    print(f"  certificate hole-free: {not holes}")

    if not args.skip_audit:
        import subprocess
        rel = (out / "cherenkov.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if (r.cone_valid and not holes and r.recovery_error < 1e-2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
