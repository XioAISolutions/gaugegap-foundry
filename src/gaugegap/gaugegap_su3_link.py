"""Single-link SU(3) electric Hamiltonian (Kogut-Susskind strong-coupling).

This is a *defensible* finite SU(3) gauge truncation (issue #12, A3): genuine
SU(3) representation-theory structure, exactly diagonalizable, real physics
rather than a stand-in. It implements the electric term of the Kogut-Susskind
Hamiltonian lattice gauge theory for a single gauge link,

    H_E = (g^2 / 2) * sum_a (E^a)^2 = (g^2 / 2) * C2(R),

where the link Hilbert space is spanned by the SU(3) irreducible representations
R = (p, q). On a single link the colour-electric energy is the quadratic Casimir
C2(R) of the representation carried by the link; each irrep contributes
dim(R)^2 basis states (left and right colour indices), all degenerate at energy
(g^2/2) C2(R). The basis is truncated by an irrep cutoff (p, q <= cutoff), which
is the standard strong-coupling truncation.

Everything here is exact: the Casimir C2(p,q) = (p^2 + q^2 + p q)/3 + (p + q)
and the dimension dim(p,q) = (p+1)(q+1)(p+q+2)/2 are textbook SU(3) identities,
so the spectrum, ground state, and gap are known in closed form.

CLAIM BOUNDARY:
A single-link SU(3) electric (strong-coupling) Hamiltonian, exactly diagonalized
in a truncated irrep basis. This is genuine finite SU(3) gauge structure, but it
is one link with NO magnetic/plaquette dynamics, NO continuum limit, and NO
Yang-Mills mass-gap claim. It is a finite-system benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np

IMPLEMENTATION_STATUS = "exact_finite_truncation"
CLAIM_BOUNDARY = (
    "Single-link SU(3) electric (Kogut-Susskind strong-coupling) Hamiltonian, "
    "exact in a truncated irrep basis; no plaquette dynamics, no continuum or "
    "Yang-Mills mass-gap claim."
)


def su3_dim(p: int, q: int) -> int:
    """Dimension of the SU(3) irrep (p, q): (p+1)(q+1)(p+q+2)/2."""
    if p < 0 or q < 0:
        raise ValueError("Dynkin labels (p, q) must be non-negative")
    return (p + 1) * (q + 1) * (p + q + 2) // 2


def su3_casimir(p: int, q: int) -> Fraction:
    """Exact quadratic Casimir C2(p, q) = (p^2+q^2+pq)/3 + (p+q).

    Normalized so the fundamental (1, 0) has C2 = 4/3 and the adjoint (1, 1) has
    C2 = 3.
    """
    if p < 0 or q < 0:
        raise ValueError("Dynkin labels (p, q) must be non-negative")
    return Fraction(p * p + q * q + p * q, 3) + Fraction(p + q)


@dataclass(frozen=True)
class SU3Irrep:
    p: int
    q: int

    @property
    def dim(self) -> int:
        return su3_dim(self.p, self.q)

    @property
    def casimir(self) -> Fraction:
        return su3_casimir(self.p, self.q)

    @property
    def label(self) -> str:
        names = {(0, 0): "1", (1, 0): "3", (0, 1): "3bar", (1, 1): "8",
                 (2, 0): "6", (0, 2): "6bar", (3, 0): "10", (0, 3): "10bar"}
        return names.get((self.p, self.q), f"({self.p},{self.q})")


def enumerate_irreps(cutoff: int) -> list[SU3Irrep]:
    """All SU(3) irreps (p, q) with 0 <= p, q <= cutoff, sorted by (C2, p, q)."""
    if cutoff < 0:
        raise ValueError("cutoff must be non-negative")
    irreps = [SU3Irrep(p, q) for p in range(cutoff + 1) for q in range(cutoff + 1)]
    return sorted(irreps, key=lambda r: (r.casimir, r.p, r.q))


@dataclass(frozen=True)
class SU3LinkElectricConfig:
    """Configuration for the single-link SU(3) electric Hamiltonian."""

    g_electric: float = 1.0
    cutoff: int = 2  # include irreps with p, q <= cutoff

    def __post_init__(self) -> None:
        if not (self.g_electric > 0):
            raise ValueError("g_electric must be positive")
        if self.cutoff < 1:
            raise ValueError("cutoff must be at least 1 (to include the fundamental)")


class SU3LinkElectric:
    """Exact single-link SU(3) electric Hamiltonian in the truncated irrep basis."""

    def __init__(self, config: SU3LinkElectricConfig):
        self.config = config
        self.irreps = enumerate_irreps(config.cutoff)
        # Each irrep R contributes dim(R)^2 degenerate basis states.
        self.multiplicities = [r.dim * r.dim for r in self.irreps]
        self.hilbert_dim = sum(self.multiplicities)

    def _energy(self, irrep: SU3Irrep) -> float:
        return 0.5 * self.config.g_electric ** 2 * float(irrep.casimir)

    def hamiltonian_dense(self) -> np.ndarray:
        """Dense (diagonal) electric Hamiltonian over the truncated basis."""
        diag = []
        for irrep, mult in zip(self.irreps, self.multiplicities):
            diag.extend([self._energy(irrep)] * mult)
        return np.diag(np.array(diag, dtype=np.float64))

    def spectrum(self) -> np.ndarray:
        return np.sort(np.diag(self.hamiltonian_dense()))

    def levels(self) -> list[dict[str, Any]]:
        """Distinct energy levels with their irrep content and degeneracy."""
        by_energy: dict[float, dict[str, Any]] = {}
        for irrep, mult in zip(self.irreps, self.multiplicities):
            e = self._energy(irrep)
            slot = by_energy.setdefault(
                e, {"energy": e, "casimir": float(irrep.casimir), "irreps": [], "degeneracy": 0}
            )
            slot["irreps"].append(irrep.label)
            slot["degeneracy"] += mult
        return [by_energy[e] for e in sorted(by_energy)]

    def compute_gap(self) -> dict[str, Any]:
        """Ground energy and electric mass gap (exact)."""
        levels = self.levels()
        ground = levels[0]
        # The first *excited* energy level (not the degenerate ground multiplet).
        first = levels[1] if len(levels) > 1 else levels[0]
        return {
            "implementation_status": IMPLEMENTATION_STATUS,
            "claim_boundary": CLAIM_BOUNDARY,
            "method": "exact_diagonalization",
            "hilbert_dim": self.hilbert_dim,
            "ground_energy": ground["energy"],
            "ground_degeneracy": ground["degeneracy"],
            "first_excited_energy": first["energy"],
            "gap": first["energy"] - ground["energy"],
            "n_irreps": len(self.irreps),
        }


def electric_gap_closed_form(g_electric: float) -> float:
    """Exact electric gap = (g^2/2) * C2(fundamental) = 2 g^2 / 3."""
    return 0.5 * g_electric ** 2 * float(su3_casimir(1, 0))
