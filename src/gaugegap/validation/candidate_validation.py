from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.metadata
import importlib.util
from pathlib import Path
import math

import numpy as np

from gaugegap.ledger import git_state, object_hash, utc_run_id
from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY, hamiltonian_dense, model_metadata, pauli_terms
from gaugegap.quantum.pauli_export import pauli_terms_to_dense
from gaugegap.solvers.exact_gap import exact_gap

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ValidationConfig:
    hypothesis_id: str = "gaugegap-0004"
    n_plaquettes: int = 1
    plaquette_coupling: float = 1.0
    transverse_field: float = 0.2
    shots: int = 1024
    noise_strength: float = 0.02
    run_id: str | None = None
    max_qubits: int = 12
    enable_qiskit_probe: bool = True

    def validated(self) -> "ValidationConfig":
        if isinstance(self.n_plaquettes, bool) or not isinstance(self.n_plaquettes, int) or self.n_plaquettes < 1:
            raise ValueError("n_plaquettes must be a positive integer")
        if not math.isfinite(float(self.plaquette_coupling)):
            raise ValueError("plaquette_coupling must be finite")
        if not math.isfinite(float(self.transverse_field)):
            raise ValueError("transverse_field must be finite")
        if isinstance(self.shots, bool) or not isinstance(self.shots, int) or self.shots < 1:
            raise ValueError("shots must be a positive integer")
        if not math.isfinite(float(self.noise_strength)) or not 0.0 <= float(self.noise_strength) <= 1.0:
            raise ValueError("noise_strength must be in [0, 1]")
        if isinstance(self.max_qubits, bool) or not isinstance(self.max_qubits, int) or self.max_qubits < 1:
            raise ValueError("max_qubits must be a positive integer")
        return self


