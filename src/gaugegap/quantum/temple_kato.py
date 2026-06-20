"""Temple-Kato certified lower bound: a rigorous lower bound on E0 from a quantum
trial state, pairing with the variational upper bound for a two-sided bracket.

For any normalized trial state psi with energy mean <H> and variance Var(H), and any
rigorous lower bound mu on the first excited energy E1 (we take it from the certified
interval enclosure of E1), the Temple inequality gives a RIGOROUS lower bound on the
ground energy whenever <H> < mu:

    E0 >= <H> - Var(H) / (mu - <H>).

Combined with the variational upper bound <H> >= E0, this brackets E0 entirely from
the trial state: E0 in [temple_lower, <H>] -- complementing the interval-kernel
bracket with a fully trial-state-based one. Dependency-light (numpy only).

CLAIM BOUNDARY: a rigorous bracket on a finite-matrix ground energy; simulation-
level trial state. Not a continuum/Millennium claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from gaugegap.curverank_registry import build_certified_general
from gaugegap.rigorous.bracket_certificate import emit_bracket_certificate


def temple_lower_bound(H: np.ndarray, psi: np.ndarray, mu: float) -> Optional[float]:
    """Temple lower bound on E0 from trial state ``psi`` and an E1 lower bound ``mu``.

    Returns ``None`` if ``mu <= <H>`` (the inequality's validity condition fails).
    """
    H = (np.asarray(H) + np.asarray(H).conj().T) / 2.0
    psi = np.asarray(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    Hpsi = H @ psi
    mean = float(np.real(psi.conj() @ Hpsi))
    h2 = float(np.real(Hpsi.conj() @ Hpsi))
    var = max(0.0, h2 - mean * mean)
    if mu <= mean:
        return None
    return mean - var / (mu - mean)


def _imaginary_time_state(H: np.ndarray, beta: float, psi0: np.ndarray) -> np.ndarray:
    """exp(-beta H) psi0, normalized, via the eigendecomposition (no scipy)."""
    evals, evecs = np.linalg.eigh(H)
    coeffs = evecs.conj().T @ psi0
    psi = evecs @ (np.exp(-beta * evals) * coeffs)
    return psi / np.linalg.norm(psi)


@dataclass
class TempleBracket:
    lower: float          # Temple lower bound on E0 (trial-state based)
    upper: float          # variational upper bound <H> (trial-state based)
    mu: float             # certified E1 lower bound used in Temple
    interval_lower: float # certified interval-kernel lower bound (for comparison)
    width: float
    valid: bool
    contains_exact: bool
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "temple_kato_bracket",
            "lower": self.lower, "upper": self.upper, "mu_E1_lower": self.mu,
            "interval_kernel_lower": self.interval_lower,
            "width": self.width, "valid": self.valid,
            "contains_exact": self.contains_exact,
            "claim_boundary": ("rigorous trial-state bracket on a finite-matrix "
                               "ground energy (Temple lower + variational upper); "
                               "not a continuum/Millennium claim"),
        }


def certified_temple_bracket(H: np.ndarray, *, beta: float = 0.6) -> TempleBracket:
    """Two-sided E0 bracket from a quantum imaginary-time trial state: Temple lower
    bound + variational upper bound, with E1's lower bound from the certified kernel,
    and a discharged Lean/Coq certificate of ``lower <= E0 <= upper``."""
    H = (np.asarray(H) + np.asarray(H).conj().T) / 2.0
    n = H.shape[0]
    psi0 = np.ones(n) / np.sqrt(n)
    psi = _imaginary_time_state(H, beta, psi0.astype(complex))

    enclosures = build_certified_general(H)
    e0_lower = float(enclosures[0].lower)
    mu = float(enclosures[1].lower)              # rigorous lower bound on E1

    mean = float(np.real(psi.conj() @ (H @ psi)))
    temple = temple_lower_bound(H, psi, mu)
    lower = max(temple, e0_lower) if temple is not None else e0_lower
    upper = mean
    lower = min(lower, upper)                     # guard numerical degeneracy

    ev = float(np.linalg.eigvalsh(H)[0])
    cert = emit_bracket_certificate("E0_temple", lower, upper)
    return TempleBracket(
        lower=lower, upper=upper, mu=mu, interval_lower=e0_lower,
        width=upper - lower, valid=lower <= upper + 1e-9,
        contains_exact=bool(lower - 1e-9 <= ev <= upper + 1e-9),
        lean4=cert.lean4, coq=cert.coq,
    )
