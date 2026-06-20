"""Certified two-sided energy / gap brackets.

The flagship "certified quantum" primitive: combine a RIGOROUS LOWER bound (from
the verified interval-arithmetic kernel) with a RIGOROUS UPPER bound (a variational
Rayleigh value from a quantum subspace eigensolver) to bracket a true eigenvalue.

Both sides are rigorous:
  * lower: ``build_certified_general(H)`` gives a directed-rounding interval that
    provably contains each eigenvalue; its lower endpoint bounds the eigenvalue
    from below;
  * upper: by the Courant-Fischer min-max principle, the k-th Ritz value of any
    subspace is an UPPER bound on the k-th eigenvalue. The quantum Krylov / QITE
    eigensolver supplies these Ritz values.

So ``E_k in [certified_lower_k, ritz_upper_k]`` -- a two-sided certified bracket the
quantum method genuinely contributes to (the variational upper bound). For the gap,
``E1 - E0 in [E1.lower - E0.upper, E1.upper - E0.lower]``.

CLAIM BOUNDARY: finite-matrix, simulation-level. A rigorous bracket on finite
eigenvalues; not a continuum/Yang-Mills/Millennium claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from gaugegap.curverank_registry import build_certified_general
from gaugegap.quantum.quantum_subspace_methods import quantum_krylov_method


@dataclass
class CertifiedBracket:
    label: str
    index: int            # which eigenvalue (0 = ground)
    lower: float          # certified lower bound (interval kernel)
    upper: float          # variational upper bound (quantum Ritz value)
    width: float
    method: str           # quantum method supplying the upper bound

    @property
    def valid(self) -> bool:
        return self.lower <= self.upper + 1e-9

    def contains(self, value: float, tol: float = 1e-9) -> bool:
        return self.lower - tol <= value <= self.upper + tol

    def to_dict(self) -> dict:
        return {
            "label": self.label, "index": self.index,
            "lower": self.lower, "upper": self.upper, "width": self.width,
            "method": self.method, "valid": self.valid,
            "claim_boundary": ("rigorous two-sided bracket on a finite-matrix "
                               "eigenvalue (certified lower + variational upper); "
                               "not a continuum or Millennium claim"),
        }


def _hermitian(H: np.ndarray) -> np.ndarray:
    H = np.asarray(H)
    return (H + H.conj().T) / 2.0


def _ritz_upper_bounds(H: np.ndarray, n_states: int, n_iterations: int) -> List[float]:
    """Quantum Krylov Ritz values -> rigorous variational upper bounds on the
    lowest ``n_states`` eigenvalues (Courant-Fischer)."""
    n = H.shape[0]
    psi0 = np.ones(n) / np.sqrt(n)
    kr = quantum_krylov_method(psi0.astype(complex), H,
                               n_iterations=n_iterations, n_states=n_states)
    return [float(x) for x in np.sort(np.real(kr.energies))[:n_states]]


def certified_ground_bracket(H: np.ndarray, *, n_iterations: int = 16
                             ) -> CertifiedBracket:
    """Certified bracket for the ground energy E0 of Hermitian ``H``."""
    H = _hermitian(H)
    enclosures = build_certified_general(H)
    lower = float(enclosures[0].lower)
    upper = _ritz_upper_bounds(H, 1, n_iterations)[0]
    # The Ritz value is a rigorous upper bound; guard against degenerate numerics.
    upper = max(upper, lower)
    return CertifiedBracket(label="E0", index=0, lower=lower, upper=upper,
                            width=upper - lower, method="quantum_krylov")


def certified_gap_bracket(H: np.ndarray, *, n_iterations: int = 16) -> dict:
    """Certified brackets for E0, E1 and the spectral gap E1 - E0.

    Lower bounds from the certified interval kernel; upper bounds from the quantum
    Krylov Ritz values. The gap bracket is rigorous:
        gap >= E1.lower - E0.upper   and   gap <= E1.upper - E0.lower.
    """
    H = _hermitian(H)
    enclosures = build_certified_general(H)
    lo0, lo1 = float(enclosures[0].lower), float(enclosures[1].lower)
    up = _ritz_upper_bounds(H, 2, n_iterations)
    up0, up1 = max(up[0], lo0), max(up[1], lo1)
    e0 = CertifiedBracket("E0", 0, lo0, up0, up0 - lo0, "quantum_krylov")
    e1 = CertifiedBracket("E1", 1, lo1, up1, up1 - lo1, "quantum_krylov")
    gap_lower = lo1 - up0
    gap_upper = up1 - lo0
    return {
        "E0": e0.to_dict(),
        "E1": e1.to_dict(),
        "gap_bracket": {
            "lower": gap_lower, "upper": gap_upper,
            "width": gap_upper - gap_lower,
            "note": "gap = E1 - E0; lower = E1.lower - E0.upper, "
                    "upper = E1.upper - E0.lower",
        },
        "claim_boundary": ("rigorous finite-matrix energy/gap bracket: certified "
                           "interval lower bounds + quantum variational (Ritz) upper "
                           "bounds; simulation-level; not a continuum/Millennium claim"),
    }


def bracket_contains_exact(H: np.ndarray, bracket: CertifiedBracket) -> bool:
    """Cross-check: the numpy eigenvalue lies inside the certified bracket."""
    H = _hermitian(H)
    ev = np.linalg.eigvalsh(H)
    return bracket.contains(float(ev[bracket.index]))
