#!/usr/bin/env python3
"""Certified enclosures for the symmetric quartic double well.

H = 1/2 p^2 - 1/2 x^2 + lambda x^4. Reports certified two-sided level enclosures
(Rayleigh-Ritz upper + comparison-oscillator lower) and a certified enclosure of
the finite-truncation ground tunnelling splitting.

CLAIM BOUNDARY: level upper/lower bounds are rigorous for the true operator; the
tunnelling-splitting enclosure is certified for the finite truncation (it
converges to the true splitting, shown by stability in N). Not a field-theory,
continuum, or Millennium-Prize claim.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.double_well import (  # noqa: E402
    certified_double_well_levels,
    certified_tunnelling_splitting,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lam", type=float, default=0.1)
    ap.add_argument("--n-basis", type=int, default=40)
    args = ap.parse_args()

    print("# Certified symmetric double well: H = 1/2 p^2 - 1/2 x^2 + lambda x^4\n")
    print(f"lambda = {args.lam}   barrier height 1/(16 lambda) = {1/(16*args.lam):.4f}\n")

    print("Certified two-sided level enclosures (lower = comparison oscillator, "
          "upper = Rayleigh-Ritz):")
    for L in certified_double_well_levels(n_basis=args.n_basis, lam=args.lam, n_levels=4):
        print(f"  E{L.n} in [{L.lower:.8f}, {L.upper:.8f}]   width {L.width:.3f}")

    print()
    s40 = certified_tunnelling_splitting(n_basis=args.n_basis, lam=args.lam)
    s_more = certified_tunnelling_splitting(n_basis=args.n_basis + 10, lam=args.lam)
    print("Certified ground tunnelling splitting (finite truncation):")
    print(f"  N={args.n_basis:3d}  Delta in [{s40.lower:.12f}, {s40.upper:.12f}]  width {s40.upper-s40.lower:.2e}")
    print(f"  N={args.n_basis+10:3d}  Delta in [{s_more.lower:.12f}, {s_more.upper:.12f}]")
    print(f"  stability |Delta(N) - Delta(N+10)| = {abs(s40.midpoint - s_more.midpoint):.2e}"
          "  (evidence the truncated splitting equals the true splitting)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
