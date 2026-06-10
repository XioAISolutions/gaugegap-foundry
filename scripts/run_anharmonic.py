#!/usr/bin/env python3
"""Certified variational upper bounds on the quartic anharmonic oscillator.

H = 1/2 p^2 + 1/2 x^2 + lambda x^4. By Rayleigh-Ritz, each truncated eigenvalue
is a rigorous upper bound on the true (infinite-dimensional) energy; this reports
the certified upper bounds and their convergence as the basis grows.

CLAIM BOUNDARY: a certified one-sided (variational) upper bound on the spectrum
of a quantum-mechanical anharmonic oscillator; not a field theory, continuum, or
Millennium-Prize claim.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.anharmonic import REFERENCE_E0, certified_anharmonic_bounds  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lam", type=float, default=1.0)
    ap.add_argument("--n-basis", type=int, default=30)
    ap.add_argument("--n-levels", type=int, default=4)
    args = ap.parse_args()

    print("# Certified variational bounds: H = 1/2 p^2 + 1/2 x^2 + lambda x^4\n")
    print(f"lambda = {args.lam}\n")
    print("Convergence of the certified upper bound on E0 (Rayleigh-Ritz, decreasing):")
    for N in sorted({10, 20, args.n_basis}):
        ub = certified_anharmonic_bounds(n_basis=N, lam=args.lam, n_levels=1).ground_upper_bound()
        print(f"  N={N:3d}   E0 <= {ub:.10f}")
    ref = REFERENCE_E0.get(args.lam)
    if ref is not None:
        print(f"  reference E0 ~ {ref}")
    print()

    b = certified_anharmonic_bounds(n_basis=args.n_basis, lam=args.lam, n_levels=args.n_levels)
    print(f"Certified eigenvalue enclosures at N={args.n_basis} "
          f"(upper endpoint = certified upper bound on E_n):")
    for n, enc in enumerate(b.enclosures):
        print(f"  E{n}  in  [{float(enc.lower):.10f}, {float(enc.upper):.10f}]   "
              f"width {float(enc.width()):.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
