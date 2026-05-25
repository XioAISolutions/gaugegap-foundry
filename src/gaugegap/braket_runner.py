"""Amazon Braket runner for local simulation and cloud QPU access.

Supports Braket local simulator (StateVectorSimulator) for validation and
cloud devices (IonQ, Rigetti, QuEra Aquila) when AWS credentials are
configured.  Every result records device ARN, shots, and task metadata.

Requires the [braket] optional dependency group.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def _check_braket():
    try:
        from braket.circuits import Circuit  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "braket_runner requires amazon-braket-sdk. "
            "Install with: pip install -e '.[braket]'"
        ) from exc


def run_local_simulator(
    circuit,
    shots: int = 1024,
) -> dict[str, Any]:
    """Run a Braket circuit on the local StateVectorSimulator."""
    _check_braket()
    from braket.devices import LocalSimulator

    device = LocalSimulator()
    task = device.run(circuit, shots=shots)
    result = task.result()
    counts = dict(result.measurement_counts)

    return {
        "provider": "braket-local",
        "device": "LocalSimulator",
        "device_arn": None,
        "shots": shots,
        "counts": counts,
        "measured_qubits": result.measured_qubits,
        "status": "completed",
    }


def qiskit_to_braket(qiskit_circuit) -> Any:
    """Convert a Qiskit circuit to a Braket circuit via OpenQASM 3."""
    _check_braket()
    from braket.circuits import Circuit as BraketCircuit

    qasm3 = qiskit_circuit.qasm()
    return BraketCircuit.from_ir(qasm3)


def build_tfim_trotter_braket(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    time: float,
    steps: int,
    initial_state: str = "zeros",
) -> Any:
    """Build a TFIM Trotter circuit natively in Braket gates."""
    _check_braket()
    from braket.circuits import Circuit

    circuit = Circuit()

    if initial_state == "ones":
        for q in range(n_sites):
            circuit.x(q)
    elif initial_state == "domain_wall":
        for q in range(n_sites // 2, n_sites):
            circuit.x(q)

    dt = time / steps
    for _ in range(steps):
        for site in range(n_sites - 1):
            angle = -2.0 * exchange_coupling * dt
            circuit.zz(site, site + 1, angle)
        for site in range(n_sites):
            angle = -2.0 * transverse_field * dt
            circuit.rx(site, angle)

    return circuit


def braket_counts_to_z_observables(
    counts: dict[str, int],
    n_sites: int,
) -> dict[str, Any]:
    """Extract Z and ZZ expectation values from Braket measurement counts."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("counts must contain at least one shot")

    z_sums = [0.0] * n_sites
    zz_sums = [0.0] * (n_sites - 1)

    for bitstring, count in counts.items():
        bits = bitstring[:n_sites]
        z_vals = [1.0 if b == "0" else -1.0 for b in bits]
        for site, val in enumerate(z_vals):
            z_sums[site] += count * val
        for site in range(n_sites - 1):
            zz_sums[site] += count * z_vals[site] * z_vals[site + 1]

    return {
        "z": [s / total for s in z_sums],
        "zz": [s / total for s in zz_sums],
        "shots": total,
    }


CLOUD_DEVICES = {
    "ionq-aria1": "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1",
    "ionq-aria2": "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-2",
    "ionq-forte1": "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1",
    "rigetti-ankaa2": "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-2",
    "quera-aquila": "arn:aws:braket:us-east-1::device/qpu/quera/Aquila",
    "sv1": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    "dm1": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
    "tn1": "arn:aws:braket:::device/quantum-simulator/amazon/tn1",
}


def run_cloud_device(
    circuit,
    device_name: str,
    shots: int = 1024,
    s3_bucket: str | None = None,
    s3_prefix: str = "gaugegap-foundry",
) -> dict[str, Any]:
    """Submit a Braket circuit to a cloud QPU or managed simulator."""
    _check_braket()
    from braket.aws import AwsDevice, AwsQuantumTask

    arn = CLOUD_DEVICES.get(device_name)
    if arn is None:
        arn = device_name

    device = AwsDevice(arn)

    if s3_bucket is None:
        s3_bucket = f"amazon-braket-{device.name.lower().replace(' ', '-')}"
    s3_location = (s3_bucket, s3_prefix)

    task = device.run(circuit, shots=shots, s3_destination_folder=s3_location)
    result = task.result()
    counts = dict(result.measurement_counts)

    return {
        "provider": "braket-cloud",
        "device": device.name,
        "device_arn": arn,
        "task_id": task.id,
        "shots": shots,
        "counts": counts,
        "measured_qubits": result.measured_qubits,
        "status": "completed",
    }


def braket_readiness(probe: bool = False) -> dict[str, Any]:
    """Check Braket SDK availability and optionally probe AWS access."""
    try:
        import braket  # noqa: F401
        dependency_present = True
    except ImportError:
        dependency_present = False

    import os
    aws_configured = bool(
        os.getenv("AWS_ACCESS_KEY_ID")
        or os.getenv("AWS_PROFILE")
        or os.getenv("AWS_DEFAULT_REGION")
    )

    result: dict[str, Any] = {
        "dependency_present": dependency_present,
        "aws_credentials_present": aws_configured,
        "local_simulator_available": dependency_present,
        "probe_requested": probe,
        "status": "not_probed",
        "devices": [],
    }

    if not probe:
        return result

    if not dependency_present:
        result["status"] = "missing_dependency"
        return result

    try:
        from braket.devices import LocalSimulator
        from braket.circuits import Circuit
        dev = LocalSimulator()
        c = Circuit().h(0).cnot(0, 1)
        r = dev.run(c, shots=10).result()
        result["local_simulator_available"] = True
        result["status"] = "local_ok"
    except Exception as exc:
        result["status"] = "local_failed"
        result["error"] = f"{type(exc).__name__}: {exc}"

    if aws_configured:
        try:
            from braket.aws import AwsDevice
            devices = AwsDevice.get_devices(statuses=["ONLINE"])
            result["devices"] = [
                {"name": d.name, "arn": d.arn, "status": d.status}
                for d in devices
            ]
            result["status"] = "cloud_ok"
        except Exception as exc:
            if result["status"] != "local_failed":
                result["status"] = "cloud_probe_failed"
            result["cloud_error"] = f"{type(exc).__name__}: {exc}"

    return result
