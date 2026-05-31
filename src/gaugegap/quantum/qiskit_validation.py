from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import importlib.metadata
import importlib.util
import math
from pathlib import Path
from typing import Any

import numpy as np

from gaugegap.ledger import git_state, object_hash, utc_run_id
from gaugegap.models.z2_plaquette import hamiltonian_dense, model_metadata, open_plaquette_chain_layout, pauli_terms
from gaugegap.quantum.pauli_export import pauli_terms_to_dense, z2_plaquette_sparse_pauli
from gaugegap.solvers.exact_gap import exact_gap

ROOT = Path(__file__).resolve().parents[3]
QISKIT_CLAIM_BOUNDARY = "finite-system Qiskit validation only; no continuum Yang-Mills mass-gap claim."


@dataclass(frozen=True)
class QiskitValidationConfig:
    hypothesis_id: str = "gaugegap-0004"
    n_plaquettes: int = 1
    plaquette_coupling: float = 1.0
    transverse_field: float = 0.2
    shots: int = 1024
    noise_strength: float = 0.001
    layers: int = 2
    seed: int = 1234
    run_id: str | None = None
    include_measurements: bool = False
    max_qubits: int = 12

    def validated(self) -> "QiskitValidationConfig":
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
        if isinstance(self.layers, bool) or not isinstance(self.layers, int) or self.layers < 1:
            raise ValueError("layers must be a positive integer")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError("seed must be an integer")
        if isinstance(self.max_qubits, bool) or not isinstance(self.max_qubits, int) or self.max_qubits < 1:
            raise ValueError("max_qubits must be a positive integer")
        return self


def detect_qiskit_capabilities() -> dict[str, object]:
    qiskit_available = _module_available("qiskit")
    return {
        "qiskit_available": qiskit_available,
        "qiskit_version": _package_version("qiskit") if qiskit_available else None,
        "qpy_available": _module_available("qiskit.qpy") if qiskit_available else False,
        "qiskit_aer_available": _module_available("qiskit_aer"),
        "qiskit_aer_version": _package_version("qiskit-aer") if _module_available("qiskit_aer") else None,
        "qiskit_ibm_runtime_available": _module_available("qiskit_ibm_runtime"),
        "qiskit_ibm_runtime_version": _package_version("qiskit-ibm-runtime")
        if _module_available("qiskit_ibm_runtime")
        else None,
        "credentials_checked": False,
        "hardware_submission_enabled": False,
        "claim_boundary": QISKIT_CLAIM_BOUNDARY,
    }


