"""Finite Quantum Gap synthesis functional.

The Quantum Gap Functional is a repository-level synthesis metric.  It is not a
new physical law.  It compresses several finite separation checks into one
fail-closed scalar so Deep Boil can report whether the current evidence stack has
simultaneously preserved spectral, algebraic, geometric, topological,
non-classical-correlation, and interface margins.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable, Mapping

CLAIM_BOUNDARY = (
    "finite cross-track synthesis metric only; not a physical constant, not a "
    "universal law of quantum gravity, not a continuum mass-gap theorem, and not "
    "evidence for extra dimensions, conscious realism, faster-than-light "
    "communication, completed fractal topology, or general quantum AI"
)

EQUATION = (
    "Q_gap = B * exp((sum_i w_i log(eps + g_i)) / (sum_i w_i)); "
    "g_i in [0,1], B=1 only when every finite validation gate passes"
)


@dataclass(frozen=True)
class QuantumGapTerm:
    name: str
    value: float
    weight: float
    passed: bool
    definition: str

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QuantumGapReport:
    schema: str
    benchmark_id: str
    equation: str
    score: float
    boundary_gate: int
    passed: bool
    terms: tuple[QuantumGapTerm, ...]
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "benchmark_id": self.benchmark_id,
            "equation": self.equation,
            "score": self.score,
            "boundary_gate": self.boundary_gate,
            "passed": self.passed,
            "terms": [term.summary() for term in self.terms],
            "claim_boundary": self.claim_boundary,
        }


def _clip01(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def _weighted_geometric_mean(terms: Iterable[QuantumGapTerm], *, eps: float = 1e-12) -> float:
    items = tuple(terms)
    total_weight = sum(max(term.weight, 0.0) for term in items)
    if total_weight <= 0.0:
        return 0.0
    log_sum = 0.0
    for term in items:
        weight = max(term.weight, 0.0)
        log_sum += weight * math.log(eps + _clip01(term.value))
    return float(math.exp(log_sum / total_weight))


def _hamiltonian_gap_term(hamiltonians: Iterable[Mapping[str, Any]]) -> QuantumGapTerm:
    values: list[float] = []
    for record in hamiltonians:
        audit = record["audit"]
        gap = float(audit.get("spectral_gap") or 0.0)
        ground = abs(float(audit.get("ground_energy") or 0.0))
        first = abs(float(audit.get("first_excited_energy") or 0.0))
        values.append(gap / (1.0 + ground + first))
    value = min(values) if values else 0.0
    return QuantumGapTerm(
        name="normalized_hamiltonian_gap",
        value=_clip01(value),
        weight=1.0,
        passed=value > 0.0,
        definition="min finite spectral gap divided by 1 + |E0| + |E1|",
    )


def _dynamics_term(dynamics: Iterable[Mapping[str, Any]]) -> QuantumGapTerm:
    records = tuple(dynamics)
    if not records:
        value = 0.0
    else:
        max_error = max(float(record["dmd"]["reconstruction_error"]) for record in records)
        all_validated = all(bool(record["validated_step"]["validated"]) for record in records)
        value = (1.0 / (1.0 + max_error)) if all_validated else 0.0
    return QuantumGapTerm(
        name="validated_dynamics_coherence",
        value=_clip01(value),
        weight=0.75,
        passed=value > 0.0,
        definition="1/(1+max DMD residual), gated by interval-step validation",
    )


def _uqt_terms(uqt_summary: Mapping[str, Any]) -> tuple[QuantumGapTerm, QuantumGapTerm]:
    tasks = tuple(uqt_summary.get("tasks", ()))
    reversible = [
        float(task["row_permutation_fraction"])
        for task in tasks
        if not bool(task.get("negative_control"))
    ]
    negative = [
        float(task["row_permutation_fraction"])
        for task in tasks
        if bool(task.get("negative_control"))
    ]
    reversible_floor = min(reversible) if reversible else 0.0
    negative_ceiling = max(negative) if negative else 0.0
    algebra_gap = reversible_floor - negative_ceiling
    circuit = uqt_summary.get("circuit", {})
    residual = float(circuit.get("unitarity_residual") or math.inf)
    unitary_confidence = 1.0 / (1.0 + residual)
    return (
        QuantumGapTerm(
            name="uqt_reversibility_gap",
            value=_clip01(algebra_gap),
            weight=1.0,
            passed=algebra_gap > 0.0,
            definition="min reversible row-permutation fraction minus irreversible-control fraction",
        ),
        QuantumGapTerm(
            name="uqt_unitarity_confidence",
            value=_clip01(unitary_confidence),
            weight=0.5,
            passed=residual < 1e-12,
            definition="1/(1+unitarity residual) for the finite UQT-like circuit scaffold",
        ),
    )


def _compactification_term(compact_summaries: Iterable[Mapping[str, Any]]) -> QuantumGapTerm:
    margins: list[float] = []
    for report in compact_summaries:
        first = float(report["first_excited_mass"])
        cutoff = float(report["cutoff"])
        margins.append((first - cutoff) / (first + cutoff))
    value = min(margins) if margins else 0.0
    return QuantumGapTerm(
        name="compactification_visibility_gap",
        value=_clip01(value),
        weight=0.75,
        passed=value > 0.0,
        definition="min positive margin (m_first - cutoff)/(m_first + cutoff)",
    )


def _perception_term(perception_summary: Mapping[str, Any]) -> QuantumGapTerm:
    value = float(perception_summary.get("minimum_payoff_advantage") or 0.0)
    return QuantumGapTerm(
        name="fitness_interface_gap",
        value=_clip01(value),
        weight=0.5,
        passed=value > 0.0,
        definition="minimum interface payoff advantage over truth-coded bins",
    )


def _menger_term(menger_summary: Mapping[str, Any]) -> QuantumGapTerm:
    volume = _clip01(float(menger_summary.get("volume_collapse_score") or 0.0))
    surface = _clip01(float(menger_summary.get("surface_growth_score") or 0.0))
    dimension = _clip01(float(menger_summary.get("dimension_bridge_score") or 0.0))
    value = (volume * surface * dimension) ** (1.0 / 3.0) if volume and surface and dimension else 0.0
    return QuantumGapTerm(
        name="fractal_topology_gap",
        value=_clip01(value),
        weight=0.5,
        passed=bool(menger_summary.get("passed")) and value > 0.0,
        definition="geometric mean of finite volume-collapse, surface-growth, and dimension-bridge scores",
    )


def _entanglement_term(entanglement_summary: Mapping[str, Any]) -> QuantumGapTerm:
    violation = _clip01(float(entanglement_summary.get("violation_fraction") or 0.0))
    residual = float(entanglement_summary.get("no_signaling_residual") or 0.0)
    no_signal_score = _clip01(1.0 - residual / 1e-9)
    value = violation * no_signal_score
    return QuantumGapTerm(
        name="entanglement_nonlocality_gap",
        value=_clip01(value),
        weight=0.75,
        passed=bool(entanglement_summary.get("passed")) and violation > 0.0 and residual < 1e-12,
        definition="CHSH violation fraction gated by the no-signaling residual",
    )


def compute_quantum_gap(
    *,
    dynamics: Iterable[Mapping[str, Any]],
    hamiltonians: Iterable[Mapping[str, Any]],
    uqt_summary: Mapping[str, Any],
    compact_summaries: Iterable[Mapping[str, Any]],
    perception_summary: Mapping[str, Any],
    validation_gate: bool,
    menger_summary: Mapping[str, Any] | None = None,
    entanglement_summary: Mapping[str, Any] | None = None,
) -> QuantumGapReport:
    term_list = [
        _hamiltonian_gap_term(hamiltonians),
        _dynamics_term(dynamics),
        *_uqt_terms(uqt_summary),
        _compactification_term(compact_summaries),
        _perception_term(perception_summary),
    ]
    if menger_summary is not None:
        term_list.append(_menger_term(menger_summary))
    if entanglement_summary is not None:
        term_list.append(_entanglement_term(entanglement_summary))
    terms = tuple(term_list)
    boundary_gate = 1 if validation_gate and all(term.passed for term in terms) else 0
    score = boundary_gate * _weighted_geometric_mean(terms)
    return QuantumGapReport(
        schema="gaugegap.quantum_gap.v1",
        benchmark_id="quantum-gap-0001",
        equation=EQUATION,
        score=score,
        boundary_gate=boundary_gate,
        passed=bool(boundary_gate and score > 0.0),
        terms=terms,
    )
