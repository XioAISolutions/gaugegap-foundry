"""OriginQ pyQPanda runner for local CPUQVM simulation.

Builds TFIM Trotter circuits using pyQPanda gates and runs them on the
local CPUQVM simulator.  Every result records device, shots, and circuit
metadata in the standard ledger format.

Requires the [originq] optional dependency group.
"""
from __future__ import annotations

from typing import Any


def _check_pyqpanda():
    try:
        import pyqpanda  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "originq_runner requires pyqpanda. "
            "Install with: pip install -e '.[originq]'"
        ) from exc


def build_tfim_trotter_originq(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    time: float,
    steps: int,
    initial_state: str = "zeros",
) -> dict[str, Any]:
    """Build a TFIM Trotter circuit using pyQPanda gates.

    RZZ is decomposed as CNOT · RZ · CNOT since pyQPanda does not have
    a native RZZ gate.
    """
    _check_pyqpanda()
    import pyqpanda as pq

    qvm = pq.CPUQVM()
    qvm.init_qvm()
    qubits = qvm.qAlloc_many(n_sites)
    cbits = qvm.cAlloc_many(n_sites)

    prog = pq.QProg()

    if initial_state == "ones":
        for q in range(n_sites):
            prog << pq.X(qubits[q])
    elif initial_state == "domain_wall":
        for q in range(n_sites // 2, n_sites):
            prog << pq.X(qubits[q])

    dt = time / steps if steps > 0 else 0.0
    for _ in range(steps):
        for site in range(n_sites - 1):
            angle = -2.0 * exchange_coupling * dt
            prog << pq.CNOT(qubits[site], qubits[site + 1])
            prog << pq.RZ(qubits[site + 1], angle)
            prog << pq.CNOT(qubits[site], qubits[site + 1])
        for site in range(n_sites):
            angle = -2.0 * transverse_field * dt
            prog << pq.RX(qubits[site], angle)

    prog << pq.measure_all(qubits, cbits)

    return {
        "qvm": qvm,
        "prog": prog,
        "qubits": qubits,
        "cbits": cbits,
    }


def run_local_cpuqvm(
    n_sites: int,
    exchange_coupling: float,
    transverse_field: float,
    time: float,
    steps: int,
    initial_state: str = "zeros",
    shots: int = 1024,
) -> dict[str, Any]:
    """Run a TFIM Trotter circuit on the pyQPanda CPUQVM."""
    bundle = build_tfim_trotter_originq(
        n_sites, exchange_coupling, transverse_field, time, steps, initial_state
    )
    qvm = bundle["qvm"]
    prog = bundle["prog"]
    cbits = bundle["cbits"]

    counts = qvm.run_with_configuration(prog, cbits, shots)
    qvm.finalize()

    return {
        "provider": "originq-local",
        "device": "CPUQVM",
        "device_id": None,
        "shots": shots,
        "counts": counts,
        "status": "completed",
    }


def originq_counts_to_z_observables(
    counts: dict[str, int],
    n_sites: int,
) -> dict[str, Any]:
    """Extract Z and ZZ expectation values from pyQPanda measurement counts.

    pyQPanda uses the same bit ordering as Qiskit: qubit 0 is the
    rightmost bit in the bitstring.
    """
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("counts must contain at least one shot")

    z_sums = [0.0] * n_sites
    zz_sums = [0.0] * (n_sites - 1)

    for bitstring, count in counts.items():
        bits = list(reversed(bitstring[-n_sites:]))
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


def originq_readiness(probe: bool = False) -> dict[str, Any]:
    """Check pyQPanda availability and optionally probe local simulator."""
    try:
        import pyqpanda  # noqa: F401
        dependency_present = True
    except ImportError:
        dependency_present = False

    result: dict[str, Any] = {
        "dependency_present": dependency_present,
        "local_simulator_available": dependency_present,
        "probe_requested": probe,
        "status": "not_probed",
    }

    if not probe:
        return result

    if not dependency_present:
        result["status"] = "missing_dependency"
        return result

    try:
        import pyqpanda as pq
        qvm = pq.CPUQVM()
        qvm.init_qvm()
        q = qvm.qAlloc_many(2)
        c = qvm.cAlloc_many(2)
        prog = pq.QProg()
        prog << pq.H(q[0]) << pq.CNOT(q[0], q[1]) << pq.measure_all(q, c)
        counts = qvm.run_with_configuration(prog, c, 10)
        qvm.finalize()
        result["local_simulator_available"] = True
        result["status"] = "local_ok"
    except Exception as exc:
        result["status"] = "local_failed"
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result
