from __future__ import annotations

import math
from typing import Iterable

CLAIM_BOUNDARY_REQUIRED = "no continuum Yang-Mills mass-gap claim"


def mean_gap(records: Iterable[dict[str, object]]) -> float:
    values = _gaps(records)
    return sum(values) / len(values) if values else 0.0


def min_gap(records: Iterable[dict[str, object]]) -> float:
    values = _gaps(records)
    return min(values) if values else 0.0


def gap_variance(records: Iterable[dict[str, object]]) -> float:
    values = _gaps(records)
    if len(values) <= 1:
        return 0.0
    mu = sum(values) / len(values)
    return sum((value - mu) ** 2 for value in values) / len(values)


def finite_size_survival_score(records: Iterable[dict[str, object]]) -> float:
    """Reward candidates whose smallest-size and largest-size gaps are comparable."""

    by_size: dict[int, list[float]] = {}
    for record in records:
        params = _params(record)
        by_size.setdefault(int(params["n_plaquettes"]), []).append(_gap(record))
    if not by_size:
        return 0.0
    ordered = sorted((size, sum(gaps) / len(gaps)) for size, gaps in by_size.items())
    if len(ordered) == 1:
        return 1.0
    first = max(ordered[0][1], 1e-12)
    last = max(ordered[-1][1], 0.0)
    return _clamp(last / first, 0.0, 1.5) / 1.5


def perturbation_stability_score(records: Iterable[dict[str, object]]) -> float:
    """Reward low variation in gap profile across parameter perturbations."""

    values = _gaps(records)
    if not values:
        return 0.0
    mu = sum(values) / len(values)
    if mu <= 1e-12:
        return 0.0
    coefficient = math.sqrt(gap_variance(records)) / mu
    return 1.0 / (1.0 + coefficient)


def pauli_replica_penalty(records: Iterable[dict[str, object]]) -> float:
    penalty = 0.0
    for record in records:
        replica = record.get("pauli_replica", {})
        if not isinstance(replica, dict):
            penalty += 5.0
            continue
        if replica.get("status") != "pass":
            penalty += 5.0
        penalty += 1e6 * abs(float(replica.get("matrix_delta", 0.0)))
        penalty += 1e6 * abs(float(replica.get("gap_delta", 0.0)))
    return penalty


def residual_penalty(records: Iterable[dict[str, object]]) -> float:
    penalty = 0.0
    for record in records:
        residual = abs(float(record.get("residual_norm", 0.0)))
        penalty += min(10.0, 1e8 * residual)
    return penalty


def complexity_penalty(candidate: dict[str, object]) -> float:
    records = _records(candidate)
    sizes = {int(_params(record)["n_plaquettes"]) for record in records}
    couplings = {round(float(_params(record)["plaquette_coupling"]), 12) for record in records}
    fields = {round(float(_params(record)["transverse_field"]), 12) for record in records}
    return 0.02 * len(sizes) + 0.01 * len(couplings) + 0.005 * len(fields)


def claim_boundary_penalty(candidate: dict[str, object]) -> float:
    if CLAIM_BOUNDARY_REQUIRED not in str(candidate.get("claim_boundary", "")):
        return 100.0
    for record in _records(candidate):
        if CLAIM_BOUNDARY_REQUIRED not in str(record.get("claim_boundary", "")):
            return 100.0
    return 0.0


def total_candidate_score(candidate: dict[str, object]) -> float:
    records = _records(candidate)
    if not records:
        return -math.inf

    base = 2.0 * mean_gap(records) + 1.5 * min_gap(records)
    stability = perturbation_stability_score(records)
    survival = finite_size_survival_score(records)
    variance_penalty = gap_variance(records)

    score = (
        base
        + 0.75 * stability
        + 0.75 * survival
        - 0.15 * variance_penalty
        - 0.10 * pauli_replica_penalty(records)
        - 0.05 * residual_penalty(records)
        - complexity_penalty(candidate)
        - claim_boundary_penalty(candidate)
    )
    return float(score)


def explain_score(candidate: dict[str, object]) -> dict[str, float]:
    records = _records(candidate)
    return {
        "mean_gap": mean_gap(records),
        "min_gap": min_gap(records),
        "gap_variance": gap_variance(records),
        "finite_size_survival_score": finite_size_survival_score(records),
        "perturbation_stability_score": perturbation_stability_score(records),
        "pauli_replica_penalty": pauli_replica_penalty(records),
        "residual_penalty": residual_penalty(records),
        "complexity_penalty": complexity_penalty(candidate),
        "claim_boundary_penalty": claim_boundary_penalty(candidate),
        "total_candidate_score": total_candidate_score(candidate),
    }


def _records(candidate: dict[str, object]) -> list[dict[str, object]]:
    records = candidate.get("records", [])
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _params(record: dict[str, object]) -> dict[str, object]:
    params = record.get("params", {})
    if not isinstance(params, dict):
        raise ValueError("candidate record is missing params")
    return params


def _gap(record: dict[str, object]) -> float:
    return max(0.0, float(record.get("value", 0.0)))


def _gaps(records: Iterable[dict[str, object]]) -> list[float]:
    return [_gap(record) for record in records]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
