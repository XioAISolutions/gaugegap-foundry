"""Finite Bell-state entanglement benchmark.

The forge computes a CHSH violation for a singlet state and pairs it with a
no-signaling audit.  It is intentionally hostile to the Bluetooth analogy: the
artifact permits "paired" intuition only as a user-interface metaphor and
checks that no usable communication channel is present.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any

import numpy as np


CLAIM_BOUNDARY = (
    "finite two-qubit Bell-state calculation only; demonstrates CHSH violation "
    "and no-signaling numerically, not faster-than-light communication or a "
    "hardware Bell experiment"
)
BLUETOOTH_ANALOGY_BOUNDARY = (
    "Bluetooth pairing is a local-device analogy only.  Entanglement correlations "
    "are audited here with a no-signaling residual, so the benchmark explicitly "
    "does not implement communication through measurement choices."
)
TECHNOLOGY_CONTEXT = (
    {
        "name": "quantum cryptography",
        "scope": "context only; this benchmark does not implement a protocol",
    },
    {
        "name": "quantum computing",
        "scope": "context only; this benchmark does not implement an algorithm",
    },
    {
        "name": "quantum teleportation",
        "scope": "state-information protocol context only; no teleportation of matter and no FTL channel",
    },
)
SOURCES = (
    {
        "kind": "background_reference",
        "title": "Nobel Prize in Physics 2022 press release",
        "url": "https://www.nobelprize.org/prizes/physics/2022/press-release/",
        "scope": "entangled states, Bell-inequality experiments, quantum information context",
    },
    {
        "kind": "background_reference",
        "title": "Stanford Encyclopedia of Philosophy: Bell's Theorem",
        "url": "https://plato.stanford.edu/entries/bell-theorem/",
        "scope": "Bell theorem and local-hidden-variable boundary context",
    },
)

_I2 = np.eye(2, dtype=complex)
_SX = np.array([[0, 1], [1, 0]], dtype=complex)
_SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
_SZ = np.array([[1, 0], [0, -1]], dtype=complex)


@dataclass(frozen=True)
class CorrelationTerm:
    alice_setting: str
    bob_setting: str
    expectation: float

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JointProbability:
    alice_setting: str
    bob_setting: str
    alice_outcome: int
    bob_outcome: int
    probability: float

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EntanglementReport:
    schema: str
    benchmark_id: str
    state_label: str
    chsh_value: float
    classical_bound: float
    tsirelson_bound: float
    violation_margin: float
    violation_fraction: float
    no_signaling_residual: float
    local_marginal_min: float
    local_marginal_max: float
    classical_control_chsh: float
    entanglement_gap_score: float
    correlations: list[CorrelationTerm]
    joint_probabilities: list[JointProbability]
    passed: bool
    claim_boundary: str = CLAIM_BOUNDARY
    bluetooth_analogy_boundary: str = BLUETOOTH_ANALOGY_BOUNDARY

    def summary(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "benchmark_id": self.benchmark_id,
            "state_label": self.state_label,
            "chsh_value": self.chsh_value,
            "classical_bound": self.classical_bound,
            "tsirelson_bound": self.tsirelson_bound,
            "violation_margin": self.violation_margin,
            "violation_fraction": self.violation_fraction,
            "no_signaling_residual": self.no_signaling_residual,
            "local_marginal_min": self.local_marginal_min,
            "local_marginal_max": self.local_marginal_max,
            "classical_control_chsh": self.classical_control_chsh,
            "entanglement_gap_score": self.entanglement_gap_score,
            "technology_context": list(TECHNOLOGY_CONTEXT),
            "correlations": [term.summary() for term in self.correlations],
            "joint_probabilities": [prob.summary() for prob in self.joint_probabilities],
            "passed": self.passed,
            "sources": list(SOURCES),
            "claim_boundary": self.claim_boundary,
            "bluetooth_analogy_boundary": self.bluetooth_analogy_boundary,
        }


def _observable(axis: np.ndarray) -> np.ndarray:
    axis = np.asarray(axis, dtype=float)
    norm = np.linalg.norm(axis)
    if norm <= 0.0:
        raise ValueError("axis must be non-zero")
    x, y, z = axis / norm
    return x * _SX + y * _SY + z * _SZ


def _projector(axis: np.ndarray, outcome: int) -> np.ndarray:
    if outcome not in (-1, 1):
        raise ValueError("outcome must be -1 or 1")
    return 0.5 * (_I2 + outcome * _observable(axis))


def _singlet() -> np.ndarray:
    state = np.zeros(4, dtype=complex)
    state[1] = 1.0 / sqrt(2.0)
    state[2] = -1.0 / sqrt(2.0)
    return state


def _expectation(state: np.ndarray, alice_axis: np.ndarray, bob_axis: np.ndarray) -> float:
    operator = np.kron(_observable(alice_axis), _observable(bob_axis))
    return float(np.real(np.vdot(state, operator @ state)))


def _joint_probability(
    state: np.ndarray,
    alice_axis: np.ndarray,
    bob_axis: np.ndarray,
    alice_outcome: int,
    bob_outcome: int,
) -> float:
    operator = np.kron(
        _projector(alice_axis, alice_outcome),
        _projector(bob_axis, bob_outcome),
    )
    return float(np.real(np.vdot(state, operator @ state)))


def _classical_chsh_bound() -> float:
    best = 0.0
    for a0 in (-1, 1):
        for a1 in (-1, 1):
            for b0 in (-1, 1):
                for b1 in (-1, 1):
                    best = max(best, abs(a0 * b0 + a0 * b1 + a1 * b0 - a1 * b1))
    return float(best)


def run_entanglement_forge() -> EntanglementReport:
    """Compute the finite Bell-state benchmark."""

    state = _singlet()
    axes = {
        "A0:sigma_z": np.array([0.0, 0.0, 1.0]),
        "A1:sigma_x": np.array([1.0, 0.0, 0.0]),
        "B0:(z+x)/sqrt2": np.array([1.0, 0.0, 1.0]) / sqrt(2.0),
        "B1:(z-x)/sqrt2": np.array([-1.0, 0.0, 1.0]) / sqrt(2.0),
    }
    pairings = [
        ("A0:sigma_z", "B0:(z+x)/sqrt2"),
        ("A0:sigma_z", "B1:(z-x)/sqrt2"),
        ("A1:sigma_x", "B0:(z+x)/sqrt2"),
        ("A1:sigma_x", "B1:(z-x)/sqrt2"),
    ]
    correlations = [
        CorrelationTerm(a, b, _expectation(state, axes[a], axes[b]))
        for a, b in pairings
    ]
    chsh = abs(
        correlations[0].expectation
        + correlations[1].expectation
        + correlations[2].expectation
        - correlations[3].expectation
    )
    joint_probabilities: list[JointProbability] = []
    for a, b in pairings:
        for alice_outcome in (-1, 1):
            for bob_outcome in (-1, 1):
                joint_probabilities.append(
                    JointProbability(
                        alice_setting=a,
                        bob_setting=b,
                        alice_outcome=alice_outcome,
                        bob_outcome=bob_outcome,
                        probability=_joint_probability(
                            state,
                            axes[a],
                            axes[b],
                            alice_outcome,
                            bob_outcome,
                        ),
                    )
                )

    residuals: list[float] = []
    marginal_values: list[float] = []
    alice_settings = ["A0:sigma_z", "A1:sigma_x"]
    bob_settings = ["B0:(z+x)/sqrt2", "B1:(z-x)/sqrt2"]
    for alice_setting in alice_settings:
        for alice_outcome in (-1, 1):
            marginals = []
            for bob_setting in bob_settings:
                marginals.append(
                    sum(
                        prob.probability
                        for prob in joint_probabilities
                        if prob.alice_setting == alice_setting
                        and prob.bob_setting == bob_setting
                        and prob.alice_outcome == alice_outcome
                    )
                )
            marginal_values.extend(marginals)
            residuals.append(abs(marginals[0] - marginals[1]))
    for bob_setting in bob_settings:
        for bob_outcome in (-1, 1):
            marginals = []
            for alice_setting in alice_settings:
                marginals.append(
                    sum(
                        prob.probability
                        for prob in joint_probabilities
                        if prob.alice_setting == alice_setting
                        and prob.bob_setting == bob_setting
                        and prob.bob_outcome == bob_outcome
                    )
                )
            marginal_values.extend(marginals)
            residuals.append(abs(marginals[0] - marginals[1]))

    classical_bound = _classical_chsh_bound()
    tsirelson_bound = 2.0 * sqrt(2.0)
    violation_margin = chsh - classical_bound
    violation_fraction = max(0.0, min(1.0, violation_margin / (tsirelson_bound - classical_bound)))
    no_signaling_residual = max(residuals)
    no_signal_score = max(0.0, min(1.0, 1.0 - no_signaling_residual / 1e-9))
    entanglement_gap_score = violation_fraction * no_signal_score
    passed = (
        abs(chsh - tsirelson_bound) < 1e-12
        and classical_bound == 2.0
        and no_signaling_residual < 1e-12
        and entanglement_gap_score > 0.999999
    )
    return EntanglementReport(
        schema="gaugegap.entanglement_forge.v1",
        benchmark_id="entangle-0001",
        state_label="singlet Bell state (|01> - |10>)/sqrt(2)",
        chsh_value=chsh,
        classical_bound=classical_bound,
        tsirelson_bound=tsirelson_bound,
        violation_margin=violation_margin,
        violation_fraction=violation_fraction,
        no_signaling_residual=no_signaling_residual,
        local_marginal_min=min(marginal_values),
        local_marginal_max=max(marginal_values),
        classical_control_chsh=classical_bound,
        entanglement_gap_score=entanglement_gap_score,
        correlations=correlations,
        joint_probabilities=joint_probabilities,
        passed=passed,
    )
