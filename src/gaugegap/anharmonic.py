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

# Reference high-precision ground energies for H = 1/2 p^2 + 1/2 x^2 + lambda x^4
# (from large-N diagonalization; for validation / convergence display only).
REFERENCE_E0 = {
    0.1: 0.5591463272,
    0.5: 0.6961758208,
    1.0: 0.8037706512,
    2.0: 0.9515684727,
}


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


def mpmath_ground_eigenvalue(n_basis: int = 20, lam: float = 1.0, dps: int = 40) -> float:
    """Ground eigenvalue of the truncated anharmonic H via mpmath.eigsy.

    An *independent* high-precision symmetric eigensolver (a different code path
    from ``verified_hermitian_eigenvalues``, which uses numpy + a residual bound)
    -- used to cross-check the certified enclosure against a second library.
    """
    import mpmath as mp

    with mp.workdps(dps):
        m = n_basis + 4
        x = mp.zeros(m)
        for k in range(m - 1):
            v = mp.sqrt(mp.mpf(k + 1) / 2)
            x[k, k + 1] = v
            x[k + 1, k] = v
        x4 = (x * x) * (x * x)
        H = mp.zeros(n_basis)
        for i in range(n_basis):
            for j in range(n_basis):
                H[i, j] = mp.mpf(lam) * x4[i, j] + (mp.mpf(i) + mp.mpf("0.5") if i == j else mp.mpf(0))
        evals, _ = mp.eigsy(H)
        return float(min(evals[i] for i in range(n_basis)))


# ---------------------------------------------------------------------------
# Two-sided (Temple) enclosure of the ground-state energy.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Comparison-oscillator lower bounds (sharpened, level-resolved).
# ---------------------------------------------------------------------------

def _comparison_level_interval(n: int, lam: float, a: float) -> Interval:
    """Certified value of E_n of the comparison oscillator at parameter a.

    Since (x^2 - a)^2 >= 0 gives x^4 >= 2 a x^2 - a^2, for a > 0

        H = 1/2 p^2 + 1/2 x^2 + lambda x^4
          >= 1/2 p^2 + 1/2 (1 + 4 lambda a) x^2 - lambda a^2  =: H_a,

    a solvable oscillator with E_n(H_a) = sqrt(1 + 4 lambda a) (n + 1/2)
    - lambda a^2. By min-max E_n(H) >= E_n(H_a) for EVERY a > 0, so the lower
    endpoint of this interval is a rigorous lower bound on E_n(H).
    """
    lam_i = Interval.from_float(float(lam))
    a_i = Interval.from_float(float(a))
    one = Interval.from_float(1.0)
    four = Interval.from_float(4.0)
    omega2 = one + four * lam_i * a_i          # 1 + 4 lambda a  (> 0)
    omega = omega2.sqrt()
    n_half = Interval.from_float(n + 0.5)
    return omega * n_half - lam_i * (a_i * a_i)


def certified_level_lower_bound(n: int, lam: float = 1.0) -> float:
    """Rigorous lower bound on E_n(H) via the optimized comparison oscillator.

    The bound is valid for any a > 0; we scan a in floating point to find a
    near-optimal value, then evaluate the bound rigorously at that a.
    """
    import numpy as np

    a_max = 1.0 + 1.5 * (n + 1)
    a_grid = np.linspace(1e-3, a_max, 400)
    f = np.sqrt(1.0 + 4.0 * lam * a_grid) * (n + 0.5) - lam * a_grid ** 2
    a_best = float(a_grid[int(np.argmax(f))])
    return float(_comparison_level_interval(n, lam, a_best).lower)


def _matvec(matrix: IntervalMatrix, vec: List[Interval]) -> List[Interval]:
    out: List[Interval] = []
    for i in range(matrix.m):
        acc = matrix.entries[i][0] * vec[0]
        for j in range(1, matrix.n):
            acc = acc + matrix.entries[i][j] * vec[j]
        out.append(acc)
    return out


def _dot(a: List[Interval], b: List[Interval]) -> Interval:
    acc = a[0] * b[0]
    for i in range(1, len(a)):
        acc = acc + a[i] * b[i]
    return acc


@dataclass(frozen=True)
class GroundStateEnclosure:
    n_basis: int
    lam: float
    lower: float        # certified lower bound (Temple's inequality)
    upper: float        # certified upper bound (Rayleigh-Ritz)
    rayleigh: Interval  # the Rayleigh quotient <psi|H|psi>
    variance: Interval  # <psi|H^2|psi> - <psi|H|psi>^2
    e1_lower_bound: float

    @property
    def width(self) -> float:
        return self.upper - self.lower


