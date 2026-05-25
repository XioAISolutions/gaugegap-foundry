"""FlowGap: VQLS-style quantum subroutine for tiny pressure-Poisson solves.

Requires the [quantum] optional dependency group.
This is a finite reduced-model benchmark, not a Navier-Stokes regularity claim.
"""
from __future__ import annotations

import numpy as np

from gaugegap.flowgap_burgers import poisson_matrix_1d, pressure_poisson_2d


def _check_qiskit():
    try:
        from qiskit.quantum_info import SparsePauliOp  # noqa: F401
        from qiskit.circuit import QuantumCircuit  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "flowgap_qsubroutine requires qiskit. "
            "Install with: pip install -e '.[quantum]'"
        ) from exc


def matrix_to_pauli_op(matrix: np.ndarray):
    _check_qiskit()
    from qiskit.quantum_info import SparsePauliOp
    return SparsePauliOp.from_operator(matrix)


def _hardware_efficient_ansatz(n_qubits: int, depth: int):
    _check_qiskit()
    from qiskit.circuit import QuantumCircuit, ParameterVector

    params = ParameterVector("θ", n_qubits * (depth + 1))
    qc = QuantumCircuit(n_qubits)

    idx = 0
    for d in range(depth):
        for q in range(n_qubits):
            qc.ry(params[idx], q)
            idx += 1
        for q in range(n_qubits - 1):
            qc.cx(q, q + 1)

    for q in range(n_qubits):
        qc.ry(params[idx], q)
        idx += 1

    return qc, params


def vqls_cost_statevector(
    params_values: np.ndarray,
    A: np.ndarray,
    b: np.ndarray,
    ansatz_circuit,
    param_vector,
) -> float:
    _check_qiskit()
    from qiskit.quantum_info import Statevector

    bound = ansatz_circuit.assign_parameters(
        dict(zip(param_vector, params_values))
    )
    psi = Statevector(bound).data

    norm_psi = np.linalg.norm(psi)
    if norm_psi < 1e-15:
        return 1e6
    psi = psi / norm_psi

    Ax = A @ psi
    norm_Ax = np.linalg.norm(Ax)
    if norm_Ax < 1e-15:
        return 1e6

    b_norm = b / np.linalg.norm(b)
    Ax_norm = Ax / norm_Ax

    cost = 1.0 - abs(np.dot(b_norm.conj(), Ax_norm)) ** 2
    return float(cost)


def run_vqls_poisson_1d(
    nx: int,
    rhs: np.ndarray | None = None,
    depth: int = 2,
    max_iter: int = 200,
    learning_rate: float = 0.05,
) -> dict[str, object]:
    _check_qiskit()
    n_qubits = int(np.log2(nx))
    if 2 ** n_qubits != nx:
        raise ValueError(f"nx must be a power of 2, got {nx}")

    A = poisson_matrix_1d(nx)
    if rhs is None:
        x = np.linspace(0, 1, nx, endpoint=False)
        rhs = -np.sin(2.0 * np.pi * x)

    b = rhs - np.mean(rhs)
    b_norm = np.linalg.norm(b)
    if b_norm < 1e-15:
        return {
            "p_quantum": np.zeros(nx),
            "p_classical": np.zeros(nx),
            "l2_error": 0.0,
            "poisson_residual": 0.0,
            "cost_history": [],
            "n_iter": 0,
        }
    b = b / b_norm

    A_pinv = np.linalg.pinv(A)
    p_classical = A_pinv @ (rhs - np.mean(rhs))
    p_classical -= np.mean(p_classical)

    ansatz, params = _hardware_efficient_ansatz(n_qubits, depth)
    theta = np.random.default_rng(42).uniform(-np.pi, np.pi, size=len(params))

    cost_history: list[float] = []
    eps = 1e-5
    for iteration in range(max_iter):
        cost = vqls_cost_statevector(theta, A, b, ansatz, params)
        cost_history.append(cost)

        if cost < 1e-8:
            break

        grad = np.zeros_like(theta)
        for j in range(len(theta)):
            theta_p = theta.copy()
            theta_m = theta.copy()
            theta_p[j] += eps
            theta_m[j] -= eps
            grad[j] = (
                vqls_cost_statevector(theta_p, A, b, ansatz, params)
                - vqls_cost_statevector(theta_m, A, b, ansatz, params)
            ) / (2 * eps)

        theta -= learning_rate * grad

    from qiskit.quantum_info import Statevector

    bound = ansatz.assign_parameters(dict(zip(params, theta)))
    psi_final = Statevector(bound).data.real
    psi_final = psi_final / np.linalg.norm(psi_final)

    Ax = A @ psi_final
    scale = np.dot(rhs - np.mean(rhs), Ax) / np.dot(Ax, Ax) if np.dot(Ax, Ax) > 1e-15 else 1.0
    p_quantum = psi_final * scale
    p_quantum -= np.mean(p_quantum)

    residual = float(np.linalg.norm(A @ p_quantum - (rhs - np.mean(rhs))))
    l2_error = float(np.linalg.norm(p_quantum - p_classical))

    return {
        "p_quantum": p_quantum,
        "p_classical": p_classical,
        "l2_error": l2_error,
        "poisson_residual": residual,
        "cost_history": cost_history,
        "n_iter": len(cost_history),
    }
