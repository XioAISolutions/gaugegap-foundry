#!/usr/bin/env python3
"""Extract eigenvalues of a CurveRank operator from its quantum correlation signal
and validate them against the certified interval enclosures.

Demonstrates the time-series / super-resolution route (Hadamard test -> g(t) ->
Prony/ESPRIT) as a NISQ-friendly complement to QPE. Exact (statevector) mode by
default; pass --shots for sampled Hadamard-test estimation.

CLAIM BOUNDARY: finite-operator spectral screening + method benchmark. The
extracted eigenvalues are evidence cross-checked against the certified kernel;
nothing here is a proof of the Riemann Hypothesis.
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
from gaugegap.curverank_certified import certified_xp_spectrum
from gaugegap import curverank_signal as cs


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n-basis", type=int, default=8)
    p.add_argument("--method", choices=["prony", "esprit"], default="esprit")
    p.add_argument("--shots", type=int, default=None,
                   help="sampled Hadamard test; omit for exact mode")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output-dir", type=Path, default=ROOT / "results" / "curverank-signal")
    args = p.parse_args()

    H = berry_keating_xp(args.n_basis)
    rng = np.random.default_rng(args.seed)
    psi = rng.standard_normal(args.n_basis) + 1j * rng.standard_normal(args.n_basis)
    psi /= np.linalg.norm(psi)

    res = cs.extract_eigenvalues(H, psi, method=args.method, shots=args.shots,
                                 rng=np.random.default_rng(args.seed + 1))
    enclosures = certified_xp_spectrum(args.n_basis)
    report = cs.validate_against_certified(res.eigenvalues, enclosures)
    n_in = sum(r["in_certified_enclosure"] for r in report)

    print(f"CurveRank signal extraction: xp n={args.n_basis} method={args.method} "
          f"mode={'shots=%d' % args.shots if args.shots else 'exact'}")
    print(f"  recovered {len(res.eigenvalues)} modes over {res.n_times} samples "
          f"(dt={res.dt:.4f})")
    print(f"  in certified enclosure: {n_in}/{len(report)}")
    for r in sorted(report, key=lambda x: x["estimate"])[:8]:
        flag = "OK" if r["in_certified_enclosure"] else "MISS"
        lo, hi = r["nearest_enclosure"]
        print(f"    {r['estimate']:+.6f}  [{flag}]  enclosure [{lo:.6f}, {hi:.6f}]")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "curverank-signal-report.json").write_text(json.dumps({
        "claim_boundary": (
            "Finite-operator spectral screening + method benchmark; extracted "
            "eigenvalues are evidence validated against the certified kernel, not "
            "a proof of the Riemann Hypothesis."
        ),
        "n_basis": args.n_basis, "method": args.method,
        "mode": f"shots={args.shots}" if args.shots else "exact",
        "dt": res.dt, "n_times": res.n_times,
        "in_certified_enclosure": f"{n_in}/{len(report)}",
        "estimates": report,
    }, indent=2), encoding="utf-8")
    print(f"  report -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