def certified_ground_state_enclosure(n_basis: int = 30, lam: float = 1.0) -> GroundStateEnclosure:
    """Certified TWO-SIDED enclosure of the true ground-state energy E0.

    Combines the Rayleigh-Ritz upper bound with **Temple's inequality** for a
    rigorous lower bound:

        E0 >= eps - sigma^2 / (beta - eps),

    where eps = <psi|H|psi>, sigma^2 = <psi|H^2|psi> - eps^2 for a trial vector
    psi, and beta is any number with eps < beta <= E1. We use the operator bound
    H = (HO) + lambda x^4 with lambda x^4 >= 0, hence E1 >= 3/2 (every eigenvalue
    of H is at least the harmonic value), so beta = 3/2 is rigorous. The trial
    vector is the floating-point ground vector of the truncation (its accuracy
    only affects tightness, not validity), and eps, sigma^2 are evaluated in
    interval arithmetic over the exact (N+4)-projected Hamiltonian so that
    <psi|H^2|psi> = ||H psi||^2 captures every component H couples into.
    """
    if lam < 0:
        raise ValueError("Temple bound here assumes lambda >= 0 (so E1 >= 3/2)")

    # Trial vector: float ground eigenvector of the N-truncation.
    H_n = anharmonic_hamiltonian_interval(n_basis, lam)
    A = H_n.to_numpy()
    import numpy as np
    w, V = np.linalg.eigh(A)
    psi = V[:, 0]
    psi = psi / np.linalg.norm(psi)

    # Embed psi in the larger (N+4) space and evaluate H psi exactly there, so
    # ||H psi||^2 = <psi|H^2|psi> for the true operator (x^4 spreads by +-4).
    m = n_basis + 4
    H_m = anharmonic_hamiltonian_interval(m, lam)
    psi_iv = [Interval.from_float(float(psi[i])) if i < n_basis else Interval.from_float(0.0)
              for i in range(m)]
    h_psi = _matvec(H_m, psi_iv)
    eps = _dot(psi_iv, h_psi)
    eps2 = _dot(h_psi, h_psi)
    variance = eps2 - eps * eps

    # Temple's beta: a rigorous lower bound on E1. The operator bound gives
    # E1 >= 3/2; the optimized comparison oscillator gives a much sharper one.
    # Both are rigorous, so take the larger (it only needs eps < beta <= E1).
    beta_value = max(1.5, certified_level_lower_bound(1, lam))
    beta = Interval.from_float(beta_value)
    # Require eps < beta strictly so (beta - eps) is positive (no division by 0).
    if not (float(eps.upper) < beta_value):
        raise ValueError("Temple bound requires <psi|H|psi> < beta; increase n_basis")
    temple = eps - variance / (beta - eps)

    # Upper bound: the certified eigenvalue enclosure's upper endpoint (tighter
    # than the Rayleigh quotient).
    upper = float(verified_hermitian_eigenvalues(H_n)[0].upper)
    return GroundStateEnclosure(
        n_basis=n_basis, lam=lam,
        lower=float(temple.lower), upper=upper,
        rayleigh=eps, variance=variance, e1_lower_bound=beta_value,
    )


# ---------------------------------------------------------------------------
# Two-sided enclosures across the low-lying spectrum.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LevelEnclosure:
    n: int
    lower: float
    upper: float
    method: str  # how the lower bound was obtained

    @property
    def width(self) -> float:
        return self.upper - self.lower


def certified_two_sided_spectrum(n_basis: int = 30, lam: float = 1.0,
                                 n_levels: int = 3) -> List[LevelEnclosure]:
    """Certified two-sided enclosures [lower, upper] for the lowest n_levels.

    Upper bounds are Rayleigh-Ritz (certified eigenvalue enclosure upper
    endpoints); lower bounds are the optimized comparison-oscillator bounds,
    with the ground state additionally sharpened by Temple's inequality.
    """
    uppers = [float(e.upper) for e in certified_anharmonic_bounds(
        n_basis=n_basis, lam=lam, n_levels=n_levels).enclosures]
    out: List[LevelEnclosure] = []
    for n in range(n_levels):
        comp = certified_level_lower_bound(n, lam)
        if n == 0:
            temple = certified_ground_state_enclosure(n_basis=n_basis, lam=lam).lower
            lower, method = (temple, "Temple") if temple > comp else (comp, "comparison")
        else:
            lower, method = comp, "comparison"
        out.append(LevelEnclosure(n=n, lower=lower, upper=uppers[n], method=method))
    return out