def validate_z2_candidate(config: ValidationConfig | None = None) -> dict[str, object]:
    """Validate a finite Z2 candidate across exact, replica, and readiness checks.

    The validation is intentionally local and deterministic. It prepares the same
    conceptual handoff used by IBM's Qiskit patterns workflow: map to operators,
    optimize/inspect resources, execute only after local checks, then analyze.
    No real hardware job is submitted here.
    """

    cfg = (config or ValidationConfig()).validated()
    run_id = cfg.run_id or utc_run_id()
    metadata = model_metadata(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field)
    exact_matrix = hamiltonian_dense(
        cfg.n_plaquettes,
        cfg.plaquette_coupling,
        cfg.transverse_field,
        max_qubits=cfg.max_qubits,
    )
    exact = exact_gap(exact_matrix)
    replica_matrix = pauli_terms_to_dense(
        pauli_terms(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field),
        max_qubits=cfg.max_qubits,
    )
    replica = exact_gap(replica_matrix)
    matrix_delta = float(np.linalg.norm(exact_matrix - replica_matrix))
    gap_delta = abs(exact.gap - replica.gap)
    shot_sigma = _shot_sigma(exact.gap, cfg.shots)
    noisy_gap_estimate = max(0.0, exact.gap * (1.0 - cfg.noise_strength))
    noisy_gap_delta = abs(noisy_gap_estimate - exact.gap)
    resource = _resource_estimate(metadata)
    qiskit_probe = _qiskit_probe(cfg.enable_qiskit_probe)
    score, verdict, reasons = _hardware_readiness_score(
        exact_gap_value=exact.gap,
        residual_norm=exact.residual_norm,
        matrix_delta=matrix_delta,
        gap_delta=gap_delta,
        shot_sigma=shot_sigma,
        noisy_gap_delta=noisy_gap_delta,
        resource=resource,
        qiskit_probe=qiskit_probe,
    )
    return {
        "schema": "gaugegap.validation.hardware_readiness.v1",
        "hypothesis_id": cfg.hypothesis_id,
        "run_id": run_id,
        "model": metadata["model"],
        "params": metadata,
        "hamiltonian_hash": object_hash(metadata),
        "exact": exact.to_dict(),
        "pauli_replica": {
            "gap": replica.gap,
            "gap_delta": gap_delta,
            "matrix_delta": matrix_delta,
            "status": "pass" if matrix_delta <= 1e-9 and gap_delta <= 1e-9 else "fail",
        },
        "shot_model": {
            "shots": cfg.shots,
            "gap_sigma_proxy": shot_sigma,
            "status": "informational_proxy",
        },
        "noise_model": {
            "noise_strength": float(cfg.noise_strength),
            "noisy_gap_estimate": noisy_gap_estimate,
            "noisy_gap_delta": noisy_gap_delta,
            "status": "informational_proxy",
        },
        "resource_estimate": resource,
        "qiskit_probe": qiskit_probe,
        "hardware_readiness": {
            "score": score,
            "verdict": verdict,
            "reasons": reasons,
            "next_action": _next_action(verdict),
        },
        "workflow_mapping": {
            "ibm_qiskit_pattern_step_1": "map finite candidate to circuit/operator format",
            "ibm_qiskit_pattern_step_2": "optimize/inspect resources and ISA constraints before hardware",
            "ibm_qiskit_pattern_step_3": "execute through estimator/sampler only after local checks pass",
            "ibm_qiskit_pattern_step_4": "analyze exact-vs-simulator-vs-hardware deviations",
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "git": git_state(ROOT),
    }


def _resource_estimate(metadata: dict[str, object]) -> dict[str, object]:
    n_qubits = int(metadata["n_qubits"])
    n_plaquettes = int(metadata["n_plaquettes"])
    n_terms = n_plaquettes + n_qubits
    return {
        "n_qubits": n_qubits,
        "n_pauli_terms": n_terms,
        "estimated_min_observable_groups": n_terms,
        "approximate_observable_groups": n_terms,
        "toy_ansatz_depth_proxy": max(1, 2 * n_qubits - 1),
        "depth_proxy": max(1, 2 * n_qubits - 1),
        "hardware_scale": "tiny" if n_qubits <= 5 else "small" if n_qubits <= 12 else "too_large_for_default_exact_path",
    }


def _qiskit_probe(enabled: bool) -> dict[str, object]:
    qiskit_available = _module_available("qiskit") if enabled else False
    qpy_available = _module_available("qiskit.qpy") if enabled and qiskit_available else False
    aer_available = _module_available("qiskit_aer") if enabled else False
    runtime_available = _module_available("qiskit_ibm_runtime") if enabled else False
    return {
        "enabled": bool(enabled),
        "qiskit_available": bool(qiskit_available),
        "qiskit_version": _package_version("qiskit") if qiskit_available else None,
        "qpy_export_available": bool(qpy_available),
        "aer_available": bool(aer_available),
        "qiskit_aer_version": _package_version("qiskit-aer") if aer_available else None,
        "ibm_runtime_available": bool(runtime_available),
        "qiskit_ibm_runtime_version": _package_version("qiskit-ibm-runtime") if runtime_available else None,
        "credentials_checked": False,
        "credential_policy": "IBM Runtime credentials are not inspected unless an explicit runtime submission command opts in.",
        "runtime_submission_ready": False,
        "status": "qiskit_probe_ready" if qiskit_available else "qiskit_optional_dependency_missing_or_disabled",
    }


def _shot_sigma(gap: float, shots: int) -> float:
    # Conservative proxy: bounded observable standard error shrinks as 1/sqrt(shots).
    return max(1.0, abs(float(gap))) / math.sqrt(float(shots))


def _hardware_readiness_score(
    *,
    exact_gap_value: float,
    residual_norm: float,
    matrix_delta: float,
    gap_delta: float,
    shot_sigma: float,
    noisy_gap_delta: float,
    resource: dict[str, object],
    qiskit_probe: dict[str, object],
) -> tuple[float, str, list[str]]:
    score = 100.0
    reasons: list[str] = []
    if exact_gap_value <= 0.0:
        score -= 30.0
        reasons.append("exact finite gap is not positive")
    if residual_norm > 1e-8:
        score -= 20.0
        reasons.append("exact diagonalization residual is high")
    if matrix_delta > 1e-9 or gap_delta > 1e-9:
        score -= 30.0
        reasons.append("Pauli dense replica does not match exact dense Hamiltonian")
    if shot_sigma > max(0.1, 0.5 * max(exact_gap_value, 1e-12)):
        score -= 10.0
        reasons.append("shot-count proxy is too noisy relative to the gap")
    if noisy_gap_delta > max(0.2, 0.5 * max(exact_gap_value, 1e-12)):
        score -= 10.0
        reasons.append("noise proxy strongly distorts the finite gap")
    if int(resource["n_qubits"]) > 5:
        score -= 5.0
        reasons.append("candidate is beyond the tiny first-hardware target")
    if not bool(qiskit_probe.get("qiskit_available")):
        score -= 5.0
        reasons.append("Qiskit optional dependency not available in this environment")
    if not bool(qiskit_probe.get("qpy_export_available")):
        score -= 5.0
        reasons.append("QPY export is unavailable for reproducible circuit artifacts")
    if not bool(qiskit_probe.get("aer_available")):
        score -= 5.0
        reasons.append("Aer simulator path is unavailable for local shot validation")
    score = max(0.0, min(100.0, score))
    if score >= 85.0:
        verdict = "ready_for_simulator_and_tiny_qpu_trial"
    elif score >= 65.0:
        verdict = "ready_for_simulator_not_hardware"
    else:
        verdict = "not_ready"
    if not reasons:
        reasons.append("all local finite-system readiness checks passed")
    return score, verdict, reasons


def _next_action(verdict: str) -> str:
    if verdict == "ready_for_simulator_and_tiny_qpu_trial":
        return "run Qiskit statevector/Aer estimator path, then optional tiny IBM Runtime job with saved credentials"
    if verdict == "ready_for_simulator_not_hardware":
        return "run local simulator validation and improve score before provider submission"
    return "fix exact/replica/noise/resource issues before quantum execution"


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None
