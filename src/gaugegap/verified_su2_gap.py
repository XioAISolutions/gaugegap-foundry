"""Verified finite SU(2) one-plaquette gap benchmark.

This module works in the gauge-invariant class-function basis ``|j> = chi_j`` on
one SU(2) plaquette. Haar orthogonality makes the character basis orthonormal,
and multiplication by the fundamental Wilson character follows the exact fusion
rule ``chi_(1/2) chi_j = chi_(j+1/2) + chi_(j-1/2)``.

The resulting finite truncation is a real symmetric tridiagonal matrix.  Its
lowest two eigenvalues are enclosed with exact-rational Sturm bisection, so the
reported positive gap is a bounded finite statement rather than a floating-point
plot.  It is not a continuum Yang-Mills mass-gap result.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Iterable

import numpy as np

CLAIM_BOUNDARY = (
    "finite one-plaquette SU(2) class-function truncation with exact-rational "
    "Sturm enclosures; no thermodynamic limit, continuum limit, or continuum "
    "Yang-Mills mass-gap claim"
)


def as_fraction(value: Fraction | int | str | float) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        return Fraction(str(value))
    return Fraction(value)


def fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class GaugeInvariantBasis:
    """Truncated SU(2) character basis indexed by ``two_j = 2j``."""

    max_two_j: int

    def __post_init__(self) -> None:
        if self.max_two_j < 1:
            raise ValueError("max_two_j must be at least 1")

    @property
    def labels(self) -> tuple[int, ...]:
        return tuple(range(self.max_two_j + 1))

    @property
    def dimension(self) -> int:
        return self.max_two_j + 1

    @property
    def j_values(self) -> tuple[Fraction, ...]:
        return tuple(Fraction(label, 2) for label in self.labels)

    @property
    def gauss_law_residual(self) -> Fraction:
        # Class functions are invariant under conjugation by construction.
        return Fraction(0)

    def summary(self) -> dict[str, object]:
        return {
            "basis": "SU(2) irreducible characters chi_j",
            "max_two_j": self.max_two_j,
            "j_max": fraction_text(Fraction(self.max_two_j, 2)),
            "dimension": self.dimension,
            "labels": [fraction_text(value) for value in self.j_values],
            "gauge_invariant_by_construction": True,
            "gauss_law_residual": "0",
        }


@dataclass(frozen=True)
class RationalInterval:
    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise ValueError("interval lower bound exceeds upper bound")

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    @property
    def midpoint(self) -> Fraction:
        return (self.lower + self.upper) / 2

    def contains(self, value: Fraction) -> bool:
        return self.lower <= value <= self.upper

    def summary(self) -> dict[str, object]:
        return {
            "lower": fraction_text(self.lower),
            "upper": fraction_text(self.upper),
            "lower_float": float(self.lower),
            "upper_float": float(self.upper),
            "width": fraction_text(self.width),
        }


@dataclass(frozen=True)
class VerifiedGapResult:
    basis: GaugeInvariantBasis
    electric: Fraction
    magnetic: Fraction
    matrix_digest: str
    ground: RationalInterval
    first_excited: RationalInterval
    gap: RationalInterval
    direct_spectrum: tuple[float, ...]
    fusion_spectrum: tuple[float, ...]
    construction_residual: float
    spectrum_residual: float
    sturm_bits: int

    @property
    def strictly_positive(self) -> bool:
        return self.gap.lower > 0

    def summary(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.verified_su2_gap.v1",
            "model": "SU(2) one-plaquette class-function truncation",
            "basis": self.basis.summary(),
            "parameters": {
                "electric": fraction_text(self.electric),
                "magnetic": fraction_text(self.magnetic),
            },
            "matrix_digest": self.matrix_digest,
            "independent_paths": {
                "direct_tridiagonal": list(self.direct_spectrum),
                "fusion_rule": list(self.fusion_spectrum),
                "construction_residual": self.construction_residual,
                "spectrum_residual": self.spectrum_residual,
                "exact_sturm_bisection_bits": self.sturm_bits,
            },
            "ground_state_interval": self.ground.summary(),
            "first_excited_interval": self.first_excited.summary(),
            "gap_interval": self.gap.summary(),
            "strictly_positive": self.strictly_positive,
            "claim_boundary": CLAIM_BOUNDARY,
        }


def casimir(two_j: int) -> Fraction:
    """Return j(j+1) exactly for ``two_j = 2j``."""
    if two_j < 0:
        raise ValueError("two_j must be nonnegative")
    return Fraction(two_j * (two_j + 2), 4)


def direct_matrix_exact(
    basis: GaugeInvariantBasis,
    *,
    electric: Fraction | int | str | float = Fraction(1),
    magnetic: Fraction | int | str | float = Fraction(1, 2),
) -> tuple[tuple[Fraction, ...], ...]:
    """Construct the finite Hamiltonian directly as a tridiagonal matrix."""
    e = as_fraction(electric)
    b = as_fraction(magnetic)
    if e <= 0 or b <= 0:
        raise ValueError("electric and magnetic couplings must be positive")
    n = basis.dimension
    matrix = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for idx, two_j in enumerate(basis.labels):
        matrix[idx][idx] = e * casimir(two_j)
        if idx + 1 < n:
            matrix[idx][idx + 1] = -b
            matrix[idx + 1][idx] = -b
    return tuple(tuple(row) for row in matrix)


def fusion_matrix_exact(
    basis: GaugeInvariantBasis,
    *,
    electric: Fraction | int | str | float = Fraction(1),
    magnetic: Fraction | int | str | float = Fraction(1, 2),
) -> tuple[tuple[Fraction, ...], ...]:
    """Construct the same Hamiltonian independently from SU(2) fusion rules."""
    e = as_fraction(electric)
    b = as_fraction(magnetic)
    if e <= 0 or b <= 0:
        raise ValueError("electric and magnetic couplings must be positive")
    labels = basis.labels
    index = {label: idx for idx, label in enumerate(labels)}
    matrix = [[Fraction(0) for _ in labels] for _ in labels]
    for source_label in labels:
        source = index[source_label]
        matrix[source][source] += e * casimir(source_label)
        # Fundamental fusion: (1/2) tensor j = (j+1/2) direct-sum (j-1/2).
        for target_label in (source_label - 1, source_label + 1):
            if target_label in index:
                matrix[index[target_label]][source] -= b
    return tuple(tuple(row) for row in matrix)


def matrix_digest(matrix: tuple[tuple[Fraction, ...], ...]) -> str:
    payload = [[fraction_text(value) for value in row] for row in matrix]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


def dense_float(matrix: tuple[tuple[Fraction, ...], ...]) -> np.ndarray:
    return np.asarray([[float(value) for value in row] for row in matrix], dtype=np.float64)


def tridiagonal_parts(
    matrix: tuple[tuple[Fraction, ...], ...]
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    n = len(matrix)
    if n < 2 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square with dimension at least two")
    for row in range(n):
        for col in range(n):
            if abs(row - col) > 1 and matrix[row][col] != 0:
                raise ValueError("matrix is not tridiagonal")
            if matrix[row][col] != matrix[col][row]:
                raise ValueError("matrix is not symmetric")
    return (
        tuple(matrix[idx][idx] for idx in range(n)),
        tuple(matrix[idx][idx + 1] for idx in range(n - 1)),
    )


def sturm_count_less_than(
    diagonal: tuple[Fraction, ...],
    off_diagonal: tuple[Fraction, ...],
    x: Fraction,
) -> int:
    """Count eigenvalues strictly below ``x`` via exact principal minors."""
    if len(diagonal) != len(off_diagonal) + 1:
        raise ValueError("invalid tridiagonal dimensions")
    sequence = [Fraction(1), diagonal[0] - x]
    for idx in range(1, len(diagonal)):
        sequence.append(
            (diagonal[idx] - x) * sequence[-1]
            - off_diagonal[idx - 1] ** 2 * sequence[-2]
        )
    nonzero = [value for value in sequence if value != 0]
    return sum(
        (nonzero[idx] > 0) != (nonzero[idx - 1] > 0)
        for idx in range(1, len(nonzero))
    )


def gershgorin_bounds(
    diagonal: tuple[Fraction, ...], off_diagonal: tuple[Fraction, ...]
) -> tuple[Fraction, Fraction]:
    lows: list[Fraction] = []
    highs: list[Fraction] = []
    for idx, center in enumerate(diagonal):
        radius = Fraction(0)
        if idx > 0:
            radius += abs(off_diagonal[idx - 1])
        if idx < len(off_diagonal):
            radius += abs(off_diagonal[idx])
        lows.append(center - radius)
        highs.append(center + radius)
    scale = max([Fraction(1), *(abs(value) for value in diagonal), *(abs(value) for value in off_diagonal)])
    return min(lows) - scale, max(highs) + scale


def isolate_eigenvalue(
    diagonal: tuple[Fraction, ...],
    off_diagonal: tuple[Fraction, ...],
    index: int,
    *,
    bits: int = 96,
) -> RationalInterval:
    """Enclose one ordered eigenvalue with exact-rational Sturm bisection."""
    if not 0 <= index < len(diagonal):
        raise IndexError("eigenvalue index out of range")
    if bits < 16:
        raise ValueError("bits must be at least 16")
    lower, upper = gershgorin_bounds(diagonal, off_diagonal)
    if sturm_count_less_than(diagonal, off_diagonal, lower) > index:
        raise RuntimeError("lower spectral bound is invalid")
    if sturm_count_less_than(diagonal, off_diagonal, upper) <= index:
        raise RuntimeError("upper spectral bound is invalid")
    for _ in range(bits):
        midpoint = (lower + upper) / 2
        if sturm_count_less_than(diagonal, off_diagonal, midpoint) <= index:
            lower = midpoint
        else:
            upper = midpoint
    return RationalInterval(lower, upper)


def verify_gap(
    *,
    max_two_j: int = 1,
    electric: Fraction | int | str | float = Fraction(1),
    magnetic: Fraction | int | str | float = Fraction(1, 2),
    sturm_bits: int = 96,
) -> VerifiedGapResult:
    basis = GaugeInvariantBasis(max_two_j=max_two_j)
    e = as_fraction(electric)
    b = as_fraction(magnetic)
    direct = direct_matrix_exact(basis, electric=e, magnetic=b)
    fusion = fusion_matrix_exact(basis, electric=e, magnetic=b)
    direct_array = dense_float(direct)
    fusion_array = dense_float(fusion)
    direct_spectrum = tuple(float(value) for value in np.linalg.eigvalsh(direct_array))
    fusion_spectrum = tuple(float(value) for value in np.linalg.eigvalsh(fusion_array))
    construction_residual = float(np.max(np.abs(direct_array - fusion_array)))
    spectrum_residual = float(np.max(np.abs(np.asarray(direct_spectrum) - np.asarray(fusion_spectrum))))
    diagonal, off_diagonal = tridiagonal_parts(direct)
    ground = isolate_eigenvalue(diagonal, off_diagonal, 0, bits=sturm_bits)
    first = isolate_eigenvalue(diagonal, off_diagonal, 1, bits=sturm_bits)
    gap = RationalInterval(first.lower - ground.upper, first.upper - ground.lower)
    return VerifiedGapResult(
        basis=basis,
        electric=e,
        magnetic=b,
        matrix_digest=matrix_digest(direct),
        ground=ground,
        first_excited=first,
        gap=gap,
        direct_spectrum=direct_spectrum,
        fusion_spectrum=fusion_spectrum,
        construction_residual=construction_residual,
        spectrum_residual=spectrum_residual,
        sturm_bits=sturm_bits,
    )


def sweep_verified_gaps(
    *,
    max_two_j_values: Iterable[int],
    electric_values: Iterable[Fraction | int | str | float],
    magnetic: Fraction | int | str | float = Fraction(1, 2),
    sturm_bits: int = 80,
) -> list[VerifiedGapResult]:
    return [
        verify_gap(
            max_two_j=max_two_j,
            electric=electric,
            magnetic=magnetic,
            sturm_bits=sturm_bits,
        )
        for max_two_j in max_two_j_values
        for electric in electric_values
    ]
