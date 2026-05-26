from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class VQEGAPResult:
    ground_energy: float
    first_excited_energy: float
    gap: float
    exact_ground_energy: float
    exact_first_excited_energy: float
    exact_gap: float
    ground_error: float
    first_error: float
    gap_error: float
    backend: str
    n_qubits: int
    layers: int
    samples: int
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def estimate_gap_statevector(
    matrix: np.ndarray,
    *,
    n_qubits: int,
    layers: int = 2,
    samples: int = 128,
    seed: int = 7,
    penalty: float = 5.0,
) -> VQEGAPResult:
    """Tiny numpy statevector VQE-style gap estimate.

    This is a local variational quantum prototype. It is not a hardware result.
    The goal is to keep the optimization loop testable before wiring QPU
    backends.
    """

    arr = np.asarray(matrix, dtype=np.complex128)
    if isinstance(n_qubits, bool) or not isinstance(n_qubits, int) or n_qubits < 1:
        raise ValueError("n_qubits must be a positive integer")
    if arr.shape != (1 << n_qubits, 1 << n_qubits):
        raise ValueError("matrix shape must match n_qubits")
    try:
        finite_entries = bool(np.all(np.isfinite(arr)))
    except TypeError as exc:
        raise ValueError("matrix entries must be numeric and finite") from exc
    if not finite_entries:
        raise ValueError("matrix entries must be finite")
    if not np.allclose(arr, arr.conj().T, atol=1e-10):
        raise ValueError("matrix must be Hermitian")
    if isinstance(layers, bool) or not isinstance(layers, int) or layers < 1:
        raise ValueError("layers must be a positive integer")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 4:
        raise ValueError("samples must be an integer of at least 4")
    if not math.isfinite(float(penalty)) or penalty <= 0.0:
        raise ValueError("penalty must be positive and finite")

    exact = np.linalg.eigvalsh(arr)
    exact_ground = float(np.real(exact[0]))
    exact_first = float(np.real(exact[1]))
    exact_gap = max(0.0, exact_first - exact_ground)

    rng = np.random.default_rng(seed)
    n_params = n_qubits * layers

    _, ground_energy, ground_state = _optimize_state(
        arr, n_qubits, layers, n_params, samples, rng, forbidden_states=(), penalty=penalty
    )
    _, first_energy, _ = _optimize_state(
        arr, n_qubits, layers, n_params, samples, rng, forbidden_states=(ground_state,), penalty=penalty
    )

    gap = max(0.0, first_energy - ground_energy)
    gap_error = abs(gap - exact_gap)
    status = "pass" if gap_error <= max(0.05, 0.2 * max(exact_gap, 1e-9)) else "warning_variational_gap_error"

    return VQEGAPResult(
        ground_energy=float(ground_energy),
        first_excited_energy=float(first_energy),
        gap=float(gap),
        exact_ground_energy=exact_ground,
        exact_first_excited_energy=exact_first,
        exact_gap=exact_gap,
        ground_error=abs(float(ground_energy) - exact_ground),
        first_error=abs(float(first_energy) - exact_first),
        gap_error=float(gap_error),
        backend="local_numpy_statevector_vqe_style",
        n_qubits=n_qubits,
        layers=layers,
        samples=samples,
        status=status,
    )


def _optimize_state(
    matrix: np.ndarray,
    n_qubits: int,
    layers: int,
    n_params: int,
    samples: int,
    rng: np.random.Generator,
    *,
    forbidden_states: Sequence[np.ndarray],
    penalty: float,
) -> tuple[np.ndarray, float, np.ndarray]:
    best_theta = rng.uniform(-math.pi, math.pi, size=n_params)
    best_state = ansatz_state(best_theta, n_qubits=n_qubits, layers=layers)
    best_score = _objective(matrix, best_state, forbidden_states, penalty)

    for _ in range(samples):
        theta = rng.uniform(-math.pi, math.pi, size=n_params)
        state = ansatz_state(theta, n_qubits=n_qubits, layers=layers)
        score = _objective(matrix, state, forbidden_states, penalty)
        if score < best_score:
            best_theta, best_state, best_score = theta, state, score

    step = 0.25
    for _ in range(4):
        improved = False
        for index in range(n_params):
            for sign in (-1.0, 1.0):
                candidate = best_theta.copy()
                candidate[index] += sign * step
                state = ansatz_state(candidate, n_qubits=n_qubits, layers=layers)
                score = _objective(matrix, state, forbidden_states, penalty)
                if score < best_score:
                    best_theta, best_state, best_score = candidate, state, score
                    improved = True
        if not improved:
            step *= 0.5

    raw_energy = _energy(matrix, best_state)
    return best_theta, raw_energy, best_state


def _objective(
    matrix: np.ndarray,
    state: np.ndarray,
    forbidden_states: Sequence[np.ndarray],
    penalty: float,
) -> float:
    score = _energy(matrix, state)
    for forbidden in forbidden_states:
        overlap = abs(np.vdot(forbidden, state)) ** 2
        score += penalty * float(overlap)
    return float(score)


def _energy(matrix: np.ndarray, state: np.ndarray) -> float:
    return float(np.real(np.vdot(state, matrix @ state)))


def ansatz_state(theta: np.ndarray, *, n_qubits: int, layers: int) -> np.ndarray:
    if isinstance(n_qubits, bool) or not isinstance(n_qubits, int) or n_qubits < 1:
        raise ValueError("n_qubits must be a positive integer")
    if isinstance(layers, bool) or not isinstance(layers, int) or layers < 1:
        raise ValueError("layers must be a positive integer")
    if theta.size != n_qubits * layers:
        raise ValueError("theta size must equal n_qubits * layers")
    state = np.zeros(1 << n_qubits, dtype=np.complex128)
    state[0] = 1.0

    cursor = 0
    for _ in range(layers):
        for qubit in range(n_qubits):
            state = _apply_ry(state, float(theta[cursor]), qubit, n_qubits)
            cursor += 1
        for control in range(n_qubits - 1):
            state = _apply_cnot(state, control, control + 1, n_qubits)
    return state / np.linalg.norm(state)


def _apply_ry(state: np.ndarray, angle: float, qubit: int, n_qubits: int) -> np.ndarray:
    c = math.cos(angle / 2.0)
    s = math.sin(angle / 2.0)
    result = state.copy()
    bit = 1 << qubit
    for idx in range(state.size):
        if idx & bit:
            continue
        j = idx | bit
        a0 = state[idx]
        a1 = state[j]
        result[idx] = c * a0 - s * a1
        result[j] = s * a0 + c * a1
    return result


def _apply_cnot(state: np.ndarray, control: int, target: int, n_qubits: int) -> np.ndarray:
    if control == target:
        raise ValueError("control and target must differ")
    result = state.copy()
    cbit = 1 << control
    tbit = 1 << target
    for idx in range(state.size):
        if (idx & cbit) and not (idx & tbit):
            j = idx | tbit
            result[idx] = state[j]
            result[j] = state[idx]
    return result
