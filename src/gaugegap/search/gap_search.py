from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable

import numpy as np

from gaugegap.ledger import git_state, object_hash, utc_run_id
from gaugegap.models.z2_plaquette import (
    CLAIM_BOUNDARY,
    ground_state_observables,
    hamiltonian_dense,
    model_metadata,
    pauli_terms,
)
from gaugegap.quantum.pauli_export import pauli_terms_to_dense
from gaugegap.search.gap_objectives import explain_score, total_candidate_score
from gaugegap.solvers.exact_gap import exact_gap

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class SearchConfig:
    hypothesis_id: str = "gaugegap-search-0001"
    n_plaquettes: tuple[int, ...] = (1, 2, 3)
    plaquette_couplings: tuple[float, ...] = (0.5, 1.0, 1.5)
    transverse_fields: tuple[float, ...] = (0.05, 0.2, 0.5, 1.0, 1.5, 2.0)
    max_candidates: int = 10
    run_id: str | None = None
    max_qubits: int = 12
    random_samples: int = 0
    seed: int = 7

    def validated(self) -> "SearchConfig":
        if not self.n_plaquettes or any(isinstance(x, bool) or not isinstance(x, int) or x < 1 for x in self.n_plaquettes):
            raise ValueError("n_plaquettes must contain positive integers")
        if not self.plaquette_couplings or any(not math.isfinite(float(x)) for x in self.plaquette_couplings):
            raise ValueError("plaquette_couplings must contain finite numbers")
        if not self.transverse_fields or any(not math.isfinite(float(x)) for x in self.transverse_fields):
            raise ValueError("transverse_fields must contain finite numbers")
        if self.max_candidates < 1:
            raise ValueError("max_candidates must be positive")
        if self.max_qubits < 1:
            raise ValueError("max_qubits must be positive")
        if self.random_samples < 0:
            raise ValueError("random_samples must be non-negative")
        return self


def linspace(start: float, stop: float, points: int) -> tuple[float, ...]:
    if not (math.isfinite(start) and math.isfinite(stop)):
        raise ValueError("linspace bounds must be finite")
    if points < 1:
        raise ValueError("points must be positive")
    if points == 1:
        return (float(start),)
    step = (stop - start) / (points - 1)
    return tuple(float(start + i * step) for i in range(points))


def search_gap_candidates(config: SearchConfig | None = None) -> list[dict[str, object]]:
    """Search finite Z2 plaquette families and rank stable gap candidates.

    A candidate is a fixed plaquette coupling J evaluated across selected finite
    sizes and nearby transverse-field perturbations. This is finite-system
    exploration only, not a continuum Yang-Mills claim.
    """

    cfg = (config or SearchConfig()).validated()
    run_id = cfg.run_id or utc_run_id()
    git = git_state(ROOT)
    candidates = [_build_candidate(cfg, run_id, git, coupling) for coupling in cfg.plaquette_couplings]
    candidates.extend(_random_candidates(cfg, run_id, git))
    candidates.sort(key=lambda item: float(item["score"]), reverse=True)
    return candidates[: cfg.max_candidates]


def _build_candidate(cfg: SearchConfig, run_id: str, git: dict[str, object], plaquette_coupling: float) -> dict[str, object]:
    records: list[dict[str, object]] = []
    for count in cfg.n_plaquettes:
        for field in cfg.transverse_fields:
            records.append(_run_one(cfg, run_id, git, count, float(plaquette_coupling), float(field)))

    candidate_seed = {
        "hypothesis_id": cfg.hypothesis_id,
        "plaquette_coupling": float(plaquette_coupling),
        "n_plaquettes": list(cfg.n_plaquettes),
        "transverse_fields": list(cfg.transverse_fields),
    }
    candidate: dict[str, object] = {
        "candidate_id": f"{cfg.hypothesis_id}-candidate-{object_hash(candidate_seed)[:12]}",
        "hypothesis_id": cfg.hypothesis_id,
        "run_id": run_id,
        "track": "GaugeGap",
        "model": "z2_open_plaquette_chain",
        "plaquette_coupling": float(plaquette_coupling),
        "n_plaquettes": list(cfg.n_plaquettes),
        "transverse_fields": list(cfg.transverse_fields),
        "records": records,
        "gap_profile": _gap_profile(records),
        "claim_boundary": CLAIM_BOUNDARY,
        "git": git,
    }
    candidate["score_components"] = explain_score(candidate)
    candidate["score"] = total_candidate_score(candidate)
    candidate["status"] = _candidate_status(candidate)
    candidate["summary"] = _candidate_summary(candidate)
    return candidate


