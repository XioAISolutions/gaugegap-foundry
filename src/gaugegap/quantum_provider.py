"""Provider-neutral quantum execution contract with a local reference backend."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol

import numpy as np


@dataclass(frozen=True)
class ProviderCapabilities:
    provider_id: str
    simulator: bool
    hardware: bool
    max_qubits: int
    supports_counts: bool = True
    supports_expectation: bool = True


@dataclass(frozen=True)
class CalibrationSnapshot:
    provider_id: str
    calibration_id: str
    readout_matrix: tuple[tuple[float, float], tuple[float, float]] | None = None
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class QuantumExecutionRequest:
    operation: str
    statevector: tuple[complex, ...]
    shots: int = 1024
    seed: int = 0
    qubit: int = 0


@dataclass(frozen=True)
class QuantumExecutionResult:
    provider_id: str
    operation: str
    counts: Mapping[str, int] | None
    expectation: float | None
    shots: int
    seed: int
    metadata: Mapping[str, object]

    def summary(self) -> dict[str, Any]:
        return asdict(self)


class QuantumProvider(Protocol):
    def capabilities(self) -> ProviderCapabilities: ...
    def execute(self, request: QuantumExecutionRequest) -> QuantumExecutionResult: ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, QuantumProvider] = {}

    def register(self, provider: QuantumProvider) -> None:
        provider_id = provider.capabilities().provider_id
        if provider_id in self._providers:
            raise ValueError(f"provider already registered: {provider_id}")
        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> QuantumProvider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"unknown provider: {provider_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))


def _validated_statevector(values: tuple[complex, ...]) -> np.ndarray:
    state = np.asarray(values, dtype=np.complex128)
    if state.ndim != 1 or state.size < 2 or state.size & (state.size - 1):
        raise ValueError("statevector length must be a power of two")
    if not np.all(np.isfinite(state)):
        raise ValueError("statevector must be finite")
    norm = float(np.linalg.norm(state))
    if norm <= 0.0:
        raise ValueError("statevector norm must be positive")
    return state / norm


class LocalStatevectorProvider:
    """Deterministic seeded reference backend; not a hardware claim."""

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities("local-statevector", True, False, 20)

    def execute(self, request: QuantumExecutionRequest) -> QuantumExecutionResult:
        state = _validated_statevector(request.statevector)
        qubits = int(np.log2(state.size))
        if request.qubit < 0 or request.qubit >= qubits:
            raise ValueError("qubit index outside statevector")
        probabilities = np.abs(state) ** 2
        operation = request.operation
        counts: dict[str, int] | None = None
        expectation: float | None = None
        if operation == "sample_statevector":
            if request.shots <= 0:
                raise ValueError("shots must be positive")
            rng = np.random.default_rng(request.seed)
            samples = rng.choice(state.size, size=request.shots, p=probabilities)
            width = qubits
            counts = {}
            for sample in samples:
                key = format(int(sample), f"0{width}b")
                counts[key] = counts.get(key, 0) + 1
        elif operation == "expectation_pauli_z":
            mask = 1 << request.qubit
            signs = np.array([1.0 if index & mask == 0 else -1.0 for index in range(state.size)])
            expectation = float(np.dot(probabilities, signs))
        else:
            raise ValueError(f"unsupported operation: {operation}")
        return QuantumExecutionResult(
            provider_id=self.capabilities().provider_id,
            operation=operation,
            counts=counts,
            expectation=expectation,
            shots=request.shots,
            seed=request.seed,
            metadata={"qubits": qubits, "normalized": True, "claim_boundary": "local finite simulation only"},
        )


def mitigate_binary_counts(
    counts: Mapping[str, int],
    readout_matrix: tuple[tuple[float, float], tuple[float, float]],
) -> dict[str, float]:
    """Invert a one-qubit readout matrix, clip negatives, and renormalize."""
    total = int(counts.get("0", 0)) + int(counts.get("1", 0))
    if total <= 0:
        raise ValueError("counts must contain positive one-qubit shots")
    matrix = np.asarray(readout_matrix, dtype=float)
    if matrix.shape != (2, 2) or not np.all(np.isfinite(matrix)):
        raise ValueError("readout matrix must be finite 2x2")
    if abs(float(np.linalg.det(matrix))) < 1e-12:
        raise ValueError("readout matrix must be invertible")
    measured = np.array([counts.get("0", 0), counts.get("1", 0)], dtype=float) / total
    corrected = np.linalg.solve(matrix, measured)
    corrected = np.clip(corrected, 0.0, None)
    normalizer = float(corrected.sum())
    if normalizer <= 0.0:
        raise ValueError("mitigation produced zero probability")
    corrected /= normalizer
    return {"0": float(corrected[0]), "1": float(corrected[1])}
