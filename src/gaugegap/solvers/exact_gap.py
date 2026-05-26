from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np


@dataclass(frozen=True)
class GapResult:
    eigenvalues: list[float]
    ground_energy: float
    first_excited_energy: float
    gap: float
    residual_norm: float
    degeneracy_warning: bool
    method: str
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def exact_gap(matrix: np.ndarray, *, degeneracy_tol: float = 1e-10) -> GapResult:
    """Compute the finite-system spectral gap with dense exact diagonalization."""

    arr = np.asarray(matrix)
    try:
        tol = float(degeneracy_tol)
    except (TypeError, ValueError) as exc:
        raise ValueError("degeneracy_tol must be a non-negative finite number") from exc
    if not math.isfinite(tol) or tol < 0.0:
        raise ValueError("degeneracy_tol must be a non-negative finite number")
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError("matrix must be square")
    if arr.shape[0] < 2:
        raise ValueError("matrix must have dimension at least 2")
    try:
        finite_entries = bool(np.all(np.isfinite(arr)))
    except TypeError as exc:
        raise ValueError("matrix entries must be numeric and finite") from exc
    if not finite_entries:
        raise ValueError("matrix entries must be finite")
    if not np.allclose(arr, arr.conj().T, atol=1e-10):
        raise ValueError("matrix must be Hermitian")

    eigenvalues, eigenvectors = np.linalg.eigh(arr)
    eigenvalues = np.real_if_close(eigenvalues).astype(float)
    ground = float(eigenvalues[0])
    first = float(eigenvalues[1])
    gap = max(0.0, first - ground)

    residuals = []
    for index in range(min(2, arr.shape[0])):
        vec = eigenvectors[:, index]
        residuals.append(float(np.linalg.norm(arr @ vec - eigenvalues[index] * vec)))
    residual_norm = max(residuals) if residuals else math.nan

    degeneracy_warning = bool(abs(first - ground) <= tol)
    status = "finite_system_verified" if residual_norm <= 1e-8 else "warning_high_residual"

    return GapResult(
        eigenvalues=[float(x) for x in eigenvalues],
        ground_energy=ground,
        first_excited_energy=first,
        gap=gap,
        residual_norm=residual_norm,
        degeneracy_warning=degeneracy_warning,
        method="dense_exact_diagonalization",
        status=status,
    )
