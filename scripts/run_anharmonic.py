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

from gaugegap.anharmonic import (  # noqa: E402
    REFERENCE_E0,
    certified_anharmonic_bounds,
    certified_ground_state_enclosure,
    certified_two_sided_spectrum,
)


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
    print()

    # Certified two-sided enclosures across the low-lying spectrum.
    print("Certified TWO-SIDED enclosures (lower = Temple/comparison, upper = Rayleigh-Ritz):")
    for L in certified_two_sided_spectrum(n_basis=args.n_basis, lam=args.lam,
                                          n_levels=min(3, args.n_levels)):
        print(f"  E{L.n}_true in [{L.lower:.10f}, {L.upper:.10f}]   "
              f"width {L.width:.2e}   (lower via {L.method})")
    gs = certified_ground_state_enclosure(n_basis=args.n_basis, lam=args.lam)
    print(f"  ground-state Temple beta (sharpened E1 lower bound) = {gs.e1_lower_bound:.6f}")

    # Lambda sweep for the ground state.
    print("\nGround-state two-sided enclosure across lambda:")
    for lam in (0.1, 0.5, 1.0, 2.0):
        e = certified_ground_state_enclosure(n_basis=args.n_basis, lam=lam)
        ref = REFERENCE_E0.get(lam)
        tag = f"  (ref {ref})" if ref is not None else ""
        print(f"  lambda={lam:<4}  E0 in [{e.lower:.10f}, {e.upper:.10f}]  width {e.width:.2e}{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
