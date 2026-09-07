"""Exact rational mirror of the Lean variational-bound statements.

Restates every node of the ``gaugegap-variational`` track of
``formal/lean/dag.json`` over ``fractions.Fraction`` and checks it on rational
eigenvalue and coefficient vectors, including exactly normalised ones.

The point of the track, and so of this mirror: the emitted bracket certificates
(``results/certified-bracket/bracket_E0.lean`` and friends) assume three things,
of which two are numerical facts and one -- "the Rayleigh quotient of a
normalised trial state is at least the smallest eigenvalue" -- is a theorem.
This restates the theorem.

CLAIM BOUNDARY: finite-dimensional linear algebra for a declared eigenbasis
expansion. The spectral theorem that supplies the eigenbasis is a standing
hypothesis, not something established here.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Callable, Sequence

Q = Fraction

#: Exactly normalised rational coefficient vectors: sum of squares is 1.
NORMALISED: tuple[tuple[Q, ...], ...] = (
    (Q(1),),
    (Q(1), Q(0)),
    (Q(3, 5), Q(4, 5)),
    (Q(-3, 5), Q(4, 5)),
    (Q(1, 2), Q(1, 2), Q(1, 2), Q(1, 2)),
    (Q(5, 13), Q(12, 13)),
    (Q(2, 3), Q(2, 3), Q(1, 3)),
    (Q(0), Q(1), Q(0), Q(0)),
)

#: Unnormalised vectors, for the scaled forms D01 and D02.
UNNORMALISED: tuple[tuple[Q, ...], ...] = NORMALISED + (
    (Q(2), Q(-3)),
    (Q(1, 7), Q(0), Q(5)),
    (Q(0), Q(0)),
)

#: Rational eigenvalue vectors paired by length with the coefficient vectors.
SPECTRA: dict[int, tuple[tuple[Q, ...], ...]] = {
    1: ((Q(-2),), (Q(7, 3),)),
    2: ((Q(-2), Q(5)), (Q(1, 2), Q(1, 2)), (Q(-13), Q(-1, 4))),
    3: ((Q(-1), Q(0), Q(4)), (Q(2), Q(2), Q(2))),
    4: ((Q(-5), Q(-1), Q(0), Q(3)), (Q(1, 8), Q(9), Q(-2), Q(6))),
}


def norm_sq(c: Sequence[Q]) -> Q:
    return sum((x**2 for x in c), Q(0))


def rayleigh(lam: Sequence[Q], c: Sequence[Q]) -> Q:
    return sum((l * x**2 for l, x in zip(lam, c)), Q(0))


def _pairs(vectors: Sequence[Sequence[Q]]):
    for c in vectors:
        for lam in SPECTRA.get(len(c), ()):
            yield lam, c


def d01() -> bool:
    for lam, c in _pairs(UNNORMALISED):
        lo = min(lam)
        if not lo * norm_sq(c) <= rayleigh(lam, c):
            return False
    return True


def d02() -> bool:
    for lam, c in _pairs(UNNORMALISED):
        hi = max(lam)
        if not rayleigh(lam, c) <= hi * norm_sq(c):
            return False
    return True


def d03() -> bool:
    for lam, c in _pairs(NORMALISED):
        lo, hi = min(lam), max(lam)
        value = rayleigh(lam, c)
        if not (lo <= value <= hi):
            return False
    return True


def d04() -> bool:
    """No normalised trial state beats the ground energy."""
    for lam, c in _pairs(NORMALISED):
        if not min(lam) <= rayleigh(lam, c):
            return False
    return True


def d05() -> bool:
    """The bracket, with the two numerical inputs supplied as hypotheses."""
    for lam, c in _pairs(NORMALISED):
        ground = min(lam)
        lower = ground - Q(1, 100)          # an interval-arithmetic enclosure
        upper = rayleigh(lam, c)            # an evaluated trial state
        if not (lower <= ground and ground <= upper):
            return False
    return True


def strictly_above_ground_energy() -> int:
    """Non-vacuity: trial states whose Rayleigh quotient is strictly above the
    ground energy, so D04 is not an equality in disguise."""
    return sum(
        1 for lam, c in _pairs(NORMALISED) if min(lam) < rayleigh(lam, c)
    )


NODE_CHECKS: dict[str, Callable[[], bool]] = {
    "D01": d01,
    "D02": d02,
    "D03": d03,
    "D04": d04,
    "D05": d05,
}
