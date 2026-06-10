"""Certified variational bounds for the quantum quartic anharmonic oscillator.

The quartic anharmonic oscillator

    H = 1/2 p^2 + 1/2 x^2 + lambda x^4         (hbar = m = omega = 1)

is the textbook quantum system with *no closed-form* spectrum -- its energy
levels are transcendental numbers known only numerically. This module computes
**certified variational upper bounds** on those true (infinite-dimensional)
energies, on the rigorous interval-arithmetic eigensolver used elsewhere in this
repository.

Method
------
In the harmonic-oscillator basis |0>, |1>, ..., the unperturbed part
1/2 p^2 + 1/2 x^2 is diagonal with entries n + 1/2, and the quartic perturbation
has exact matrix elements via x = (a + a^dagger)/sqrt(2). Projecting H onto the
first N basis states and diagonalizing gives, by the Rayleigh-Ritz / min-max
theorem, eigenvalues that are **rigorous upper bounds** on the true ordered
eigenvalues:

    E_n^(N)  >=  E_n^(true)        for every truncation N.

We build the projected H as an interval matrix (the only irrational entries are
the sqrt((k+1)/2) off-diagonals of x, enclosed by directed-rounding sqrt) and run
``verified_hermitian_eigenvalues``. The **upper endpoint** of each certified
enclosure is then a machine-checked upper bound on E_n^(true). As N grows the
bounds decrease monotonically toward the true energies.

CLAIM BOUNDARY
--------------
This certifies *upper bounds* on the true eigenvalues of a finite-dimensional
quantum-mechanical Hamiltonian (the anharmonic oscillator). It is a rigorous
one-sided bound from the variational principle -- not a two-sided enclosure of
the true energy, and not a statement about any field theory, continuum limit, or
Millennium Prize problem.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import mpmath as mp

from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    IntervalMatrix,
    verified_hermitian_eigenvalues,
)

# Reference high-precision values for the standard normalization
# H = 1/2 p^2 + 1/2 x^2 + lambda x^4 (for validation / convergence display only).
REFERENCE_E0 = {1.0: 0.8037706512, 0.1: 0.5591463, 0.5: 0.6961757}


def _sqrt_half_int(n: int) -> Interval:
    """Certified enclosure of sqrt(n / 2) via directed-rounding sqrt."""
    s = mp.iv.sqrt(mp.iv.mpf(n) / 2)
    return Interval(mp.mpf(s.a), mp.mpf(s.b))


def position_matrix_interval(dim: int) -> IntervalMatrix:
    """The position operator x = (a + a^dagger)/sqrt(2) as an interval matrix.

    Off-diagonal entries <k|x|k+1> = <k+1|x|k> = sqrt((k+1)/2), enclosed exactly.
    """
    zero = Interval.from_float(0.0)
    entries = [[zero for _ in range(dim)] for _ in range(dim)]
    for k in range(dim - 1):
        val = _sqrt_half_int(k + 1)
        entries[k][k + 1] = val
        entries[k + 1][k] = val
    return IntervalMatrix(entries)


def anharmonic_hamiltonian_interval(n_basis: int, lam: float = 1.0,
                                    pad: int = 4) -> IntervalMatrix:
    """Projected anharmonic Hamiltonian H = (n+1/2) + lambda x^4 on N basis states.

    x^4 is formed in a slightly larger (N+pad) space and the exact N x N block is
    taken, so the matrix elements <m|x^4|n> (m,n < N) are the true projection
    (x^4 connects states differing by at most 4). pad >= 4 guarantees exactness.
    """
    if n_basis < 1:
        raise ValueError("n_basis must be >= 1")
    if pad < 4:
        raise ValueError("pad must be >= 4 so the x^4 block is exact")

    m = n_basis + pad
    x = position_matrix_interval(m)
    x2 = x * x
    x4 = x2 * x2  # interval matmul: rigorous enclosure of <m|x^4|n>

    lam_iv = Interval.from_float(float(lam))
    entries = [[Interval.from_float(0.0) for _ in range(n_basis)] for _ in range(n_basis)]
    for i in range(n_basis):
        for j in range(n_basis):
            term = lam_iv * x4.entries[i][j]
            if i == j:
                term = term + Interval.from_float(i + 0.5)
            entries[i][j] = term
    return IntervalMatrix(entries)


@dataclass(frozen=True)
class AnharmonicBounds:
    n_basis: int
    lam: float
    enclosures: List[Interval]

    def upper_bounds(self) -> List[float]:
        """Certified variational upper bounds on the true energies E_n."""
        return [float(e.upper) for e in self.enclosures]

    def ground_upper_bound(self) -> float:
        return float(self.enclosures[0].upper)


def certified_anharmonic_bounds(n_basis: int = 30, lam: float = 1.0,
                                n_levels: int | None = None) -> AnharmonicBounds:
    """Certified variational upper bounds on the anharmonic-oscillator spectrum.

    Returns enclosures of the projected Hamiltonian's eigenvalues; each upper
    endpoint is a rigorous upper bound on the corresponding true eigenvalue.
    """
    H = anharmonic_hamiltonian_interval(n_basis, lam)
    enclosures = verified_hermitian_eigenvalues(H)
    if n_levels is not None:
        enclosures = enclosures[:n_levels]
    return AnharmonicBounds(n_basis=n_basis, lam=lam, enclosures=enclosures)
