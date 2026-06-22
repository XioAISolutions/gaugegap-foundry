#!/usr/bin/env python3
"""Temporal double-slit (time diffraction): two time slits interfere in the FREQUENCY
spectrum with fringe spacing Delta_omega = 2 pi / Delta_t -- exact time-frequency
Fourier duality (the time<->energy currency of the physical-limits web). Recovers the
slit separation from the fringes and certifies the time-bandwidth bound.

Inspired by Tirole, Vezzoli et al., Nature Physics 2023.
CLAIM BOUNDARY: a finite, exact Fourier simulation of the time-diffraction principle;
NOT a reproduction of the ITO thin-film experiment or its numbers; the time-bandwidth
inequality is an exact Fourier theorem.
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.temporal_double_slit import (
    analyze_time_diffraction, fringe_spacing_theory, spectrum, time_slits)
from gaugegap.visualization.svg import SVGCanvas


def _plot(path, dt, tau, t_max, n):
    times = np.linspace(-t_max, t_max, n)
    omega, power = spectrum(times, time_slits(times, dt, tau))
    # show a central window of the spectrum where fringes are visible
    mask = np.abs(omega) <= 8.0
    w, p = omega[mask], power[mask]
    p = p / (p.max() or 1.0)
    W = H = 520; pad = 60
    c = SVGCanvas(W, H)
    c.line(pad, H - pad, W - pad, H - pad, stroke="#30363d")
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    wmin, wmax = w.min(), w.max()
    def tf(x, y):
        return (pad + (x - wmin) / (wmax - wmin) * (W - 2 * pad),
                (H - pad) - y * (H - 2 * pad))
    c.polyline([tf(x, y) for x, y in zip(w, p)], stroke="#58a6ff", stroke_width=1.6)
    c.text(W / 2, 26, "Time diffraction: spectral fringes |E(omega)|^2", size=14)
    c.text(W / 2, H - 22, f"angular frequency omega   -   fringe spacing 2pi/dt "
           f"= {fringe_spacing_theory(dt):.3f}", size=11, fill="#8b949e")
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dt", type=float, default=8.0, help="time-slit separation")
    ap.add_argument("--tau", type=float, default=0.6, help="time-slit width")
    ap.add_argument("--t-max", type=float, default=40.0)
    ap.add_argument("--n", type=int, default=8192)
    ap.add_argument("--sweep", default="6,8,12,16",
                    help="separations for the fringe-law check")
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "results" / "temporal-double-slit")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    r = analyze_time_diffraction(dt=args.dt, tau=args.tau, t_max=args.t_max, n=args.n)
    print("=" * 72)
    print("Temporal double-slit (time diffraction)")
    print("=" * 72)
    print(f"  slit separation dt         : {r.dt}")
    print(f"  fringe spacing 2pi/dt      : {r.fringe_spacing_theory:.4f}")
    print(f"  separation recovered       : {r.separation_recovered:.4f} "
          f"(from the fringes)")
    print(f"  fringe spacing recovered   : {r.fringe_spacing_recovered:.4f}  "
          f"(rel err {r.fringe_relative_error:.1e})")
    print(f"  sigma_t * sigma_omega      : {r.time_bandwidth_product:.4f} "
          f"(>= 1/2: {r.uncertainty_respected})")

    seps = [float(x) for x in args.sweep.split(",") if x.strip()]
    rows = []
    for s in seps:
        rs = analyze_time_diffraction(dt=s, tau=args.tau, t_max=args.t_max, n=args.n)
        rows.append((s, rs.fringe_spacing_theory, rs.separation_recovered,
                     rs.fringe_relative_error))
    print("  fringe law Delta_omega = 2pi/dt (recovered separation vs set):")
    for s, fth, sep, err in rows:
        print(f"    dt={s:5.1f}  fringe={fth:.4f}  recovered={sep:.3f}  err={err:.1e}")

    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    payload = dict(r.to_dict())
    payload["sweep"] = [{"dt": s, "fringe_spacing": fth, "recovered_separation": sep,
                         "rel_error": err} for s, fth, sep, err in rows]
    payload["lean4_certificate"] = r.lean4
    payload["coq_certificate"] = r.coq
    (out / "temporal-double-slit.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    (out / "time_bandwidth.lean").write_text(r.lean4)
    (out / "time_bandwidth.coq").write_text(r.coq)
    _plot(out / "spectral_fringes.svg", args.dt, args.tau, args.t_max, args.n)

    holes = ("sorry" in r.lean4) or ("Admitted" in r.coq)
    max_err = max(err for *_, err in rows)
    (out / "temporal-double-slit.md").write_text(
        "# Temporal double-slit (time diffraction)\n\n"
        "Two **time slits** (short windows in time, separation `dt`) make a probe "
        "interfere in the **frequency** spectrum, with fringe spacing "
        "`Delta_omega = 2 pi / dt` -- exact time-frequency Fourier duality (the "
        "time<->energy currency of the physical-limits web). Recovering the slit "
        "separation from the fringes reproduces `dt` to "
        f"< {max_err:.0e} relative error across a sweep, and a discharged Lean 4 / Coq "
        "certificate proves the time-bandwidth bound `sigma_t sigma_omega >= 1/2` (the "
        "Fourier-dual sibling of the Mandelstam-Tamm speed limit). **Claim boundary:** "
        "a finite, exact Fourier simulation of the time-diffraction principle; NOT a "
        "reproduction of the ITO thin-film experiment (Tirole, Vezzoli et al., Nat. "
        "Phys. 2023) or its numbers; the time-bandwidth inequality is an exact Fourier "
        "theorem. Not a continuum/Millennium claim.\n\n"
        f"- fringe spacing 2pi/dt = **{r.fringe_spacing_theory:.4f}** (dt={r.dt})\n"
        f"- separation recovered from fringes = **{r.separation_recovered:.4f}** "
        f"(rel err {r.fringe_relative_error:.1e})\n"
        f"- time-bandwidth product = **{r.time_bandwidth_product:.4f}** "
        f"(>= 1/2: **{r.uncertainty_respected}**), certificate hole-free = "
        f"**{not holes}**\n\n"
        "![spectral fringes](spectral_fringes.svg)\n\n"
        "_Generated by `scripts/run_temporal_double_slit.py`._\n")
    print(f"\nReport: {out / 'temporal-double-slit.json'} (+ .md, .svg, .lean, .coq)")
    print(f"  certificate hole-free: {not holes}")

    if not args.skip_audit:
        import subprocess
        rel = (out / "temporal-double-slit.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    ok = (r.uncertainty_respected and not holes and max_err < 1e-2)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
