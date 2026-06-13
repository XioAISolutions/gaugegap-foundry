"""Certified enclosures for the symmetric quartic double-well oscillator.

The symmetric double well

    H = 1/2 p^2 - 1/2 x^2 + lambda x^4        (hbar = m = 1, lambda > 0)

has two degenerate classical minima separated by a barrier of height 1/(16 lambda).
Quantum tunnelling through the barrier splits each would-be degenerate pair into a
close doublet; the ground-state tunnelling splitting Delta = E1 - E0 is the
canonical observable.

This module builds the truncated Hamiltonian in the harmonic-oscillator basis as a
certified interval matrix (reusing ``gaugegap.anharmonic.position_matrix_interval``)
and reports:

- certified Rayleigh-Ritz **upper bounds** on the low-lying levels (each truncated
  eigenvalue bounds the corresponding true eigenvalue from above);
- certified comparison-oscillator **lower bounds** (for a > 1/(4 lambda),
  x^4 >= 2 a x^2 - a^2 gives a solvable lower-envelope oscillator);
- a certified enclosure of the **finite-truncation tunnelling splitting**
  mu_1 - mu_0 from the two certified eigenvalue enclosures.

CLAIM BOUNDARY
--------------
The level *upper* bounds and the comparison-oscillator *lower* bounds are rigorous
statements about the true (infinite-dimensional) double-well operator. The
tunnelling-splitting enclosure is certified for the FINITE truncation; it
converges to the true splitting as the basis grows (shown as evidence), but a
two-sided bound on the true splitting of a near-degenerate doublet is not claimed.
Not a field-theory, continuum, or Millennium-Prize claim.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from gaugegap.anharmonic import position_matrix_interval
from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    IntervalMatrix,
    verified_hermitian_eigenvalues,
)


def double_well_hamiltonian_interval(n_basis: int, lam: float = 0.1,
                                     pad: int = 8) -> IntervalMatrix:
    """Projected double-well Hamiltonian H = (n+1/2) - x^2 + lambda x^4.

    Using 1/2 p^2 + 1/2 x^2 = diag(n+1/2), we have
    H = 1/2 p^2 - 1/2 x^2 + lambda x^4 = diag(n+1/2) - x^2 + lambda x^4.
    x^2 and x^4 are taken as the exact N x N blocks of an (N+pad) product
    (x^4 couples states by at most 4, so pad >= 4 makes the block exact).
    """
    if n_basis < 2:
        raise ValueError("n_basis must be >= 2 (need a ground doublet)")
    if pad < 4:
        raise ValueError("pad must be >= 4 so the x^4 block is exact")
    if lam <= 0:
        raise ValueError("lambda must be > 0 for a bounded-below double well")

    m = n_basis + pad
    x = position_matrix_interval(m)
    x2 = x * x
    x4 = x2 * x2

    lam_iv = Interval.from_float(float(lam))
    entries = [[Interval.from_float(0.0) for _ in range(n_basis)] for _ in range(n_basis)]
    for i in range(n_basis):
        for j in range(n_basis):
            term = lam_iv * x4.entries[i][j] - x2.entries[i][j]
            if i == j:
                term = term + Interval.from_float(i + 0.5)
            entries[i][j] = term
    return IntervalMatrix(entries)


def _comparison_level_interval(n: int, lam: float, a: float) -> Interval:
    """E_n of the comparison oscillator for the double well, at parameter a.

    x^4 >= 2 a x^2 - a^2 gives H >= 1/2 p^2 + (2 lambda a - 1/2) x^2 - lambda a^2.
    For 4 lambda a > 1 this is a (shifted) harmonic oscillator with
    E_n = sqrt(4 lambda a - 1) (n + 1/2) - lambda a^2, a rigorous lower bound on
    E_n(H).
    """
    lam_i = Interval.from_float(float(lam))
    a_i = Interval.from_float(float(a))
    one = Interval.from_float(1.0)
    four = Interval.from_float(4.0)
    inner = four * lam_i * a_i - one          # 4 lambda a - 1  (> 0 required)
    if not (float(inner.lower) > 0):
        raise ValueError("need 4*lambda*a > 1 for the harmonic comparison")
    omega = inner.sqrt()
    n_half = Interval.from_float(n + 0.5)
    return omega * n_half - lam_i * (a_i * a_i)


def certified_level_lower_bound(n: int, lam: float = 0.1) -> float:
    """Rigorous lower bound on E_n(H) via the optimized comparison oscillator."""
    import numpy as np

    a_lo = 1.0 / (4.0 * lam) + 1e-6
    a_grid = np.linspace(a_lo, a_lo + 4.0 * (n + 1), 600)
    f = np.sqrt(4.0 * lam * a_grid - 1.0) * (n + 0.5) - lam * a_grid ** 2
    a_best = float(a_grid[int(np.argmax(f))])
    return float(_comparison_level_interval(n, lam, a_best).lower)


@dataclass(frozen=True)
class DoubleWellLevel:
    n: int
    lower: float       # certified lower bound (comparison oscillator)
    upper: float       # certified upper bound (Rayleigh-Ritz)

    @property
    def width(self) -> float:
        return self.upper - self.lower


@dataclass(frozen=True)
class TunnellingSplitting:
    n_basis: int
    lam: float
    lower: float       # certified enclosure of the truncated splitting mu1 - mu0
    upper: float
    barrier_height: float

    @property
    def midpoint(self) -> float:
        return 0.5 * (self.lower + self.upper)


def certified_double_well_levels(n_basis: int = 40, lam: float = 0.1,
                                 n_levels: int = 4) -> List[DoubleWellLevel]:
    """Certified two-sided enclosures of the lowest double-well levels."""
    enclosures = verified_hermitian_eigenvalues(
        double_well_hamiltonian_interval(n_basis, lam))[:n_levels]
    out: List[DoubleWellLevel] = []
    for n, enc in enumerate(enclosures):
        out.append(DoubleWellLevel(n=n, lower=certified_level_lower_bound(n, lam),
                                   upper=float(enc.upper)))
    return out


def certified_tunnelling_splitting(n_basis: int = 40, lam: float = 0.1) -> TunnellingSplitting:
    """Certified enclosure of the (finite-truncation) ground tunnelling splitting.

    From the two lowest certified eigenvalue enclosures [a0,b0], [a1,b1] of the
    truncated Hamiltonian, the truncated splitting mu1 - mu0 lies in
    [a1 - b0, b1 - a0]. For a deep well this equals the true splitting to many
    digits at moderate N (the truncated eigenvalues converge from above).
    """
    enc = verified_hermitian_eigenvalues(double_well_hamiltonian_interval(n_basis, lam))
    e0, e1 = enc[0], enc[1]
    lower = float(e1.lower) - float(e0.upper)
    upper = float(e1.upper) - float(e0.lower)
    return TunnellingSplitting(
        n_basis=n_basis, lam=lam, lower=lower, upper=upper,
        barrier_height=1.0 / (16.0 * lam),
    )
