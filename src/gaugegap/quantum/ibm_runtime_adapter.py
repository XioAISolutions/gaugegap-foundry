from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import importlib.util
import math
from pathlib import Path
from typing import Any

from gaugegap.ledger import git_state, utc_run_id
from gaugegap.models.z2_plaquette import model_metadata, open_plaquette_chain_layout, pauli_terms
from gaugegap.quantum.qiskit_validation import QISKIT_CLAIM_BOUNDARY, QiskitValidationConfig, build_candidate_circuit

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_CLAIM_BOUNDARY = (
    "finite-system exploratory IBM Runtime plan only; no continuum Yang-Mills mass-gap claim and no proof claim."
)


@dataclass(frozen=True)
class RuntimeSubmissionConfig:
    hypothesis_id: str = "gaugegap-0004"
    n_plaquettes: int = 1
    plaquette_coupling: float = 1.0
    transverse_field: float = 0.2
    shots: int = 1024
    backend: str | None = None
    least_busy: bool = False
    dry_run: bool = True
    submit_runtime: bool = False
    finite_system_confirmation: bool = False
    allow_service_probe: bool = False
    run_id: str | None = None
    seed: int = 1234

    def validated(self) -> "RuntimeSubmissionConfig":
        if isinstance(self.n_plaquettes, bool) or not isinstance(self.n_plaquettes, int) or self.n_plaquettes < 1:
            raise ValueError("n_plaquettes must be a positive integer")
        if not math.isfinite(float(self.plaquette_coupling)):
            raise ValueError("plaquette_coupling must be finite")
        if not math.isfinite(float(self.transverse_field)):
            raise ValueError("transverse_field must be finite")
        if isinstance(self.shots, bool) or not isinstance(self.shots, int) or self.shots < 1:
            raise ValueError("shots must be a positive integer")
        if self.submit_runtime and not self.finite_system_confirmation:
            raise ValueError("--submit-runtime requires --i-understand-this-is-finite-system-only")
        if self.submit_runtime and self.dry_run:
            raise ValueError("--submit-runtime and --dry-run are mutually exclusive")
        return self


def runtime_capabilities() -> dict[str, object]:
    qiskit_available = _module_available("qiskit")
    runtime_available = _module_available("qiskit_ibm_runtime")
    return {
        "qiskit_available": qiskit_available,
        "qiskit_version": _package_version("qiskit") if qiskit_available else None,
        "qiskit_ibm_runtime_available": runtime_available,
        "qiskit_ibm_runtime_version": _package_version("qiskit-ibm-runtime") if runtime_available else None,
        "credentials_checked": False,
        "tokens_printed_or_written": False,
        "claim_boundary": RUNTIME_CLAIM_BOUNDARY,
    }


def build_runtime_submission_plan(config: RuntimeSubmissionConfig | None = None) -> dict[str, object]:
    cfg = (config or RuntimeSubmissionConfig()).validated()
    run_id = cfg.run_id or utc_run_id()
    metadata = model_metadata(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field)
    layout = open_plaquette_chain_layout(cfg.n_plaquettes)
    capabilities = runtime_capabilities()
    circuit_stats = _candidate_circuit_stats(cfg) if capabilities["qiskit_available"] else {"status": "skipped_qiskit_missing"}
    service_probe: dict[str, object] = {"attempted": False, "reason": "credentials are not inspected unless explicit flags allow it"}
    job: dict[str, object] = {"submitted": False, "job_id": None}

    if cfg.allow_service_probe or cfg.submit_runtime:
        service_probe = _service_probe(construct_service=True)

    if cfg.submit_runtime:
        job = _submit_runtime_job(cfg)

    return {
        "schema": "gaugegap.quantum.ibm_runtime_submission_plan.v1",
        "run_id": run_id,
        "hypothesis_id": cfg.hypothesis_id,
        "dry_run": cfg.dry_run,
        "submit_runtime": cfg.submit_runtime,
        "finite_system_confirmation": cfg.finite_system_confirmation,
        "model": metadata["model"],
        "params": metadata,
        "pauli_terms": [
            {"label": label, "coefficient_real": float(complex(coeff).real), "coefficient_imag": float(complex(coeff).imag)}
            for label, coeff in pauli_terms(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field)
        ],
        "intended_backend": {
            "backend": cfg.backend,
            "least_busy": cfg.least_busy,
            "selection_attempted": bool(cfg.submit_runtime),
        },
        "resources": {
            "n_qubits": layout.n_qubits,
            "n_pauli_terms": len(pauli_terms(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field)),
            "shots": cfg.shots,
            "depth_proxy": max(1, 2 * layout.n_qubits - 1),
            "scale": "tiny" if layout.n_qubits <= 5 else "small",
        },
        "capabilities": capabilities,
        "service_probe": service_probe,
        "candidate_circuit": circuit_stats,
        "job": job,
        "warnings": [
            "finite-system exploratory job only",
            "no continuum mass-gap claim",
            "no proof claim",
            "hardware data is noisy and not theorem evidence",
            "IBM Runtime credentials, if configured locally, are never printed or written by this adapter",
        ],
        "claim_boundary": RUNTIME_CLAIM_BOUNDARY,
        "qiskit_validation_claim_boundary": QISKIT_CLAIM_BOUNDARY,
        "git": git_state(ROOT),
    }