def validate_qiskit_candidate(
    config: QiskitValidationConfig | None = None,
    *,
    output_dir: Path | None = None,
) -> dict[str, object]:
    cfg = (config or QiskitValidationConfig()).validated()
    run_id = cfg.run_id or utc_run_id()
    metadata = model_metadata(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field)
    exact_matrix = hamiltonian_dense(
        cfg.n_plaquettes,
        cfg.plaquette_coupling,
        cfg.transverse_field,
        max_qubits=cfg.max_qubits,
    )
    exact = exact_gap(exact_matrix)
    dense_replica = pauli_terms_to_dense(
        pauli_terms(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field),
        max_qubits=cfg.max_qubits,
    )
    capabilities = detect_qiskit_capabilities()
    result: dict[str, object] = {
        "schema": "gaugegap.quantum.qiskit_validation.v1",
        "status": "skipped_qiskit_missing",
        "hypothesis_id": cfg.hypothesis_id,
        "run_id": run_id,
        "model": metadata["model"],
        "params": metadata,
        "hamiltonian_hash": object_hash(metadata),
        "exact_dense": exact.to_dict(),
        "pauli_dense_replica": {
            "matrix_delta": float(np.linalg.norm(exact_matrix - dense_replica)),
            "gap_delta": abs(exact.gap - exact_gap(dense_replica).gap),
            "status": "pass" if np.allclose(exact_matrix, dense_replica, atol=1e-9) else "fail",
        },
        "pauli_terms": [
            {"label": label, "coefficient_real": float(complex(coeff).real), "coefficient_imag": float(complex(coeff).imag)}
            for label, coeff in pauli_terms(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field)
        ],
        "capabilities": capabilities,
        "hardware_submission": {
            "submitted": False,
            "policy": "IBM Runtime submission is never attempted by this validation command.",
        },
        "claim_boundary": QISKIT_CLAIM_BOUNDARY,
        "git": git_state(ROOT),
    }
    if not capabilities["qiskit_available"]:
        return result

    sparse_report = _sparse_pauli_report(cfg, exact_matrix, exact.gap)
    result["sparse_pauli_operator"] = sparse_report

    try:
        circuit = build_candidate_circuit(cfg)
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        result["status"] = "fail_circuit_construction"
        result["circuit_error"] = _safe_error(exc)
        return result

    result["circuit"] = _circuit_stats(circuit)
    result["qpy_manifest"] = _qpy_roundtrip(circuit, output_dir) if capabilities["qpy_available"] else _qpy_unavailable()
    result["transpilation"] = _transpile_report(circuit, cfg)
    result["aer_simulation"] = _aer_report(circuit, cfg, bool(capabilities["qiskit_aer_available"]))
    result["primitive_probe"] = _primitive_probe()
    result["status"] = "pass" if sparse_report.get("status") == "pass" else "fail_sparse_pauli_mismatch"
    return result


def build_candidate_circuit(config: QiskitValidationConfig, *, measure: bool | None = None):
    cfg = config.validated()
    layout = open_plaquette_chain_layout(cfg.n_plaquettes)
    if layout.n_qubits > cfg.max_qubits:
        raise ValueError(f"candidate requires {layout.n_qubits} qubits; max_qubits is {cfg.max_qubits}")
    try:
        from qiskit import QuantumCircuit
    except ImportError as exc:
        raise RuntimeError("Install Qiskit extras with: python -m pip install -e '.[quantum]'") from exc

    include_measurements = cfg.include_measurements if measure is None else bool(measure)
    circuit = QuantumCircuit(layout.n_qubits, layout.n_qubits if include_measurements else 0)
    for layer in range(cfg.layers):
        for qubit in range(layout.n_qubits):
            theta = _deterministic_angle(layer, qubit, cfg.plaquette_coupling, cfg.transverse_field, cfg.seed)
            circuit.ry(theta, qubit)
        for qubit in range(layout.n_qubits - 1):
            circuit.cx(qubit, qubit + 1)
    if include_measurements:
        circuit.measure(range(layout.n_qubits), range(layout.n_qubits))
    circuit.metadata = {
        "hypothesis_id": cfg.hypothesis_id,
        "n_plaquettes": cfg.n_plaquettes,
        "plaquette_coupling": float(cfg.plaquette_coupling),
        "transverse_field": float(cfg.transverse_field),
        "seed": cfg.seed,
        "finite_system_only": True,
        "claim_boundary": QISKIT_CLAIM_BOUNDARY,
    }
    return circuit


def _sparse_pauli_report(cfg: QiskitValidationConfig, exact_matrix: np.ndarray, exact_gap_value: float) -> dict[str, object]:
    try:
        operator = z2_plaquette_sparse_pauli(cfg.n_plaquettes, cfg.plaquette_coupling, cfg.transverse_field)
        sparse_matrix = np.asarray(operator.to_matrix())
        sparse_gap = exact_gap(sparse_matrix)
        matrix_delta = float(np.linalg.norm(exact_matrix - sparse_matrix))
        gap_delta = abs(float(exact_gap_value) - sparse_gap.gap)
        return {
            "available": True,
            "n_qubits": operator.num_qubits,
            "n_terms": len(operator),
            "matrix_delta": matrix_delta,
            "gap_delta": gap_delta,
            "status": "pass" if matrix_delta <= 1e-9 and gap_delta <= 1e-9 else "fail",
        }
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"available": False, "status": "fail", "error": _safe_error(exc)}


