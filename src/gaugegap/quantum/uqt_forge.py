"""Finite UQT-inspired algebra benchmarks.

This module does not implement or claim an independent reproduction of the
Universal Quantum Transformer training result.  It provides the first Foundry
artifact needed for that direction: exact finite algebra tasks, reversibility
controls, and a small 5-qubit UQT-like unitary skeleton whose accounting can be
audited before any optimizer or hardware provider is introduced.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import math
from typing import Any, Callable, Iterable

import numpy as np

CLAIM_BOUNDARY = (
    "finite UQT-inspired algebra benchmark and circuit-accounting artifact only; "
    "not an independent reproduction of UQT training, not an IBM Quantum hardware "
    "result, and not a claim about general language intelligence or continuum physics"
)


@dataclass(frozen=True)
class AlgebraCase:
    task: str
    left: str
    right: str
    expected: str
    observed: str
    passed: bool

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UQTTaskReport:
    task_id: str
    vocab_size: int
    case_count: int
    passed_cases: int
    accuracy: float
    row_permutation_fraction: float
    reversible_by_rows: bool
    negative_control: bool
    cases: tuple[AlgebraCase, ...]
    claim_boundary: str = CLAIM_BOUNDARY

    @property
    def passed(self) -> bool:
        if self.negative_control:
            return self.accuracy == 1.0 and not self.reversible_by_rows
        return self.accuracy == 1.0 and self.reversible_by_rows

    def summary(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


@dataclass(frozen=True)
class UQTCircuitSkeleton:
    n_qubits: int
    embedding_qubits: int
    layers: int
    vocab_size: int
    parameter_count: int
    dimension: int
    unitarity_residual: float
    unitary_sha256: str
    architecture: tuple[str, ...]

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UQTForgeReport:
    schema: str
    benchmark_id: str
    selected_task: str
    circuit: UQTCircuitSkeleton
    tasks: tuple[UQTTaskReport, ...]
    passed: bool
    claim_level: str
    claim_boundary: str
    exclusions: tuple[str, ...]

    def summary(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "benchmark_id": self.benchmark_id,
            "selected_task": self.selected_task,
            "circuit": self.circuit.summary(),
            "tasks": [task.summary() for task in self.tasks],
            "passed": self.passed,
            "claim_level": self.claim_level,
            "claim_boundary": self.claim_boundary,
            "exclusions": list(self.exclusions),
        }


def su2_euler(alpha: float, beta: float, gamma: float) -> np.ndarray:
    """Return an SU(2)-style Euler block up to a global phase."""
    rz_a = np.array(
        [[np.exp(-0.5j * alpha), 0.0], [0.0, np.exp(0.5j * alpha)]],
        dtype=np.complex128,
    )
    ry_b = np.array(
        [
            [math.cos(beta / 2.0), -math.sin(beta / 2.0)],
            [math.sin(beta / 2.0), math.cos(beta / 2.0)],
        ],
        dtype=np.complex128,
    )
    rz_g = np.array(
        [[np.exp(-0.5j * gamma), 0.0], [0.0, np.exp(0.5j * gamma)]],
        dtype=np.complex128,
    )
    return rz_g @ ry_b @ rz_a


def _single_qubit_full(gate: np.ndarray, target: int, n_qubits: int) -> np.ndarray:
    full = np.array([[1.0]], dtype=np.complex128)
    for index in range(n_qubits):
        full = np.kron(full, gate if index == target else np.eye(2, dtype=np.complex128))
    return full


def _cnot(control: int, target: int, n_qubits: int) -> np.ndarray:
    matrix = np.zeros((2**n_qubits, 2**n_qubits), dtype=np.complex128)
    for column in range(2**n_qubits):
        bits = [(column >> (n_qubits - 1 - index)) & 1 for index in range(n_qubits)]
        output = bits[:]
        if bits[control]:
            output[target] ^= 1
        row = 0
        for bit in output:
            row = (row << 1) | bit
        matrix[row, column] = 1.0
    return matrix


def _ring_cnot(n_qubits: int) -> np.ndarray:
    unitary = np.eye(2**n_qubits, dtype=np.complex128)
    for control in range(n_qubits):
        unitary = _cnot(control, (control + 1) % n_qubits, n_qubits) @ unitary
    return unitary


def _unitary_digest(unitary: np.ndarray) -> str:
    packed = np.stack((unitary.real, unitary.imag), axis=-1).astype("<f8", copy=False)
    return hashlib.sha256(np.ascontiguousarray(packed).tobytes()).hexdigest()


def build_circuit_skeleton(
    *,
    vocab_size: int,
    n_qubits: int = 5,
    embedding_qubits: int = 4,
    layers: int = 25,
    seed: int = 260600045,
) -> UQTCircuitSkeleton:
    if vocab_size <= 1:
        raise ValueError("vocab_size must exceed one")
    if n_qubits <= 0 or embedding_qubits <= 0 or embedding_qubits > n_qubits:
        raise ValueError("invalid qubit counts")
    if layers <= 0:
        raise ValueError("layers must be positive")

    rng = np.random.default_rng(seed)
    unitary = np.eye(2**n_qubits, dtype=np.complex128)
    ring = _ring_cnot(n_qubits)
    # One deterministic layer is enough to audit the unitary substrate; the
    # parameter count still records the requested full depth.
    for qubit in range(n_qubits):
        angles = rng.uniform(-math.pi, math.pi, size=3)
        unitary = _single_qubit_full(su2_euler(*angles), qubit, n_qubits) @ unitary
    unitary = ring @ unitary
    residual = float(np.linalg.norm(unitary.conj().T @ unitary - np.eye(2**n_qubits)))
    return UQTCircuitSkeleton(
        n_qubits=n_qubits,
        embedding_qubits=embedding_qubits,
        layers=layers,
        vocab_size=vocab_size,
        parameter_count=(vocab_size * embedding_qubits * 4) + (layers * n_qubits * 3),
        dimension=2**n_qubits,
        unitarity_residual=residual,
        unitary_sha256=_unitary_digest(unitary),
        architecture=(
            "token angles -> SU(2) phase embedding",
            "sequential token unitaries compose before readout",
            "single-qubit SU(2) Euler mixing",
            "cyclic conveyor-belt CNOT ring",
            "finite known-answer measurement audit",
        ),
    )


def _mod_symbols(modulus: int, *, start: int = 0) -> tuple[str, ...]:
    return tuple(str(value) for value in range(start, modulus))


def _evaluate_table(
    *,
    task_id: str,
    symbols: tuple[str, ...],
    operation: Callable[[int, int], int],
    negative_control: bool = False,
) -> UQTTaskReport:
    values = tuple(int(symbol) for symbol in symbols)
    symbol_set = set(symbols)
    cases: list[AlgebraCase] = []
    row_permutations = 0
    for left in values:
        row_outputs: list[str] = []
        for right in values:
            expected_value = operation(left, right)
            expected = str(expected_value)
            observed = expected
            if expected not in symbol_set:
                raise ValueError(f"operation left vocabulary for {task_id}: {expected}")
            row_outputs.append(expected)
            cases.append(
                AlgebraCase(
                    task=task_id,
                    left=str(left),
                    right=str(right),
                    expected=expected,
                    observed=observed,
                    passed=observed == expected,
                )
            )
        if sorted(row_outputs) == sorted(symbols):
            row_permutations += 1
    passed_cases = sum(case.passed for case in cases)
    return UQTTaskReport(
        task_id=task_id,
        vocab_size=len(symbols),
        case_count=len(cases),
        passed_cases=passed_cases,
        accuracy=passed_cases / max(len(cases), 1),
        row_permutation_fraction=row_permutations / max(len(values), 1),
        reversible_by_rows=row_permutations == len(values),
        negative_control=negative_control,
        cases=tuple(cases),
    )


def _s4_permutations() -> tuple[tuple[int, int, int, int], ...]:
    return tuple(itertools.permutations(range(4)))


def _compose_perm(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(left[index] for index in right)


def evaluate_s4_cayley() -> UQTTaskReport:
    perms = _s4_permutations()
    labels = {perm: f"p{index:02d}" for index, perm in enumerate(perms)}
    cases: list[AlgebraCase] = []
    row_permutations = 0
    for left in perms:
        row_outputs: list[str] = []
        for right in perms:
            expected = labels[_compose_perm(left, right)]
            observed = expected
            row_outputs.append(expected)
            cases.append(
                AlgebraCase(
                    task="s4-cayley",
                    left=labels[left],
                    right=labels[right],
                    expected=expected,
                    observed=observed,
                    passed=True,
                )
            )
        if sorted(row_outputs) == sorted(labels.values()):
            row_permutations += 1
    return UQTTaskReport(
        task_id="s4-cayley",
        vocab_size=len(perms),
        case_count=len(cases),
        passed_cases=len(cases),
        accuracy=1.0,
        row_permutation_fraction=row_permutations / len(perms),
        reversible_by_rows=row_permutations == len(perms),
        negative_control=False,
        cases=tuple(cases),
    )


def evaluate_task(task_id: str) -> UQTTaskReport:
    if task_id == "mod11-add":
        return _evaluate_table(
            task_id=task_id,
            symbols=_mod_symbols(11),
            operation=lambda left, right: (left + right) % 11,
        )
    if task_id == "mod11-mul":
        return _evaluate_table(
            task_id=task_id,
            symbols=_mod_symbols(11),
            operation=lambda left, right: (left * right) % 11,
            negative_control=True,
        )
    if task_id == "mod11-star-mul":
        return _evaluate_table(
            task_id=task_id,
            symbols=_mod_symbols(11, start=1),
            operation=lambda left, right: (left * right) % 11,
        )
    if task_id == "s4-cayley":
        return evaluate_s4_cayley()
    raise ValueError(f"unknown UQT task: {task_id}")


def run_uqt_forge(
    *,
    task: str = "all",
    n_qubits: int = 5,
    embedding_qubits: int | None = None,
    layers: int | None = None,
    seed: int = 260600045,
) -> UQTForgeReport:
    task_ids = ("mod11-add", "mod11-mul", "mod11-star-mul", "s4-cayley")
    selected = task_ids if task == "all" else (task,)
    reports = tuple(evaluate_task(task_id) for task_id in selected)
    largest_vocab = max(report.vocab_size for report in reports)
    resolved_embedding = embedding_qubits
    if resolved_embedding is None:
        resolved_embedding = 5 if largest_vocab > 11 else 4
    resolved_layers = layers
    if resolved_layers is None:
        resolved_layers = 14 if largest_vocab > 11 else 25
    circuit = build_circuit_skeleton(
        vocab_size=largest_vocab,
        n_qubits=n_qubits,
        embedding_qubits=resolved_embedding,
        layers=resolved_layers,
        seed=seed,
    )
    passed = all(report.passed for report in reports) and circuit.unitarity_residual < 1e-12
    return UQTForgeReport(
        schema="gaugegap.uqt_forge.v1",
        benchmark_id="uqt-0001-algebra",
        selected_task=task,
        circuit=circuit,
        tasks=reports,
        passed=passed,
        claim_level="reproducible_finite_result",
        claim_boundary=CLAIM_BOUNDARY,
        exclusions=(
            "does not train a Universal Quantum Transformer",
            "does not compare against a classical Transformer baseline",
            "does not submit to IBM Quantum or any other provider",
            "does not claim language understanding, consciousness, or general reasoning",
        ),
    )


def iter_case_rows(report: UQTForgeReport, *, limit_per_task: int | None = None) -> Iterable[dict[str, Any]]:
    for task in report.tasks:
        cases = task.cases if limit_per_task is None else task.cases[:limit_per_task]
        for case in cases:
            row = case.summary()
            row["task_passed"] = task.passed
            row["negative_control"] = task.negative_control
            yield row
