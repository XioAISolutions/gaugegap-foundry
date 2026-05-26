"""IBM Runtime guarded hardware runner.

Submits validated circuits to IBM Runtime SamplerV2 or EstimatorV2 on real
QPU backends.  Every result records provider job id, backend name, shots,
and calibration context in the run ledger.

Requires the [quantum] optional dependency group and valid IBM Quantum
credentials (QISKIT_IBM_TOKEN or saved account).
"""
from __future__ import annotations

from typing import Any


def _check_runtime():
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "ibm_runtime_runner requires qiskit-ibm-runtime. "
            "Install with: pip install -e '.[quantum]'"
        ) from exc


def list_backends(
    simulator: bool = False,
    min_qubits: int = 0,
) -> list[dict[str, Any]]:
    _check_runtime()
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()
    backends = service.backends(simulator=simulator, operational=True, min_num_qubits=min_qubits)
    return [
        {
            "name": b.name,
            "num_qubits": getattr(b, "num_qubits", None),
            "simulator": simulator,
        }
        for b in backends
    ]


def run_sampler(
    circuit,
    backend_name: str | None = None,
    shots: int = 1024,
    resilience_level: int = 1,
    dynamical_decoupling: bool = True,
) -> dict[str, Any]:
    _check_runtime()
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    service = QiskitRuntimeService()

    if backend_name:
        backend = service.backend(backend_name)
    else:
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=circuit.num_qubits)

    pm = generate_preset_pass_manager(optimization_level=2, backend=backend)
    isa_circuit = pm.run(circuit)

    sampler = SamplerV2(mode=backend)
    sampler.options.default_shots = shots
    if dynamical_decoupling:
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.dynamical_decoupling.sequence_type = "XpXm"

    job = sampler.run([isa_circuit])
    result = job.result()
    pub_result = result[0]

    counts = {}
    if hasattr(pub_result.data, "meas"):
        counts = dict(pub_result.data.meas.get_counts())
    elif hasattr(pub_result.data, "c"):
        counts = dict(pub_result.data.c.get_counts())

    return {
        "provider": "ibm-runtime",
        "backend_name": backend.name,
        "backend_num_qubits": getattr(backend, "num_qubits", None),
        "job_id": job.job_id(),
        "shots": shots,
        "resilience_level": resilience_level,
        "dynamical_decoupling": dynamical_decoupling,
        "counts": counts,
        "isa_circuit_depth": isa_circuit.depth(),
        "isa_circuit_size": isa_circuit.size(),
        "status": "completed",
    }


def run_estimator(
    circuit,
    observables: list,
    backend_name: str | None = None,
    shots: int = 1024,
    resilience_level: int = 2,
    dynamical_decoupling: bool = True,
) -> dict[str, Any]:
    _check_runtime()
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    service = QiskitRuntimeService()

    if backend_name:
        backend = service.backend(backend_name)
    else:
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=circuit.num_qubits)

    pm = generate_preset_pass_manager(optimization_level=2, backend=backend)
    isa_circuit = pm.run(circuit)
    isa_observables = [obs.apply_layout(isa_circuit.layout) for obs in observables]

    estimator = EstimatorV2(mode=backend)
    estimator.options.resilience_level = resilience_level
    estimator.options.default_shots = shots
    if dynamical_decoupling:
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XpXm"

    pub_tuples = [(isa_circuit, obs) for obs in isa_observables]
    job = estimator.run(pub_tuples)
    result = job.result()

    expectation_values = []
    for pub_result in result:
        val = pub_result.data.evs
        if hasattr(val, "tolist"):
            val = val.tolist()
        expectation_values.append(val)

    return {
        "provider": "ibm-runtime",
        "backend_name": backend.name,
        "backend_num_qubits": getattr(backend, "num_qubits", None),
        "job_id": job.job_id(),
        "shots": shots,
        "resilience_level": resilience_level,
        "dynamical_decoupling": dynamical_decoupling,
        "expectation_values": expectation_values,
        "isa_circuit_depth": isa_circuit.depth(),
        "isa_circuit_size": isa_circuit.size(),
        "status": "completed",
    }


def backend_metadata(backend_name: str | None = None) -> dict[str, Any]:
    _check_runtime()
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()
    if backend_name:
        backend = service.backend(backend_name)
    else:
        backend = service.least_busy(operational=True, simulator=False)

    return {
        "name": backend.name,
        "num_qubits": getattr(backend, "num_qubits", None),
        "basis_gates": list(backend.operation_names) if hasattr(backend, "operation_names") else [],
    }