def _candidate_circuit_stats(cfg: RuntimeSubmissionConfig) -> dict[str, object]:
    try:
        circuit = build_candidate_circuit(
            QiskitValidationConfig(
                hypothesis_id=cfg.hypothesis_id,
                n_plaquettes=cfg.n_plaquettes,
                plaquette_coupling=cfg.plaquette_coupling,
                transverse_field=cfg.transverse_field,
                shots=cfg.shots,
                seed=cfg.seed,
                include_measurements=True,
            ),
            measure=True,
        )
        counts = {str(key): int(value) for key, value in circuit.count_ops().items()}
        return {
            "status": "prepared",
            "n_qubits": circuit.num_qubits,
            "depth": circuit.depth(),
            "operations_count": sum(counts.values()),
            "gate_counts": counts,
            "metadata": dict(circuit.metadata or {}),
        }
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"status": "failed_to_prepare", "error": _safe_error(exc)}


def _service_probe(*, construct_service: bool) -> dict[str, object]:
    if not construct_service:
        return {"attempted": False}
    if not _module_available("qiskit_ibm_runtime"):
        return {"attempted": True, "constructed": False, "error": "qiskit_ibm_runtime is not installed"}
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService()
        return {
            "attempted": True,
            "constructed": True,
            "service_class": service.__class__.__name__,
            "credentials_checked": True,
            "tokens_printed_or_written": False,
        }
    except Exception as exc:  # pragma: no cover - depends on local credential state
        return {
            "attempted": True,
            "constructed": False,
            "credentials_checked": True,
            "tokens_printed_or_written": False,
            "error": _safe_error(exc),
        }


def _submit_runtime_job(cfg: RuntimeSubmissionConfig) -> dict[str, object]:
    if not _module_available("qiskit_ibm_runtime"):
        return {"submitted": False, "job_id": None, "status": "runtime_missing"}
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService()
        backend = _select_backend(service, cfg)
        circuit = build_candidate_circuit(
            QiskitValidationConfig(
                hypothesis_id=cfg.hypothesis_id,
                n_plaquettes=cfg.n_plaquettes,
                plaquette_coupling=cfg.plaquette_coupling,
                transverse_field=cfg.transverse_field,
                shots=cfg.shots,
                seed=cfg.seed,
                include_measurements=True,
            ),
            measure=True,
        )
        sampler = _runtime_sampler(backend)
        job = sampler.run([circuit], shots=cfg.shots)
        job_id = job.job_id() if callable(getattr(job, "job_id", None)) else str(getattr(job, "job_id", "unknown"))
        return {
            "submitted": True,
            "job_id": job_id,
            "backend": _backend_name(backend),
            "tokens_printed_or_written": False,
            "status": "submitted",
        }
    except Exception as exc:  # pragma: no cover - live provider path
        return {"submitted": False, "job_id": None, "status": "submission_failed", "error": _safe_error(exc)}


def _select_backend(service: Any, cfg: RuntimeSubmissionConfig) -> Any:
    if cfg.backend:
        return service.backend(cfg.backend)
    if cfg.least_busy:
        return service.least_busy(operational=True, simulator=False)
    raise ValueError("live submission requires --backend or --least-busy")


def _runtime_sampler(backend: Any) -> Any:
    runtime = __import__("qiskit_ibm_runtime", fromlist=["SamplerV2", "Sampler"])
    sampler_class = getattr(runtime, "SamplerV2", None) or getattr(runtime, "Sampler", None)
    if sampler_class is None:
        raise RuntimeError("No compatible Runtime Sampler class found")
    try:
        return sampler_class(mode=backend)
    except TypeError:
        return sampler_class(backend=backend)


def _backend_name(backend: Any) -> str:
    value = getattr(backend, "name", None)
    if callable(value):
        return str(value())
    if value:
        return str(value)
    return str(backend)


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


def _safe_error(exc: BaseException) -> str:
    text = str(exc).replace("\n", " ")
    for marker in ("token=", "TOKEN=", "api_key=", "API_KEY="):
        if marker in text:
            text = text.split(marker, 1)[0] + marker + "[redacted]"
    return text[:500]