def _qpy_roundtrip(circuit: Any, output_dir: Path | None) -> dict[str, object]:
    try:
        from qiskit import qpy
    except ImportError:
        return _qpy_unavailable()
    try:
        if output_dir is None:
            return {"available": True, "written": False, "claim_boundary": QISKIT_CLAIM_BOUNDARY}
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "candidate_circuit.qpy"
        with path.open("wb") as handle:
            qpy.dump(circuit, handle)
        payload = path.read_bytes()
        with path.open("rb") as handle:
            loaded = qpy.load(handle)[0]
        return {
            "available": True,
            "written": True,
            "path": path.name,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "loaded_circuit": _circuit_stats(loaded),
            "loaded_metadata": _jsonable_metadata(getattr(loaded, "metadata", None)),
            "claim_boundary": QISKIT_CLAIM_BOUNDARY,
        }
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"available": True, "written": False, "status": "fail", "error": _safe_error(exc), "claim_boundary": QISKIT_CLAIM_BOUNDARY}


def _qpy_unavailable() -> dict[str, object]:
    return {"available": False, "written": False, "status": "skipped_qpy_unavailable", "claim_boundary": QISKIT_CLAIM_BOUNDARY}


def _transpile_report(circuit: Any, cfg: QiskitValidationConfig) -> dict[str, object]:
    original = _circuit_stats(circuit)
    try:
        try:
            from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

            pass_manager = generate_preset_pass_manager(optimization_level=1, seed_transpiler=cfg.seed)
            transpiled = pass_manager.run(circuit)
            method = "generate_preset_pass_manager"
        except Exception:
            from qiskit import transpile

            transpiled = transpile(circuit, optimization_level=1, seed_transpiler=cfg.seed)
            method = "transpile_fallback"
        stats = _circuit_stats(transpiled)
        return {
            "available": True,
            "method": method,
            "original_depth": original["depth"],
            "transpiled_depth": stats["depth"],
            "gate_counts": stats["gate_counts"],
            "circuit_width": stats["width"],
            "backend_target_name": None,
            "claim_boundary": QISKIT_CLAIM_BOUNDARY,
        }
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"available": False, "error": _safe_error(exc), "claim_boundary": QISKIT_CLAIM_BOUNDARY}


def _aer_report(circuit: Any, cfg: QiskitValidationConfig, aer_available: bool) -> dict[str, object]:
    statevector_report = _statevector_report(circuit)
    if not aer_available:
        return {
            "aer_available": False,
            "statevector_simulation": statevector_report,
            "shot_simulation": {"status": "skipped_aer_unavailable"},
            "claim_boundary": QISKIT_CLAIM_BOUNDARY,
        }
    try:
        from qiskit import transpile
        from qiskit_aer import AerSimulator

        measured = circuit.copy()
        if measured.num_clbits < measured.num_qubits:
            measured.measure_all()
        simulator = AerSimulator(seed_simulator=cfg.seed)
        compiled = transpile(measured, simulator, seed_transpiler=cfg.seed)
        counts = simulator.run(compiled, shots=cfg.shots).result().get_counts()
        report: dict[str, object] = {
            "aer_available": True,
            "statevector_simulation": statevector_report,
            "shot_simulation": {
                "shots": cfg.shots,
                "counts_top": _top_counts(counts),
                "distinct_bitstrings": len(counts),
                "status": "pass",
            },
            "noise_simulation": _noise_shot_report(measured, cfg),
            "claim_boundary": QISKIT_CLAIM_BOUNDARY,
        }
        return report
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"aer_available": True, "status": "fail", "error": _safe_error(exc), "claim_boundary": QISKIT_CLAIM_BOUNDARY}


