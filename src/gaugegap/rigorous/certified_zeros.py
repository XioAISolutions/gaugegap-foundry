"""Independently certified Riemann-zero enclosures via Arb.

The CurveRank certified pipeline previously *trusted* ``mpmath.zetazero`` to
locate the zeros and wrapped its output in a conservative interval.  This
module replaces that trust with machine-checked enclosures from Arb
(``python-flint``): ``acb.zeta_zeros`` returns rigorous complex balls for the
n-th nontrivial zeta zero, with **index correctness established internally via
Turing's method** -- i.e. each ball provably contains the j-th zero, not merely
*a* zero.  Arb is an independent implementation (C, ball arithmetic), so this
also serves as a cross-check of the zetazero-based path.

Conversion to the repo's :class:`Interval` type goes through decimal strings of
the ball's rigorous lower/upper bounds and inflates each endpoint by a guard
margin that strictly dominates the string-rounding error, so the resulting
interval still rigorously contains the true zero.

CLAIM BOUNDARY: certifying enclosures of finitely many zeta zeros supports the
finite-truncation spectral-mismatch certificates only.  It does NOT prove or
disprove the Riemann Hypothesis.
"""
from __future__ import annotations

from typing import List


def arb_available() -> bool:
    """True if python-flint with rigorous ``acb.zeta_zeros`` is importable."""
    try:
        from flint import acb  # noqa: F401
    except ImportError:
        return False
    return hasattr(acb, "zeta_zeros")


def arb_zero_intervals(k: int, prec: int = 192, guard_exp: int = 40) -> List["Interval"]:
    """Certified enclosures of the first *k* nontrivial zeta zeros via Arb.

    Parameters
    ----------
    k : int
        Number of zeros (positive imaginary parts, ascending, index-correct).
    prec : int
        Arb working precision in bits.  192 bits gives ball radii around
        1e-55; far tighter than the guard margin.
    guard_exp : int
        Endpoint guard ``10**-guard_exp`` added outward after the decimal
        conversion.  It must dominate the string-rounding error of the
        ``digits``-digit printout (digits is chosen so this holds).

    Returns
    -------
    list[Interval]
        ``[t_j_lo, t_j_hi]`` rigorously containing the j-th zero's imaginary
        part, for j = 1..k.

    Raises
    ------
    ImportError
        If python-flint is not installed or too old (needs ``acb.zeta_zeros``,
        python-flint >= 0.7).
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    try:
        from flint import acb, ctx
    except ImportError as exc:  # pragma: no cover - exercised via arb_available
        raise ImportError(
            "python-flint is required for Arb-certified zero enclosures. "
            "Install with: pip install 'python-flint>=0.7'"
        ) from exc
    if not hasattr(acb, "zeta_zeros"):
        raise ImportError(
            "python-flint is too old: acb.zeta_zeros requires python-flint >= 0.7"
        )

    import mpmath as mp
    from gaugegap.rigorous.interval_arithmetic import Interval

    # Print enough digits that the decimal conversion error is far below the
    # guard margin (zeros up to t ~ 1e3 with guard_exp digits after the point).
    digits = guard_exp + 10

    # Compute the balls AND extract their endpoint strings at elevated Arb
    # precision: .lower()/.upper() round at the *current* ctx.prec, so reading
    # them after restoring the default 53-bit precision would widen the bounds
    # to ~1e-15 and defeat the guard margin.  mpmath parsing/inflation likewise
    # runs at elevated dps so its rounding stays far below the guard.
    old_prec = ctx.prec
    ctx.prec = max(prec, old_prec)
    try:
        balls = acb.zeta_zeros(1, k)
        endpoint_strs = [
            (
                ball.imag.lower().str(digits, radius=False),
                ball.imag.upper().str(digits, radius=False),
            )
            for ball in balls
        ]
    finally:
        ctx.prec = old_prec

    intervals: List[Interval] = []
    with mp.workdps(digits + 15):
        guard = mp.mpf(10) ** (-guard_exp)
        for lo_s, hi_s in endpoint_strs:
            lo = mp.mpf(lo_s) - guard
            hi = mp.mpf(hi_s) + guard
            intervals.append(Interval(lo, hi))
    return intervals
