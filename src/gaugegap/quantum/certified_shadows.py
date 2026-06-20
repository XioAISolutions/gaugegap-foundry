"""Certified classical shadows: observable estimates with rigorous confidence bands.

Implements the Huang-Kueng-Preskill random-Pauli classical-shadow estimator with a
**median-of-means** aggregation over independent shadow batches and a confidence
interval (reusing `repeated_runs.confidence_interval`), then cross-validates against
the exact expectation. Median-of-means is the standard robust shadow estimator (it
tames heavy-tailed single-shot variance), giving an estimate plus an honest
statistical band rather than a bare point value.

(The repo's older `shadow_tomography.classical_shadow_pauli` did not reproduce
arbitrary-observable expectations correctly, so this module implements the protocol
directly and is unit-tested against exact values.)

CLAIM BOUNDARY: a statistical confidence band on a finite-state observable at a
fixed shot budget. Not a continuum or Millennium claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from gaugegap.seeding import child_seeds, make_rng
from gaugegap.repeated_runs import confidence_interval

# Single-qubit rotations R with R P R^dag = Z (so measuring Z after R = measuring P).
_H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
_Sdg = np.array([[1, 0], [0, -1j]], dtype=complex)
_ROT = {"Z": np.eye(2, dtype=complex), "X": _H, "Y": _H @ _Sdg}
_KET = {0: np.array([1, 0], dtype=complex), 1: np.array([0, 1], dtype=complex)}


def median_of_means(samples, n_batches: int) -> float:
    """Median-of-means of a flat sample array split into ``n_batches`` groups."""
    arr = np.asarray(list(samples), dtype=float)
    if arr.size == 0:
        raise ValueError("no samples")
    n_batches = max(1, min(n_batches, arr.size))
    return float(np.median([g.mean() for g in np.array_split(arr, n_batches)]))


def _shadow_batch(psi: np.ndarray, observables: Dict[str, np.ndarray],
                  n_qubits: int, n_snapshots: int, rng) -> Dict[str, float]:
    """One shadow batch: mean over ``n_snapshots`` single-shot estimators."""
    acc = {name: 0.0 for name in observables}
    dim = 1 << n_qubits
    for _ in range(n_snapshots):
        bases = [rng.choice(("X", "Y", "Z")) for _ in range(n_qubits)]
        U = _ROT[bases[0]]
        for q in range(1, n_qubits):
            U = np.kron(U, _ROT[bases[q]])
        phi = U @ psi
        probs = np.abs(phi) ** 2
        probs = probs / probs.sum()
        idx = int(rng.choice(dim, p=probs))
        bits = [(idx >> (n_qubits - 1 - q)) & 1 for q in range(n_qubits)]
        rho = np.array([[1.0 + 0j]])
        for q in range(n_qubits):
            Uq = _ROT[bases[q]]
            proj = np.outer(_KET[bits[q]], _KET[bits[q]].conj())
            rho = np.kron(rho, 3.0 * (Uq.conj().T @ proj @ Uq) - np.eye(2))
        for name, obs in observables.items():
            acc[name] += float(np.real(np.trace(obs @ rho)))
    return {name: v / n_snapshots for name, v in acc.items()}


@dataclass
class ShadowEstimate:
    observable: str
    estimate: float           # median over batches
    ci_low: float
    ci_high: float
    exact: float
    covered: bool             # exact value inside the CI
    abs_error: float

    def to_dict(self) -> dict:
        return {
            "observable": self.observable, "estimate": self.estimate,
            "ci": [self.ci_low, self.ci_high], "exact": self.exact,
            "covered": self.covered, "abs_error": self.abs_error,
        }


def _exact_expectation(state: np.ndarray, obs: np.ndarray) -> float:
    psi = np.asarray(state, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    return float(np.real(psi.conj() @ (np.asarray(obs, dtype=complex) @ psi)))


def certified_shadow_estimate(
    state: np.ndarray,
    observables: Dict[str, np.ndarray],
    *,
    n_snapshots: int = 800,
    n_batches: int = 12,
    level: float = 0.95,
    seed: int = 1234,
) -> Dict[str, ShadowEstimate]:
    """Median-of-means classical-shadow estimate + confidence band per observable,
    cross-validated against the exact expectation.

    Runs the shadow protocol over ``n_batches`` independent child seeds; each batch
    yields one mean estimate per observable. The robust point estimate is the median
    of the batch estimates; the CI is the normal-approximation interval over batches.
    """
    psi = np.asarray(state, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    n = psi.shape[0]
    n_qubits = int(round(np.log2(n)))
    if (1 << n_qubits) != n:
        raise ValueError("state dimension must be a power of two")

    seeds = child_seeds(seed, n_batches)
    per_obs: Dict[str, List[float]] = {name: [] for name in observables}
    for s in seeds:
        batch = _shadow_batch(psi, observables, n_qubits, n_snapshots, make_rng(int(s)))
        for name, val in batch.items():
            per_obs[name].append(val)

    out: Dict[str, ShadowEstimate] = {}
    for name, obs in observables.items():
        vals = per_obs[name]
        stats = confidence_interval(vals, level=level)
        est = float(np.median(vals))
        exact = _exact_expectation(psi, obs)
        out[name] = ShadowEstimate(
            observable=name, estimate=est,
            ci_low=stats.ci_low, ci_high=stats.ci_high, exact=exact,
            covered=bool(stats.ci_low - 1e-9 <= exact <= stats.ci_high + 1e-9),
            abs_error=abs(est - exact),
        )
    return out
