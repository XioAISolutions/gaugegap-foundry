from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
import os
from typing import Any


@dataclass(frozen=True)
class QuantumSurface:
    id: str
    track: str
    level: int
    level_name: str
    status: str
    actual_quantum_hardware: bool
    files: tuple[str, ...]
    command: str
    meaning: str
    next_gate: str


SURFACES: tuple[QuantumSurface, ...] = (
    QuantumSurface(
        id="exact_dense_baselines",
        track="GaugeGap / FlowGap / CurveRank",
        level=0,
        level_name="classical_reference",
        status="active",
        actual_quantum_hardware=False,
        files=("scripts/run_gap_sweep.py", "scripts/run_gaugegap_u1.py", "scripts/run_flowgap_burgers.py", "scripts/run_curverank_screen.py"),
        command="python scripts/run_gap_sweep.py",
        meaning="Classical baselines define the finite systems and acceptance references.",
        next_gate="Keep these as the source of truth before any simulator or QPU claim.",
    ),
    QuantumSurface(
        id="qiskit_pauli_operator",
        track="GaugeGap",
        level=1,
        level_name="quantum_operator_representation",
        status="active",
        actual_quantum_hardware=False,
        files=("src/gaugegap/qiskit_backend.py", "scripts/run_gap_sweep.py"),
        command="python scripts/run_gap_sweep.py --method qiskit-pauli",
        meaning="Builds the finite Hamiltonian as a Qiskit SparsePauliOp and checks it against dense exact diagonalization.",
        next_gate="Use this before turning a Hamiltonian into circuits or IBM Runtime observables.",
    ),
    QuantumSurface(
        id="qiskit_statevector_dynamics",
        track="GaugeGap",
        level=2,
        level_name="quantum_circuit_simulation",
        status="active",
        actual_quantum_hardware=False,
        files=("src/gaugegap/qiskit_dynamics.py", "scripts/run_dynamics.py"),
        command="python scripts/run_dynamics.py --backend statevector",
        meaning="Builds a Trotter circuit and evaluates exact simulated quantum-state observables.",
        next_gate="Compare with shot sampling and noisy simulation before hardware.",
    ),
    QuantumSurface(
        id="qiskit_aer_sampler",
        track="GaugeGap",
        level=2,
        level_name="shot_based_quantum_simulation",
        status="active",
        actual_quantum_hardware=False,
        files=("src/gaugegap/qiskit_dynamics.py", "scripts/run_dynamics.py", "scripts/analyze_dynamics.py"),
        command="python scripts/run_dynamics.py --backend aer-sampler --noise depolarizing",
        meaning="Samples Trotter circuits through Aer, including a simple depolarizing noise model.",
        next_gate="Only move to hardware when analysis gates pass under shot/noise drift.",
    ),
    QuantumSurface(
        id="flowgap_vqls_statevector",
        track="FlowGap",
        level=2,
        level_name="quantum_algorithm_simulation",
        status="active",
        actual_quantum_hardware=False,
        files=("src/gaugegap/flowgap_qsubroutine.py", "scripts/run_flowgap_burgers.py"),
        command="python scripts/run_flowgap_burgers.py --quantum",
        meaning="Runs a tiny VQLS-style pressure-Poisson subroutine through statevector simulation.",
        next_gate="Treat as a quantum-algorithm benchmark, not a Navier-Stokes theorem route.",
    ),
    QuantumSurface(
        id="braket_local_simulator",
        track="GaugeGap",
        level=2,
        level_name="braket_local_simulation",
        status="active",
        actual_quantum_hardware=False,
        files=("src/gaugegap/braket_runner.py", "scripts/run_hardware.py"),
        command="python scripts/run_hardware.py --provider braket-local",
        meaning="Runs Trotter circuits on Braket local StateVectorSimulator for cross-platform validation.",
        next_gate="Compare Braket local results with Qiskit statevector before cloud submission.",
    ),
    QuantumSurface(
        id="ibm_runtime_sampler",
        track="GaugeGap",
        level=3,
        level_name="hardware_ready_boundary",
        status="ready",
        actual_quantum_hardware=True,
        files=("src/gaugegap/ibm_runtime_runner.py", "scripts/run_hardware.py"),
        command="python scripts/run_hardware.py --provider ibm",
        meaning="Submits validated circuits to IBM Runtime SamplerV2/EstimatorV2 on a physical backend. Requires QISKIT_IBM_TOKEN.",
        next_gate="Run only after statevector and Aer analysis gates pass. Ledger must record job_id, backend, shots.",
    ),
    QuantumSurface(
        id="braket_cloud_devices",
        track="GaugeGap",
        level=3,
        level_name="braket_cloud_boundary",
        status="ready",
        actual_quantum_hardware=True,
        files=("src/gaugegap/braket_runner.py", "scripts/run_hardware.py"),
        command="python scripts/run_hardware.py --provider braket-cloud --device-name ionq-aria1",
        meaning="Submits circuits to IonQ, Rigetti, or managed Braket simulators via AWS. Requires AWS credentials.",
        next_gate="Run only after Braket local simulator results match Qiskit statevector. Ledger must record task_id, device_arn, shots.",
    ),
    QuantumSurface(
        id="future_quantinuum",
        track="GaugeGap",
        level=3,
        level_name="future_provider_boundary",
        status="planned",
        actual_quantum_hardware=False,
        files=("docs/roadmap.md",),
        command="not implemented",
        meaning="Future pytket/Quantinuum backend for trapped-ion SU(2) gauge experiments.",
        next_gate="Do not implement until IBM and Braket artifacts are stable and reproducible.",
    ),
)


