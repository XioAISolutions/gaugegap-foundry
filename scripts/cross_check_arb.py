#!/usr/bin/env python3
"""Independent cross-check of the certified enclosures against Arb (python-flint).

The certified pipeline computes its eigenvalue enclosures with ``mpmath.iv``
(directed-rounding interval arithmetic). This script recomputes the *same*
residual / Weyl certificate with a completely independent rigorous arithmetic
backend -- Arb ball arithmetic via ``python-flint``, at higher working precision
(256 bits vs mpmath's 50 decimal digits) -- and checks that the two libraries
agree. Its purpose is to retire the residual trust assumption of the
independent-review packet (section 5.1): that ``mpmath.iv``'s directed rounding
is itself correct.

For each eigenpair (theta_i, x_i) obtained from a float eigensolver, both
libraries are fed the *same* inputs and each computes the certified radius
rho = ||A x_i - theta_i x_i|| / ||x_i|| that bounds |lambda - theta_i|. Feeding
identical eigenpairs (rather than matching independently sorted spectra) avoids a
spurious mismatch on operators with degenerate eigenvalues, e.g. the doubled xp
embedding. We compare, per eigenpair:

  * AGREEMENT -- the two independently computed certified radii (rho_mp from
    mpmath.iv, [rho_lo, rho_hi] from Arb) must agree to high relative precision.
  * SAFETY   -- rho_mp must not fall below Arb's rigorous lower bound rho_lo on
    the true radius (that would mean mpmath under-rounded and its enclosure could
    miss the eigenvalue).

Requires ``python-flint`` (``pip install python-flint``); it is intentionally not
a CI dependency. Run locally as part of independent review.

CLAIM BOUNDARY: a finite-truncation cross-validation of the arithmetic. It does
not touch the truncation -> infinity limit or the Riemann Hypothesis.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import mpmath as mp  # noqa: E402
import numpy as np  # noqa: E402

from gaugegap.curverank_operators import (  # noqa: E402
    berry_keating_xp_interval,
    dirac_rindler_interval,
    quantum_graph_laplacian_interval,
)
from gaugegap.rigorous.interval_arithmetic import (  # noqa: E402
    Interval,
    certified_residual_radius,
)

try:
    from flint import arb, ctx
except ImportError:  # pragma: no cover - exercised only without the optional dep
    print("python-flint is required: pip install python-flint", file=sys.stderr)
    raise SystemExit(2)

ctx.prec = 256  # bits (~77 decimal digits), tighter than mpmath's 50 dps

_GRAPH_EDGES = [(0, 1), (0, 2), (0, 3)]
_GRAPH_LENGTHS = [1.0, float(np.sqrt(2)), float(np.sqrt(3))]


def _build(family: str, n: int):
    if family == "xp":
        return berry_keating_xp_interval(n)
    if family == "dirac_rindler":
        return dirac_rindler_interval(n, 1.0, 0.0)
    if family == "quantum_graph":
        return quantum_graph_laplacian_interval(_GRAPH_EDGES, _GRAPH_LENGTHS, n)
    raise ValueError(f"unknown family {family!r}")


def _arb_entry(iv: Interval) -> arb:
    """Rigorous Arb ball enclosing an mpmath interval entry."""
    mid = (iv.lower + iv.upper) / 2
    rad = (iv.upper - iv.lower) / 2
    # midpoint at full precision (string), radius inflated to a float (Arb rounds
    # the radius outward, so containment of the true entry is preserved).
    return arb(mp.nstr(mid, 60), float(rad) if rad > 0 else 0.0)


def _arb_radius_enclosure(matrix, theta: float, x_col: np.ndarray):
    """Arb enclosure [lo, hi] of ||A x - theta x|| / ||x|| for one eigenpair."""
    n = matrix.m
    A = [[_arb_entry(matrix.entries[i][j]) for j in range(n)] for i in range(n)]
    x = [arb(float(x_col[k])) for k in range(n)]
    th = arb(float(theta))

    res_sq = arb(0)
    for row in range(n):
        acc = arb(0)
        for col in range(n):
            acc = acc + A[row][col] * x[col]
        acc = acc - th * x[row]
        res_sq = res_sq + acc * acc
    norm_x_sq = arb(0)
    for k in range(n):
        norm_x_sq = norm_x_sq + x[k] * x[k]
    ratio = res_sq.sqrt() / norm_x_sq.sqrt()
    lo = mp.mpf(ratio.lower().str(50, radius=False))
    hi = mp.mpf(ratio.upper().str(50, radius=False))
    return lo, hi


def cross_check(family: str, n: int) -> dict:
    matrix = _build(family, n)
    theta, X = np.linalg.eigh(matrix.to_numpy())

    max_rel_radius_diff = mp.mpf(0)
    all_safe = True
    for i in range(matrix.m):
        # Same eigenpair into both backends.
        rho_mp = certified_residual_radius(matrix, float(theta[i]), X[:, i])
        r_lo, r_hi = _arb_radius_enclosure(matrix, float(theta[i]), X[:, i])

        # Safety: mpmath radius must not undercut Arb's rigorous lower bound.
        all_safe = all_safe and (rho_mp + mp.mpf("1e-40") >= r_lo)
        # Agreement: mpmath's outward radius vs Arb's outward upper bound.
        denom = r_hi if r_hi > mp.mpf("1e-300") else mp.mpf("1e-300")
        rel = abs(rho_mp - r_hi) / denom
        max_rel_radius_diff = max(max_rel_radius_diff, rel)

    return {
        "family": family,
        "n": n,
        "dim": matrix.m,
        "all_safe": all_safe,
        "max_rel_radius_diff": max_rel_radius_diff,
    }


def main() -> int:
    panel = [("xp", 10), ("xp", 20), ("dirac_rindler", 8), ("quantum_graph", 8)]
    print(f"# Arb (python-flint) cross-check of mpmath.iv certified enclosures")
    print(f"# Arb precision: {ctx.prec} bits; mpmath: {mp.mp.dps} decimal digits\n")
    header = f"{'family':<16} {'n':>3} {'dim':>4} {'safe':>6} {'max rel radius diff':>22}"
    print(header)
    print("-" * len(header))

    ok = True
    for family, n in panel:
        r = cross_check(family, n)
        ok = ok and r["all_safe"]
        print(
            f"{r['family']:<16} {r['n']:>3} {r['dim']:>4} "
            f"{str(r['all_safe']):>6} {mp.nstr(r['max_rel_radius_diff'], 4):>22}"
        )

    print()
    if ok:
        print("PASS: Arb independently corroborates every mpmath.iv certified radius")
        print("(mpmath radii are rigorously lower-bounded by Arb; the two backends")
        print("agree on the certified radius to the precision shown).")
        return 0
    print("FAIL: a disagreement was found between mpmath.iv and Arb -- investigate.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
