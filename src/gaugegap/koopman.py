"""Finite-data Koopman and dynamic-mode-decomposition diagnostics.

The routines in this module operate on finite sampled trajectories.  They are
useful for discovering coherent linear evolution in an observable space, but do
not prove that a finite-dimensional Koopman-invariant subspace exists for the
underlying continuous system.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


CLAIM_BOUNDARY = (
    "finite sampled DMD/Koopman approximation only; eigenvalues and modes depend "
    "on observables, sampling, truncation, and rank selection"
)


@dataclass(frozen=True)
class DMDResult:
    eigenvalues: np.ndarray
    continuous_eigenvalues: np.ndarray
    modes: np.ndarray
    amplitudes: np.ndarray
    singular_values: np.ndarray
    rank: int
    dt: float
    reconstruction_error: float
    spectral_radius: float
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "dt": self.dt,
            "reconstruction_error": self.reconstruction_error,
            "spectral_radius": self.spectral_radius,
            "eigenvalues": [
                {"real": float(value.real), "imag": float(value.imag)}
                for value in self.eigenvalues
            ],
            "continuous_eigenvalues": [
                {"real": float(value.real), "imag": float(value.imag)}
                for value in self.continuous_eigenvalues
            ],
            "singular_values": [float(value) for value in self.singular_values],
            "claim_boundary": self.claim_boundary,
        }


def _as_snapshots(states: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    values = np.asarray(states)
    if values.ndim != 2:
        raise ValueError("states must have shape (samples, observables)")
    if values.shape[0] < 3 or values.shape[1] < 1:
        raise ValueError("at least three samples and one observable are required")
    if not np.all(np.isfinite(values)):
        raise ValueError("states must be finite")
    return values.astype(np.complex128, copy=False)


def _select_rank(singular_values: np.ndarray, rank: int | None, energy: float) -> int:
    if singular_values.size == 0:
        raise ValueError("snapshot matrix has no singular values")
    if rank is not None:
        if rank < 1 or rank > singular_values.size:
            raise ValueError(f"rank must be in [1, {singular_values.size}]")
        return int(rank)
    if not 0.0 < energy <= 1.0:
        raise ValueError("energy must lie in (0, 1]")
    weights = singular_values**2
    total = float(np.sum(weights))
    if total == 0.0:
        return 1
    cumulative = np.cumsum(weights) / total
    return int(np.searchsorted(cumulative, energy, side="left") + 1)


def _phase_normalize_modes(modes: np.ndarray) -> np.ndarray:
    normalized = modes.copy()
    for column in range(normalized.shape[1]):
        mode = normalized[:, column]
        pivot = int(np.argmax(np.abs(mode)))
        value = mode[pivot]
        if abs(value) == 0.0:
            continue
        normalized[:, column] *= np.exp(-1j * np.angle(value))
    return normalized


def exact_dmd(
    states: Sequence[Sequence[float]] | np.ndarray,
    *,
    dt: float,
    rank: int | None = None,
    energy: float = 0.999,
    rcond: float = 1e-12,
) -> DMDResult:
    """Compute exact DMD from sequential finite snapshots.

    ``states`` is interpreted as ``samples x observables``.  The implementation
    follows the reduced SVD construction and reports a one-step reconstruction
    error on the supplied snapshot pairs.
    """
    if not np.isfinite(dt) or dt <= 0.0:
        raise ValueError("dt must be finite and positive")
    if rcond <= 0.0:
        raise ValueError("rcond must be positive")

    samples = _as_snapshots(states)
    x = samples[:-1].T
    y = samples[1:].T
    u, singular_values, vh = np.linalg.svd(x, full_matrices=False)
    chosen_rank = _select_rank(singular_values, rank, energy)

    u_r = u[:, :chosen_rank]
    s_r = singular_values[:chosen_rank]
    vh_r = vh[:chosen_rank, :]
    threshold = rcond * max(float(s_r[0]), 1.0)
    if np.any(s_r <= threshold):
        kept = int(np.count_nonzero(s_r > threshold))
        if kept < 1:
            raise np.linalg.LinAlgError("snapshot matrix is numerically rank deficient")
        chosen_rank = kept
        u_r = u_r[:, :kept]
        s_r = s_r[:kept]
        vh_r = vh_r[:kept, :]

    inverse_s = np.diag(1.0 / s_r)
    reduced = u_r.conj().T @ y @ vh_r.conj().T @ inverse_s
    eigenvalues, eigenvectors = np.linalg.eig(reduced)
    modes = y @ vh_r.conj().T @ inverse_s @ eigenvectors
    modes = _phase_normalize_modes(modes)

    amplitudes, *_ = np.linalg.lstsq(modes, samples[0], rcond=rcond)
    predicted_y = modes @ np.diag(eigenvalues) @ np.linalg.pinv(modes, rcond=rcond) @ x
    denominator = max(float(np.linalg.norm(y)), np.finfo(float).tiny)
    reconstruction_error = float(np.linalg.norm(y - predicted_y) / denominator)

    continuous = np.log(eigenvalues.astype(np.complex128)) / dt
    return DMDResult(
        eigenvalues=eigenvalues,
        continuous_eigenvalues=continuous,
        modes=modes,
        amplitudes=amplitudes,
        singular_values=singular_values,
        rank=chosen_rank,
        dt=float(dt),
        reconstruction_error=reconstruction_error,
        spectral_radius=float(np.max(np.abs(eigenvalues))),
    )


def reconstruct(result: DMDResult, samples: int) -> np.ndarray:
    """Reconstruct ``samples`` snapshots from a fitted DMD model."""
    if samples < 1:
        raise ValueError("samples must be positive")
    powers = np.arange(samples, dtype=int)
    dynamics = result.amplitudes[:, None] * result.eigenvalues[:, None] ** powers[None, :]
    return (result.modes @ dynamics).T


def hankel_embed(
    signal: Sequence[float] | np.ndarray,
    *,
    delays: int,
    stride: int = 1,
) -> np.ndarray:
    """Create a delay-coordinate embedding for scalar or vector observations."""
    values = np.asarray(signal)
    if values.ndim == 1:
        values = values[:, None]
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("signal must be a finite one- or two-dimensional array")
    if delays < 1 or stride < 1:
        raise ValueError("delays and stride must be positive")
    required = 1 + (delays - 1) * stride
    rows = values.shape[0] - required + 1
    if rows < 3:
        raise ValueError("signal is too short for the requested embedding")
    return np.concatenate(
        [values[offset * stride : offset * stride + rows] for offset in range(delays)],
        axis=1,
    )


def dominant_modes(result: DMDResult, count: int = 8) -> list[dict[str, float]]:
    """Return modes ranked by initial amplitude magnitude."""
    if count < 1:
        raise ValueError("count must be positive")
    order = np.argsort(np.abs(result.amplitudes))[::-1][:count]
    records: list[dict[str, float]] = []
    for index in order:
        discrete = result.eigenvalues[index]
        continuous = result.continuous_eigenvalues[index]
        records.append(
            {
                "index": int(index),
                "amplitude": float(abs(result.amplitudes[index])),
                "discrete_magnitude": float(abs(discrete)),
                "growth_rate": float(continuous.real),
                "frequency_hz": float(abs(continuous.imag) / (2.0 * np.pi)),
            }
        )
    return records