def _statevector_report(circuit: Any) -> dict[str, object]:
    try:
        from qiskit.quantum_info import Statevector

        bare = circuit.remove_final_measurements(inplace=False)
        state = Statevector.from_instruction(bare)
        probabilities = state.probabilities()
        return {
            "available": True,
            "dimension": int(len(state.data)),
            "probability_norm": float(np.sum(probabilities)),
            "top_probabilities": _top_probabilities(state.probabilities_dict()),
            "status": "pass",
        }
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"available": False, "status": "fail", "error": _safe_error(exc)}


def _noise_shot_report(measured: Any, cfg: QiskitValidationConfig) -> dict[str, object]:
    if cfg.noise_strength <= 0.0:
        return {"status": "skipped_zero_noise_strength"}
    try:
        from qiskit import transpile
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel, depolarizing_error

        noise = NoiseModel()
        one_qubit = min(0.75, max(0.0, float(cfg.noise_strength)))
        two_qubit = min(0.75, 2.0 * one_qubit)
        noise.add_all_qubit_quantum_error(depolarizing_error(one_qubit, 1), ["ry"])
        noise.add_all_qubit_quantum_error(depolarizing_error(two_qubit, 2), ["cx"])
        simulator = AerSimulator(seed_simulator=cfg.seed + 1, noise_model=noise)
        compiled = transpile(measured, simulator, seed_transpiler=cfg.seed)
        counts = simulator.run(compiled, shots=cfg.shots).result().get_counts()
        return {
            "status": "informational_proxy",
            "noise_strength": float(cfg.noise_strength),
            "counts_top": _top_counts(counts),
            "distinct_bitstrings": len(counts),
        }
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"status": "skipped_noise_model_unavailable", "error": _safe_error(exc)}


def _primitive_probe() -> dict[str, object]:
    try:
        primitives = importlib.import_module("qiskit.primitives")
    except Exception as exc:  # pragma: no cover - defensive around optional dependency behavior
        return {"available": False, "error": _safe_error(exc)}
    classes = [
        name
        for name in (
            "StatevectorEstimator",
            "StatevectorSampler",
            "BackendEstimatorV2",
            "BackendSamplerV2",
            "Estimator",
            "Sampler",
        )
        if hasattr(primitives, name)
    ]
    return {
        "available": bool(classes),
        "classes": classes,
        "status": "available" if classes else "no_known_primitive_classes_detected",
        "claim_boundary": QISKIT_CLAIM_BOUNDARY,
    }


def _circuit_stats(circuit: Any) -> dict[str, object]:
    counts = {str(key): int(value) for key, value in circuit.count_ops().items()}
    return {
        "n_qubits": int(circuit.num_qubits),
        "depth": int(circuit.depth() or 0),
        "operations_count": int(sum(counts.values())),
        "gate_counts": counts,
        "width": int(circuit.width()),
        "metadata": _jsonable_metadata(getattr(circuit, "metadata", None)),
        "claim_boundary": QISKIT_CLAIM_BOUNDARY,
    }


def _deterministic_angle(layer: int, qubit: int, coupling: float, field: float, seed: int) -> float:
    seed_phase = (abs(seed) % 997) / 9970.0
    return float(0.07 * (layer + 1) * (qubit + 1) + 0.03 * float(coupling) + 0.05 * float(field) + seed_phase)


def _top_counts(counts: dict[str, int], limit: int = 8) -> dict[str, int]:
    return dict(sorted(((str(k), int(v)) for k, v in counts.items()), key=lambda item: item[1], reverse=True)[:limit])


def _top_probabilities(probabilities: dict[str, float], limit: int = 8) -> dict[str, float]:
    return dict(sorted(((str(k), float(v)) for k, v in probabilities.items()), key=lambda item: item[1], reverse=True)[:limit])


def _jsonable_metadata(metadata: Any) -> dict[str, object]:
    if not isinstance(metadata, dict):
        return {}
    clean: dict[str, object] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            clean[str(key)] = value
        else:
            clean[str(key)] = str(value)
    return clean


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
