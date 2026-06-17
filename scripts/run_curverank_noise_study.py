#!/usr/bin/env python3
"""Noise study for quantum signal extraction.

Sweeps coherence-decay (dephasing) and shot budgets and measures how accurately
the eigenvalues of a CurveRank operator are recovered:

- QCELS dominant-eigenvalue error (Heisenberg-style, long coherent evolution);
- ESPRIT full-spectrum max error (super-resolution from the correlation signal).

All in exact/statevector mode with explicit noise envelopes -- deterministic and
hermetic. Writes a JSON table and an SVG to results/curverank-noise/.

CLAIM BOUNDARY: finite-operator method benchmark under modelled noise; extracted
eigenvalues are evidence cross-checked against the certified kernel, not a proof
of the Riemann Hypothesis.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import berry_keating_xp
from gaugegap import curverank_signal as cs
from gaugegap.plot_svg import write_line_svg


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n-basis", type=int, default=8)
    p.add_argument("--total-time", type=float, default=80.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output-dir", type=Path, default=ROOT / "results" / "curverank-noise")
    args = p.parse_args()

    H = berry_keating_xp(args.n_basis)
    w = np.linalg.eigvalsh(H)
    _, V = np.linalg.eigh(H)
    # Dominant-on-ground state plus minor components (a realistic prepared state).
    psi = V[:, 0] + 0.25 * (V[:, min(3, args.n_basis - 1)] + V[:, min(5, args.n_basis - 1)])
    psi = psi / np.linalg.norm(psi)
    ground = float(w[0])

    dephasings = [0.0, 0.01, 0.03, 0.1]
    shot_budgets = [None, 16384, 4096, 1024]

    rows = []
    for dp in dephasings:
        for sh in shot_budgets:
            q = cs.qcels(H, psi, total_time=args.total_time, shots=sh, dephasing=dp,
                         rng=np.random.default_rng(args.seed))
            qcels_err = abs(q.eigenvalue - ground)
            r = cs.extract_eigenvalues(H, psi, method="esprit", shots=sh, dephasing=dp,
                                       rng=np.random.default_rng(args.seed + 1))
            est = np.sort(r.eigenvalues)
            esprit_err = max(min(abs(t - e) for e in est) for t in w) if est.size else float("nan")
            rows.append({
                "dephasing": dp, "shots": sh,
                "qcels_ground_error": qcels_err,
                "esprit_max_error": float(esprit_err),
            })
            print(f"dephasing={dp:<5} shots={str(sh):<6} | QCELS ground err={qcels_err:.2e} "
                  f"| ESPRIT max err={esprit_err:.2e}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "curverank-noise-study.json").write_text(json.dumps({
        "claim_boundary": (
            "Finite-operator method benchmark under modelled dephasing/shot noise; "
            "extracted eigenvalues are evidence validated against the certified "
            "kernel, not a proof of the Riemann Hypothesis."
        ),
        "n_basis": args.n_basis, "total_time": args.total_time,
        "ground_eigenvalue": ground, "rows": rows,
    }, indent=2), encoding="utf-8")

    # QCELS ground-state error vs shots, one line per dephasing level.
    series = {}
    for dp in dephasings:
        pts = [(i, r["qcels_ground_error"])
               for i, r in enumerate(rows) if r["dephasing"] == dp]
        series[f"dephasing={dp}"] = pts
    write_line_svg(
        args.output_dir / "curverank-noise-qcels.svg", series,
        title="QCELS ground-state error vs shot setting (per dephasing level)",
        x_label="shot setting index (exact, 16384, 4096, 1024)",
        y_label="abs error",
    )
    print(f"report -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