def quantum_usage_map() -> list[dict[str, Any]]:
    return [asdict(surface) for surface in SURFACES]


def quantum_summary() -> dict[str, Any]:
    active = [surface for surface in SURFACES if surface.status == "active"]
    ready = [surface for surface in SURFACES if surface.status == "ready"]
    hardware_ready = [surface for surface in SURFACES if surface.actual_quantum_hardware and surface.status == "ready"]
    max_active = max(surface.level for surface in active) if active else 0
    max_ready = max(surface.level for surface in ready) if ready else max_active
    return {
        "active_surface_count": len(active),
        "ready_surface_count": len(ready),
        "max_active_level": max_active,
        "max_active_level_name": _level_name(max_active),
        "max_ready_level": max_ready,
        "max_ready_level_name": _level_name(max_ready) if ready else "none",
        "actual_hardware_runs_present": False,
        "hardware_ready_count": len(hardware_ready),
        "plain_english": (
            "The project uses quantum simulators (Qiskit + Braket local) and has "
            "hardware runners ready for IBM Runtime and AWS Braket cloud devices. "
            "Real QPU execution requires provider credentials."
        ),
    }


def ibm_runtime_readiness(probe: bool = False) -> dict[str, Any]:
    dependency_present = importlib.util.find_spec("qiskit_ibm_runtime") is not None
    env_token_present = bool(os.getenv("QISKIT_IBM_TOKEN") or os.getenv("IBM_QUANTUM_TOKEN"))
    env_instance_present = bool(os.getenv("QISKIT_IBM_INSTANCE") or os.getenv("IBM_QUANTUM_INSTANCE"))
    result: dict[str, Any] = {
        "dependency_present": dependency_present,
        "env_token_present": env_token_present,
        "env_instance_present": env_instance_present,
        "probe_requested": probe,
        "can_attempt_runtime": dependency_present and (env_token_present or probe),
        "backends": [],
        "status": "not_probed",
    }

    if not probe:
        result["next_step"] = "Run `python scripts/quantum_status.py --probe-ibm` after configuring IBM Quantum credentials."
        return result

    if not dependency_present:
        result["status"] = "missing_dependency"
        result["error"] = "Install quantum extras with: python -m pip install -e '.[quantum]'"
        return result

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService()
        backends = service.backends(simulator=False, operational=True)
        result["backends"] = [
            {
                "name": backend.name,
                "num_qubits": getattr(backend, "num_qubits", None),
            }
            for backend in backends
        ]
        result["status"] = "ok"
    except Exception as exc:  # pragma: no cover - depends on local credentials/network
        result["status"] = "probe_failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def render_quantum_usage_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Quantum Usage Map",
        "",
        f"Current maximum active level: **{summary['max_active_level']} ({summary['max_active_level_name']})**.",
        f"Hardware-ready level: **{summary.get('max_ready_level', 'none')} ({summary.get('max_ready_level_name', 'none')})**.",
        "",
        summary["plain_english"],
        "",
        "## Levels",
        "",
        "- `0 classical_reference`: exact local baselines and finite-system definitions.",
        "- `1 quantum_operator_representation`: Hamiltonians represented as quantum operators.",
        "- `2 quantum_circuit_simulation`: circuits or quantum algorithms run in simulators.",
        "- `3 hardware_ready_boundary`: validated circuits are ready for provider submission.",
        "- `4 hardware_executed`: real QPU job submitted and recorded.",
        "",
        "## Surfaces",
        "",
    ]
    for surface in payload["surfaces"]:
        lines.extend(
            [
                f"### {surface['id']}",
                "",
                f"- Track: `{surface['track']}`",
                f"- Level: `{surface['level']} {surface['level_name']}`",
                f"- Status: `{surface['status']}`",
                f"- Real hardware: `{surface['actual_quantum_hardware']}`",
                f"- Command: `{surface['command']}`",
                f"- Meaning: {surface['meaning']}",
                f"- Next gate: {surface['next_gate']}",
                "",
            ]
        )
    ibm = payload["ibm_runtime"]
    lines.extend(
        [
            "## IBM Runtime Readiness",
            "",
            f"- Dependency present: `{ibm['dependency_present']}`",
            f"- Token env present: `{ibm['env_token_present']}`",
            f"- Instance env present: `{ibm['env_instance_present']}`",
            f"- Status: `{ibm['status']}`",
        ]
    )
    if ibm.get("error"):
        lines.append(f"- Error: `{ibm['error']}`")
    if ibm.get("backends"):
        lines.append("- Operational physical backends:")
        for backend in ibm["backends"]:
            lines.append(f"  - `{backend['name']}` ({backend['num_qubits']} qubits)")
    lines.append("")
    return "\n".join(lines)


def _level_name(level: int) -> str:
    for surface in SURFACES:
        if surface.level == level:
            return surface.level_name
    return "unknown"
