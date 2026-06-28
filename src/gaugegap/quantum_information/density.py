"""Finite-dimensional density-matrix helpers with fail-closed validation."""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def normalize_state(state: Iterable[complex]) -> np.ndarray:
    vector = np.asarray(tuple(state), dtype=np.complex128)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError("state must be a non-empty vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError("state must be finite")
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise ValueError("state norm must be positive")
    return vector / norm


def density_matrix(state: Iterable[complex]) -> np.ndarray:
    vector = normalize_state(state)
    return np.outer(vector, vector.conj())


def _validate_density(rho: np.ndarray) -> np.ndarray:
    matrix = np.asarray(rho, dtype=np.complex128)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("density operator must be square")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("density operator must be finite")
    return matrix


def partial_trace(rho: np.ndarray, dims: Iterable[int], keep: Iterable[int]) -> np.ndarray:
    matrix = _validate_density(rho)
    dimensions = [int(value) for value in dims]
    if any(value <= 0 for value in dimensions):
        raise ValueError("subsystem dimensions must be positive")
    total = math.prod(dimensions)
    if matrix.shape != (total, total):
        raise ValueError("density shape does not match subsystem dimensions")
    kept = sorted(set(int(index) for index in keep))
    if any(index < 0 or index >= len(dimensions) for index in kept):
        raise ValueError("kept subsystem index out of range")
    tensor = matrix.reshape(tuple(dimensions) + tuple(dimensions))
    current_dims = dimensions[:]
    traced = [index for index in range(len(dimensions)) if index not in kept]
    for axis in sorted(traced, reverse=True):
        count = len(current_dims)
        tensor = np.trace(tensor, axis1=axis, axis2=axis + count)
        current_dims.pop(axis)
    output_dim = math.prod(current_dims) if current_dims else 1
    return np.asarray(tensor, dtype=np.complex128).reshape(output_dim, output_dim)


def purity(rho: np.ndarray) -> float:
    matrix = _validate_density(rho)
    return float(np.real(np.trace(matrix @ matrix)))


def von_neumann_entropy(rho: np.ndarray, *, base: float = 2.0, tolerance: float = 1e-14) -> float:
    matrix = _validate_density(rho)
    hermitian = (matrix + matrix.conj().T) / 2.0
    values = np.linalg.eigvalsh(hermitian)
    values = values[values > tolerance]
    if values.size == 0:
        return 0.0
    return float(-np.sum(values * np.log(values)) / np.log(base))


def trace_distance(left: np.ndarray, right: np.ndarray) -> float:
    a = _validate_density(left)
    b = _validate_density(right)
    if a.shape != b.shape:
        raise ValueError("density operators must have matching shapes")
    delta = (a - b + (a - b).conj().T) / 2.0
    return float(0.5 * np.sum(np.abs(np.linalg.eigvalsh(delta))))


def pure_state_fidelity(rho: np.ndarray, state: Iterable[complex]) -> float:
    matrix = _validate_density(rho)
    vector = normalize_state(state)
    if matrix.shape != (vector.size, vector.size):
        raise ValueError("state dimension does not match density operator")
    value = np.vdot(vector, matrix @ vector)
    return float(np.clip(np.real(value), 0.0, 1.0))


def mutual_information(rho_ab: np.ndarray, dims: tuple[int, int]) -> float:
    matrix = _validate_density(rho_ab)
    rho_a = partial_trace(matrix, dims, keep=(0,))
    rho_b = partial_trace(matrix, dims, keep=(1,))
    return von_neumann_entropy(rho_a) + von_neumann_entropy(rho_b) - von_neumann_entropy(matrix)


def bloch_vector(rho: np.ndarray) -> tuple[float, float, float]:
    matrix = _validate_density(rho)
    if matrix.shape != (2, 2):
        raise ValueError("Bloch vectors are defined here for one qubit")
    x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    return tuple(float(np.real(np.trace(matrix @ operator))) for operator in (x, y, z))
