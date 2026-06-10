#!/usr/bin/env python3
"""Report the single-link SU(3) electric (Kogut-Susskind) spectrum (issue #12 A3).

A defensible finite SU(3) gauge truncation: the colour-electric energy of one
gauge link is the quadratic Casimir of the irrep it carries, exactly diagonalized
in a truncated irrep basis.

CLAIM BOUNDARY: single-link SU(3) electric Hamiltonian, exact in a truncated
irrep basis; no plaquette dynamics, no continuum or Yang-Mills mass-gap claim.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.gaugegap_su3_link import (  # noqa: E402
    SU3LinkElectric,
    SU3LinkElectricConfig,
    electric_gap_closed_form,
)
from gaugegap.ledger import utc_run_id


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--g-electric", type=float, default=1.0)
    ap.add_argument("--cutoff", type=int, default=2)
    ap.add_argument("--output-dir", type=str, default=None)
    args = ap.parse_args()

    model = SU3LinkElectric(SU3LinkElectricConfig(args.g_electric, args.cutoff))
    gap = model.compute_gap()

    print("# Single-link SU(3) electric (Kogut-Susskind) spectrum\n")
    print(f"g_electric = {args.g_electric}   irrep cutoff p,q <= {args.cutoff}")
    print(f"Hilbert dim = {model.hilbert_dim}   (sum of dim(R)^2)\n")
    print(f"{'energy':>10}  {'C2':>7}  {'deg':>5}  irreps")
    print("  " + "-" * 40)
    for level in model.levels():
        print(f"{level['energy']:>10.4f}  {level['casimir']:>7.4f}  "
              f"{level['degeneracy']:>5}  {', '.join(level['irreps'])}")
    print()
    print(f"ground energy = {gap['ground_energy']:.6f} (colour singlet, deg "
          f"{gap['ground_degeneracy']})")
    print(f"electric gap  = {gap['gap']:.6f}  "
          f"(closed form 2 g^2/3 = {electric_gap_closed_form(args.g_electric):.6f})")

    if args.output_dir:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        payload = {"run_id": utc_run_id(), "config": vars(args), **gap,
                   "levels": model.levels()}
        (out / "su3_link_electric.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
        print(f"\nWrote {out}/su3_link_electric.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
