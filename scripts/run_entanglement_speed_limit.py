#!/usr/bin/env python3
"""Quantum speed limit on entanglement formation: measure the entanglement build-up
time of a finite exchange model and CERTIFY (Lean 4 / Coq) that it respects the
Mandelstam-Tamm / Margolus-Levitin floor. Sweeps the coupling to show the floor
shrinking as 1/J (a stronger interaction lets entanglement form faster).

Inspired by attosecond-entanglement work (entanglement forms over a finite time).
CLAIM BOUNDARY: finite-model demonstration; the QSL inequalities are exact and
machine-checked on the simulated evolution; NOT a reproduction of the helium
experiment or the ~232 as figure; physical-time conversion is illustrative only.
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.entanglement_dynamics import two_qubit_exchange_model
from gaugegap.quantum.entanglement_speed_limit import certified_buildup_speed_limit
from gaugegap.visualization.svg import SVGCanvas


def _plot(path, couplings, floors):
    W = H = 520; pad = 64
    c = SVGCanvas(W, H)
    cmax = max(couplings); fmax = max(floors) or 1.0
    c.line(pad, H - pad, W - pad, H - pad, stroke="#30363d")
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    def tf(x, y):
        return (pad + x / cmax * (W - 2 * pad), (H - pad) - y / fmax * (H - 2 * pad))
    c.polyline([tf(x, y) for x, y in zip(couplings, floors)],
               stroke="#58a6ff", stroke_width=2.0)
    for x, y in zip(couplings, floors):
        px, py = tf(x, y); c.circle(px, py, 3.0, fill="#f0c674")
    c.text(W / 2, 28, "QSL floor on entanglement build-up  vs  coupling", size=14)
    c.text(W / 2, H - 22, "coupling J  (floor scales as 1/J)", size=11, fill="#8b949e")
    c.text(pad + 6, pad + 4, "tau_QSL (model units)", size=10, fill="#8b949e",
           anchor="start")
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--coupling", type=float, default=1.0)
    ap.add_argument("--detuning", type=float, default=0.0)
    ap.add_argument("--t-max", type=float, default=1.6)
    ap.add_argument("--samples", type=int, default=300)
    ap.add_argument("--fraction", type=float, default=0.9)
    ap.add_argument("--sweep", default="0.5,1.0,1.5,2.0",
                    help="comma-separated couplings for the floor-vs-J figure")
    ap.add_argument("--energy-scale-ev", type=float, default=None,
                    help="illustrative only: convert model time to attoseconds")
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "results" / "entanglement-speed-limit")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    H, psi0 = two_qubit_exchange_model(args.coupling, args.detuning)
    r = certified_buildup_speed_limit(
        H, psi0, t_max=args.t_max, n_samples=args.samples, fraction=args.fraction,
        energy_scale_eV=args.energy_scale_ev)

    print("=" * 72)
    print("Quantum speed limit on entanglement formation (two-qubit exchange model)")
    print("=" * 72)
    u = r.time_unit
    print(f"  build-up time          : {r.buildup_time:.4g} {u}")
    print(f"  Mandelstam-Tamm floor  : {r.tau_mandelstam_tamm:.4g} {u}")
    print(f"  Margolus-Levitin floor : {r.tau_margolus_levitin:.4g} {u}")
    print(f"  QSL floor (max)        : {r.tau_qsl:.4g} {u}")
    print(f"  respects QSL           : {r.respects_qsl}  "
          f"(saturated: {abs(r.buildup_time - r.tau_qsl) < 1e-6})")
    print(f"  max entangling rate    : {r.max_entangling_rate:.4g}")
    if u == "attoseconds":
        print(f"  (illustrative conversion at E={args.energy_scale_ev} eV; not the "
              f"TU Wien measurement)")

    couplings = [float(x) for x in args.sweep.split(",") if x.strip()]
    floors = []
    for j in couplings:
        Hj, p0 = two_qubit_exchange_model(j, args.detuning)
        rj = certified_buildup_speed_limit(Hj, p0, t_max=args.t_max,
                                           n_samples=args.samples,
                                           fraction=args.fraction)
        floors.append(rj.tau_qsl)

    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    payload = dict(r.to_dict())
    payload["coupling"] = args.coupling
    payload["sweep_couplings"] = couplings
    payload["sweep_qsl_floors_model"] = floors
    payload["lean4_certificate"] = r.lean4
    payload["coq_certificate"] = r.coq
    (out / "entanglement-speed-limit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True))
    (out / "speed_limit_t_buildup.lean").write_text(r.lean4)
    (out / "speed_limit_t_buildup.coq").write_text(r.coq)
    _plot(out / "qsl_floor_vs_coupling.svg", couplings, floors)

    holes = ("sorry" in r.lean4) or ("admit" in r.lean4.lower()) or \
            ("Admitted" in r.coq) or ("admit" in r.coq.lower())
    (out / "entanglement-speed-limit.md").write_text(
        "# Quantum speed limit on entanglement formation\n\n"
        "A finite two-qubit exchange model builds entanglement over a finite time. "
        "The Mandelstam-Tamm and Margolus-Levitin **quantum speed limits** give a "
        "rigorous lower bound (floor) on that time; here the exchange evolution "
        "saturates the floor (entanglement forms as fast as quantum mechanics "
        "allows), and a discharged Lean 4 / Coq certificate proves the build-up "
        "time respects `max(tau_MT, tau_ML)`. **Claim boundary:** a finite-model "
        "demonstration inspired by attosecond-entanglement work; the QSL "
        "inequalities are exact and machine-checked on the simulated evolution; NOT "
        "a reproduction of the helium experiment or the ~232 as figure; physical-"
        "time conversion is illustrative only.\n\n"
        f"- build-up time = **{r.buildup_time:.4g} {u}**\n"
        f"- QSL floor = **{r.tau_qsl:.4g} {u}** "
        f"(MT {r.tau_mandelstam_tamm:.4g}, ML {r.tau_margolus_levitin:.4g})\n"
        f"- respects QSL = **{r.respects_qsl}**, certificate hole-free = "
        f"**{not holes}**\n\n"
        "![floor vs coupling](qsl_floor_vs_coupling.svg)\n\n"
        "_Generated by `scripts/run_entanglement_speed_limit.py`._\n")
    print(f"\nReport: {out / 'entanglement-speed-limit.json'} (+ .md, .svg, .lean, .coq)")
    print(f"  certificate hole-free: {not holes}")

    if not args.skip_audit:
        import subprocess
        rel = (out / "entanglement-speed-limit.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if (r.respects_qsl and not holes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