def _random_candidates(cfg: SearchConfig, run_id: str, git: dict[str, object]) -> list[dict[str, object]]:
    if cfg.random_samples <= 0:
        return []
    rng = np.random.default_rng(cfg.seed)
    min_j = min(float(x) for x in cfg.plaquette_couplings)
    max_j = max(float(x) for x in cfg.plaquette_couplings)
    min_h = min(float(x) for x in cfg.transverse_fields)
    max_h = max(float(x) for x in cfg.transverse_fields)
    candidates = []
    for _ in range(cfg.random_samples):
        coupling = float(rng.uniform(min_j, max_j))
        center = float(rng.uniform(min_h, max_h))
        width = max(0.01, 0.15 * center)
        fields = tuple(max(1e-6, center + delta * width) for delta in (-1.0, 0.0, 1.0))
        random_cfg = SearchConfig(
            hypothesis_id=cfg.hypothesis_id,
            n_plaquettes=cfg.n_plaquettes,
            plaquette_couplings=(coupling,),
            transverse_fields=fields,
            max_candidates=1,
            run_id=run_id,
            max_qubits=cfg.max_qubits,
            random_samples=0,
            seed=cfg.seed,
        )
        candidate = _build_candidate(random_cfg, run_id, git, coupling)
        candidate["search_mode"] = "seeded_random_local_perturbation"
        candidates.append(candidate)
    return candidates


def _run_one(
    cfg: SearchConfig,
    run_id: str,
    git: dict[str, object],
    n_plaquettes: int,
    plaquette_coupling: float,
    transverse_field: float,
) -> dict[str, object]:
    metadata = model_metadata(n_plaquettes, plaquette_coupling, transverse_field)
    exact_matrix = hamiltonian_dense(n_plaquettes, plaquette_coupling, transverse_field, max_qubits=cfg.max_qubits)
    exact_result = exact_gap(exact_matrix)
    replica_matrix = pauli_terms_to_dense(pauli_terms(n_plaquettes, plaquette_coupling, transverse_field))
    replica_result = exact_gap(replica_matrix)
    matrix_delta = float(np.linalg.norm(exact_matrix - replica_matrix))
    gap_delta = abs(exact_result.gap - replica_result.gap)
    replica_status = "pass" if matrix_delta <= 1e-9 and gap_delta <= 1e-9 else "fail"
    status = exact_result.status if replica_status == "pass" else "fail_pauli_replica_mismatch"
    return {
        "run_id": run_id,
        "hypothesis_id": cfg.hypothesis_id,
        "track": "GaugeGap",
        "model": metadata["model"],
        "observable": "mass_gap_and_ground_state_observables",
        "params": metadata,
        "hamiltonian_hash": object_hash(metadata),
        "value": exact_result.gap,
        "ground_energy": exact_result.ground_energy,
        "first_excited_energy": exact_result.first_excited_energy,
        "residual_norm": exact_result.residual_norm,
        "pauli_replica": {
            "gap": replica_result.gap,
            "gap_delta": gap_delta,
            "matrix_delta": matrix_delta,
            "status": replica_status,
        },
        "observables": ground_state_observables(n_plaquettes, plaquette_coupling, transverse_field),
        "method": "dense_exact_diagonalization_with_pauli_dense_replica",
        "backend": {"provider": "local", "name": "numpy.linalg.eigh", "mode": "exact_dense_plus_pauli_replica", "shots": None},
        "status": status,
        "claim_boundary": CLAIM_BOUNDARY,
        "git": git,
    }


def _gap_profile(records: Iterable[dict[str, object]]) -> dict[str, object]:
    by_size: dict[int, list[tuple[float, float]]] = {}
    for record in records:
        params = record["params"]
        assert isinstance(params, dict)
        size = int(params["n_plaquettes"])
        field = float(params["transverse_field"])
        gap = float(record["value"])
        by_size.setdefault(size, []).append((field, gap))
    return {f"n_plaquettes_{size}": [{"transverse_field": h, "gap": g} for h, g in sorted(points)] for size, points in sorted(by_size.items())}


def _candidate_status(candidate: dict[str, object]) -> str:
    records = candidate.get("records", [])
    if not isinstance(records, list) or not records:
        return "fail_empty_candidate"
    if any(record.get("status") != "finite_system_verified" for record in records if isinstance(record, dict)):
        return "warning_some_records_not_verified"
    return "finite_candidate_ranked"


def _candidate_summary(candidate: dict[str, object]) -> str:
    components = candidate.get("score_components", {})
    if not isinstance(components, dict):
        return "Candidate ranked from finite-system exact diagonalization records."
    return (
        "Finite Z2 plaquette candidate ranked by gap size, perturbation stability, "
        f"and finite-size survival; mean gap={float(components.get('mean_gap', 0.0)):.6g}, "
        f"min gap={float(components.get('min_gap', 0.0)):.6g}."
    )
