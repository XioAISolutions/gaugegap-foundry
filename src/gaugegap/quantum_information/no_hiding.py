"""Finite three-qubit realization and audit of the quantum no-hiding theorem.

The circuit acts on (system S, environment A, recovery B):

    SWAP(S, B) -> H(S) -> CNOT(S, A)

For an input |psi>_S |00>_AB the result is |Phi+>_SA |psi>_B.  The
system marginal is maximally mixed and independent of |psi>, while the original
state is recoverable from the environment qubit B alone.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Any

import numpy as np

from gaugegap.quantum_information.density import (
    bloch_vector,
    density_matrix,
    mutual_information,
    partial_trace,
    pure_state_fidelity,
    purity,
    trace_distance,
    von_neumann_entropy,
)

CLAIM_BOUNDARY = (
    "finite three-qubit unitary realization and numerical audit only; not a new proof "
    "of the general no-hiding theorem, not a black-hole information result, and not a "
    "claim that macroscopic environmental recovery is practical"
)


@dataclass(frozen=True)
class NoHidingAudit:
    label: str
    theta: float
    phi: float
    passed: bool
    system_bleaching_trace_distance: float
    channel_bleaching_trace_distance: float
    recovery_fidelity: float
    recovery_trace_distance: float
    bell_pair_fidelity: float
    input_recovered_bloch_error: float
    system_purity: float
    system_entropy: float
    recovery_entropy: float
    environment_entropy: float
    mutual_information_system_environment: float
    mutual_information_system_recovery: float
    global_purity: float
    unitarity_residual: float
    channel_completeness_residual: float
    input_bloch: tuple[float, float, float]
    recovered_bloch: tuple[float, float, float]
    unitary_sha256: str
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NoHidingSuite:
    passed: bool
    case_count: int
    failed_cases: tuple[str, ...]
    maximum_system_dependence: float
    minimum_recovery_fidelity: float
    maximum_bloch_error: float
    cases: tuple[NoHidingAudit, ...]
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, Any]:
        return {
            "schema": "gaugegap.no_hiding.v1",
            "passed": self.passed,
            "case_count": self.case_count,
            "failed_cases": list(self.failed_cases),
            "maximum_system_dependence": self.maximum_system_dependence,
            "minimum_recovery_fidelity": self.minimum_recovery_fidelity,
            "maximum_bloch_error": self.maximum_bloch_error,
            "cases": [case.summary() for case in self.cases],
            "claim_boundary": self.claim_boundary,
        }


def qubit_state(theta: float, phi: float) -> np.ndarray:
    if not math.isfinite(theta) or not math.isfinite(phi):
        raise ValueError("Bloch angles must be finite")
    return np.array(
        [math.cos(theta / 2.0), np.exp(1j * phi) * math.sin(theta / 2.0)],
        dtype=np.complex128,
    )


def _controlled_x(control: int, target: int, qubits: int = 3) -> np.ndarray:
    matrix = np.zeros((2**qubits, 2**qubits), dtype=np.complex128)
    for column in range(2**qubits):
        bits = [(column >> (qubits - 1 - index)) & 1 for index in range(qubits)]
        output = bits[:]
        if bits[control]:
            output[target] ^= 1
        row = 0
        for bit in output:
            row = (row << 1) | bit
        matrix[row, column] = 1.0
    return matrix


def _swap(first: int, second: int, qubits: int = 3) -> np.ndarray:
    matrix = np.zeros((2**qubits, 2**qubits), dtype=np.complex128)
    for column in range(2**qubits):
        bits = [(column >> (qubits - 1 - index)) & 1 for index in range(qubits)]
        bits[first], bits[second] = bits[second], bits[first]
        row = 0
        for bit in bits:
            row = (row << 1) | bit
        matrix[row, column] = 1.0
    return matrix


def no_hiding_unitary() -> np.ndarray:
    identity = np.eye(2, dtype=np.complex128)
    hadamard = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / math.sqrt(2.0)
    hadamard_system = np.kron(np.kron(hadamard, identity), identity)
    return _controlled_x(0, 1) @ hadamard_system @ _swap(0, 2)


def output_state(theta: float, phi: float) -> np.ndarray:
    zero = np.array([1.0, 0.0], dtype=np.complex128)
    initial = np.kron(np.kron(qubit_state(theta, phi), zero), zero)
    return no_hiding_unitary() @ initial


def depolarizing_kraus() -> tuple[np.ndarray, ...]:
    identity = np.eye(2, dtype=np.complex128)
    x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    return tuple(operator / 2.0 for operator in (identity, x, y, z))


def _unitary_digest(unitary: np.ndarray) -> str:
    packed = np.stack((unitary.real, unitary.imag), axis=-1).astype("<f8", copy=False)
    return hashlib.sha256(np.ascontiguousarray(packed).tobytes()).hexdigest()


def _evaluate(theta: float, phi: float, label: str, tolerance: float) -> tuple[NoHidingAudit, np.ndarray]:
    psi = qubit_state(theta, phi)
    rho_input = density_matrix(psi)
    unitary = no_hiding_unitary()
    state = output_state(theta, phi)
    rho_global = density_matrix(state)
    rho_system = partial_trace(rho_global, (2, 2, 2), keep=(0,))
    rho_environment = partial_trace(rho_global, (2, 2, 2), keep=(1, 2))
    rho_recovery = partial_trace(rho_global, (2, 2, 2), keep=(2,))
    rho_system_recovery = partial_trace(rho_global, (2, 2, 2), keep=(0, 2))
    rho_bell = partial_trace(rho_global, (2, 2, 2), keep=(0, 1))

    fixed_system = np.eye(2, dtype=np.complex128) / 2.0
    bell = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
    kraus = depolarizing_kraus()
    channel_output = sum(operator @ rho_input @ operator.conj().T for operator in kraus)
    completeness = sum(operator.conj().T @ operator for operator in kraus)
    input_bloch = bloch_vector(rho_input)
    recovered_bloch = bloch_vector(rho_recovery)
    bloch_error = float(np.linalg.norm(np.asarray(input_bloch) - np.asarray(recovered_bloch)))
    unitarity_residual = float(np.linalg.norm(unitary.conj().T @ unitary - np.eye(8)))
    completeness_residual = float(np.linalg.norm(completeness - np.eye(2)))
    system_distance = trace_distance(rho_system, fixed_system)
    channel_distance = trace_distance(channel_output, fixed_system)
    recovery_fidelity = pure_state_fidelity(rho_recovery, psi)
    recovery_distance = trace_distance(rho_recovery, rho_input)
    bell_fidelity = pure_state_fidelity(rho_bell, bell)
    passed = max(
        system_distance,
        channel_distance,
        recovery_distance,
        bloch_error,
        unitarity_residual,
        completeness_residual,
        abs(1.0 - recovery_fidelity),
        abs(1.0 - bell_fidelity),
    ) <= tolerance
    audit = NoHidingAudit(
        label=label,
        theta=float(theta),
        phi=float(phi),
        passed=passed,
        system_bleaching_trace_distance=system_distance,
        channel_bleaching_trace_distance=channel_distance,
        recovery_fidelity=recovery_fidelity,
        recovery_trace_distance=recovery_distance,
        bell_pair_fidelity=bell_fidelity,
        input_recovered_bloch_error=bloch_error,
        system_purity=purity(rho_system),
        system_entropy=von_neumann_entropy(rho_system),
        recovery_entropy=von_neumann_entropy(rho_recovery),
        environment_entropy=von_neumann_entropy(rho_environment),
        mutual_information_system_environment=mutual_information(rho_global, (2, 4)),
        mutual_information_system_recovery=mutual_information(rho_system_recovery, (2, 2)),
        global_purity=purity(rho_global),
        unitarity_residual=unitarity_residual,
        channel_completeness_residual=completeness_residual,
        input_bloch=input_bloch,
        recovered_bloch=recovered_bloch,
        unitary_sha256=_unitary_digest(unitary),
    )
    return audit, rho_system


def audit_no_hiding(
    theta: float,
    phi: float,
    *,
    label: str = "custom",
    tolerance: float = 1e-10,
) -> NoHidingAudit:
    if tolerance <= 0.0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    return _evaluate(theta, phi, label, tolerance)[0]


def _haar_angles(rng: np.random.Generator) -> tuple[float, float]:
    state = rng.normal(size=2) + 1j * rng.normal(size=2)
    state = state / np.linalg.norm(state)
    theta = 2.0 * math.acos(float(np.clip(abs(state[0]), 0.0, 1.0)))
    phi = float(np.angle(state[1]) - np.angle(state[0]))
    return theta, (phi + math.pi) % (2.0 * math.pi) - math.pi


def run_no_hiding_suite(
    *,
    random_count: int = 8,
    seed: int = 1729,
    tolerance: float = 1e-10,
) -> NoHidingSuite:
    if random_count < 0:
        raise ValueError("random_count must be non-negative")
    states = [
        ("zero", 0.0, 0.0),
        ("one", math.pi, 0.0),
        ("plus", math.pi / 2.0, 0.0),
        ("minus", math.pi / 2.0, math.pi),
        ("plus_i", math.pi / 2.0, math.pi / 2.0),
        ("minus_i", math.pi / 2.0, -math.pi / 2.0),
    ]
    rng = np.random.default_rng(seed)
    states.extend((f"haar_{index:02d}", *_haar_angles(rng)) for index in range(random_count))
    audits: list[NoHidingAudit] = []
    system_states: list[np.ndarray] = []
    for label, theta, phi in states:
        audit, rho_system = _evaluate(theta, phi, label, tolerance)
        audits.append(audit)
        system_states.append(rho_system)
    maximum_dependence = 0.0
    for left in range(len(system_states)):
        for right in range(left + 1, len(system_states)):
            maximum_dependence = max(
                maximum_dependence,
                trace_distance(system_states[left], system_states[right]),
            )
    failed = tuple(audit.label for audit in audits if not audit.passed)
    passed = not failed and maximum_dependence <= tolerance
    return NoHidingSuite(
        passed=passed,
        case_count=len(audits),
        failed_cases=failed,
        maximum_system_dependence=maximum_dependence,
        minimum_recovery_fidelity=min(audit.recovery_fidelity for audit in audits),
        maximum_bloch_error=max(audit.input_recovered_bloch_error for audit in audits),
        cases=tuple(audits),
    )
