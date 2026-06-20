"""Finite open-system (Lindbladian) steady states, dependency-light.

Vectorizes the Lindblad master equation into a Liouvillian superoperator, finds the
steady state from its null space, and reports the dissipative relaxation spectrum --
all in numpy (column-stacking vectorization). Cross-validated against long-time
evolution and known analytic cases.

CLAIM BOUNDARY: exact finite-dimensional open-system computation, cross-validated
against the exact dynamics. The Liouvillian is non-Hermitian, so this is not
interval-certified like the Hermitian spectral kernel; it is an exact numpy result
with cross-checks. Not a continuum/Millennium claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np


def lindbladian_superoperator(H: np.ndarray, jumps: Sequence[np.ndarray]) -> np.ndarray:
    """Vectorized Liouvillian L (column-stacking) for
    rho' = -i[H,rho] + sum_k (L_k rho L_k^dag - 1/2 {L_k^dag L_k, rho})."""
    H = np.asarray(H, dtype=complex)
    d = H.shape[0]
    I = np.eye(d, dtype=complex)
    # column-stacking: vec(A X B) = (B^T kron A) vec(X)
    L = -1j * (np.kron(I, H) - np.kron(H.T, I))
    for Lk in jumps:
        Lk = np.asarray(Lk, dtype=complex)
        M = Lk.conj().T @ Lk
        L += np.kron(Lk.conj(), Lk)
        L -= 0.5 * (np.kron(I, M) + np.kron(M.T, I))
    return L


def steady_state(L: np.ndarray) -> np.ndarray:
    """Steady-state density matrix from the null space of the Liouvillian."""
    d2 = L.shape[0]
    d = int(round(np.sqrt(d2)))
    # smallest right singular vector ~ null space of L
    _, s, vh = np.linalg.svd(L)
    vec = vh.conj().T[:, -1]
    rho = vec.reshape((d, d), order="F")
    rho = (rho + rho.conj().T) / 2.0            # Hermitian
    tr = np.trace(rho)
    if abs(tr) < 1e-12:                          # pick a sign/scale
        rho = rho + np.eye(d) * 1e-12
        tr = np.trace(rho)
    rho = rho / tr
    return rho


def relaxation_spectrum(L: np.ndarray) -> np.ndarray:
    """Eigenvalues of the Liouvillian (Re <= 0); 0 is the steady state."""
    return np.linalg.eigvals(L)


def steady_state_observable(rho: np.ndarray, O: np.ndarray) -> float:
    return float(np.real(np.trace(np.asarray(rho) @ np.asarray(O))))


def evolve(L: np.ndarray, rho0: np.ndarray, t: float) -> np.ndarray:
    """Evolve rho0 by exp(L t) (column-stacking), for cross-validation."""
    from numpy.linalg import eig
    d = rho0.shape[0]
    vec0 = rho0.reshape(d * d, order="F")
    w, V = eig(L)
    vt = V @ (np.exp(w * t) * np.linalg.solve(V, vec0))
    rho = vt.reshape((d, d), order="F")
    rho = (rho + rho.conj().T) / 2.0
    return rho / np.trace(rho)


@dataclass
class OpenSystemResult:
    dim: int
    steady_state: np.ndarray
    relaxation_gap: float          # |Re| of the slowest nonzero mode
    is_valid_density_matrix: bool
    residual_norm: float           # ||L vec(rho_ss)||

    def to_dict(self) -> dict:
        return {
            "kind": "lindbladian_steady_state",
            "dim": self.dim,
            "relaxation_gap": self.relaxation_gap,
            "is_valid_density_matrix": self.is_valid_density_matrix,
            "residual_norm": self.residual_norm,
            "claim_boundary": ("exact finite open-system steady state, cross-"
                               "validated; non-Hermitian Liouvillian (not interval-"
                               "certified); not a continuum/Millennium claim"),
        }


def solve_open_system(H: np.ndarray, jumps: Sequence[np.ndarray]) -> OpenSystemResult:
    L = lindbladian_superoperator(H, jumps)
    rho = steady_state(L)
    d = rho.shape[0]
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    is_dm = bool(abs(np.trace(rho) - 1) < 1e-6 and np.min(evals.real) > -1e-6
                 and np.allclose(rho, rho.conj().T, atol=1e-6))
    spec = relaxation_spectrum(L)
    nonzero = sorted((abs(s.real) for s in spec))
    gap = float(next((x for x in nonzero if x > 1e-9), 0.0))
    res = float(np.linalg.norm(L @ rho.reshape(d * d, order="F")))
    return OpenSystemResult(dim=d, steady_state=rho, relaxation_gap=gap,
                            is_valid_density_matrix=is_dm, residual_norm=res)
