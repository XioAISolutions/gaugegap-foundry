"""Optional NVIDIA CUDA-Q simulation backend (capability-gated, CPU fallback).

CUDA-Q (https://github.com/NVIDIA/cuda-quantum, Apache-2.0) is a hybrid
quantum-classical platform with GPU-accelerated statevector / tensor-network
simulators. Its value to this repo is **accelerating the existing quantum
simulations** (QPE, the correlation signal ``g(t)``) to larger qubit counts than
Aer/numpy handle comfortably -- *not* the certified core, which is CPU interval
arithmetic.

Design, in keeping with the repo's verification-first / quantum-optional stance:

- **Capability-gated.** ``cudaq_available()`` is the only thing that decides
  whether the GPU path runs. Importing this module never requires CUDA-Q or a GPU.
- **CPU fallback always present.** The numpy statevector backend is the tested,
  always-available reference; ``statevector(..., backend="auto")`` uses CUDA-Q
  only when installed and falls back to numpy otherwise.
- **Parity, not trust.** A skip-guarded test compares the CUDA-Q path to the numpy
  reference; CI (no GPU) verifies the fallback. The GPU path is exercised only
  where CUDA-Q + a GPU are present.

This adapter is a thin, portable gate-list statevector primitive (the unit other
quantum code can target); wiring it into the full QPE/``g(t)`` pipelines is the
follow-up described in ``docs/cudaq-evaluation.md``.

CLAIM BOUNDARY: simulation acceleration only. Nothing here changes any result or
bears on a proof of the Riemann Hypothesis.
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np

# A gate is (name, qubits, param): 1q in {h,x,y,z,rx,ry,rz}, 2q {cx}.
Gate = Tuple[str, Tuple[int, ...], Optional[float]]

_1Q = {
    "h": lambda p: np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
    "x": lambda p: np.array([[0, 1], [1, 0]], dtype=complex),
    "y": lambda p: np.array([[0, -1j], [1j, 0]], dtype=complex),
    "z": lambda p: np.array([[1, 0], [0, -1]], dtype=complex),
    "rx": lambda p: np.array([[np.cos(p / 2), -1j * np.sin(p / 2)],
                              [-1j * np.sin(p / 2), np.cos(p / 2)]], dtype=complex),
    "ry": lambda p: np.array([[np.cos(p / 2), -np.sin(p / 2)],
                              [np.sin(p / 2), np.cos(p / 2)]], dtype=complex),
    "rz": lambda p: np.array([[np.exp(-1j * p / 2), 0],
                              [0, np.exp(1j * p / 2)]], dtype=complex),
}


def cudaq_available() -> bool:
    """True iff the ``cudaq`` package can be imported (no GPU assumption)."""
    try:
        import cudaq  # noqa: F401
    except Exception:
        return False
    return True


def backend_info() -> dict:
    """Report the active CUDA-Q target (or that it is unavailable)."""
    if not cudaq_available():
        return {"available": False, "fallback": "numpy"}
    import cudaq
    try:
        target = cudaq.get_target().name
    except Exception:
        target = "unknown"
    return {"available": True, "target": target}


# --------------------------------------------------------------------------- #
# numpy reference backend (always available, tested)
# --------------------------------------------------------------------------- #


def _full_1q(U: np.ndarray, q: int, n: int) -> np.ndarray:
    op = np.array([[1.0 + 0j]])
    for i in range(n):
        op = np.kron(op, U if i == q else np.eye(2, dtype=complex))
    return op


def _full_cx(c: int, t: int, n: int) -> np.ndarray:
    dim = 2 ** n
    M = np.zeros((dim, dim), dtype=complex)
    for i in range(dim):
        control = (i >> (n - 1 - c)) & 1
        j = i ^ (1 << (n - 1 - t)) if control else i
        M[j, i] = 1.0
    return M


def numpy_statevector(gates: Sequence[Gate], n_qubits: int) -> np.ndarray:
    """Reference statevector from a gate list (big-endian: qubit 0 is MSB).

    Builds full operators -- O(4^n), fine for the small reference cases; CUDA-Q is
    the path that scales.
    """
    state = np.zeros(2 ** n_qubits, dtype=complex)
    state[0] = 1.0
    for name, qubits, param in gates:
        if name == "cx":
            state = _full_cx(qubits[0], qubits[1], n_qubits) @ state
        elif name in _1Q:
            state = _full_1q(_1Q[name](param), qubits[0], n_qubits) @ state
        else:
            raise ValueError(f"unsupported gate {name!r}")
    return state


# --------------------------------------------------------------------------- #
# CUDA-Q backend (optional)
# --------------------------------------------------------------------------- #


def cudaq_statevector(gates: Sequence[Gate], n_qubits: int) -> np.ndarray:
    """Statevector from a gate list via CUDA-Q (GPU when a GPU target is set).

    Raises ``RuntimeError`` if CUDA-Q is not installed -- callers should use
    :func:`statevector` with ``backend="auto"`` for the fallback.
    """
    if not cudaq_available():
        raise RuntimeError("cudaq is not installed; use backend='auto' for fallback")
    import cudaq

    kernel = cudaq.make_kernel()
    q = kernel.qalloc(n_qubits)
    for name, qubits, param in gates:
        if name == "h":
            kernel.h(q[qubits[0]])
        elif name == "x":
            kernel.x(q[qubits[0]])
        elif name == "y":
            kernel.y(q[qubits[0]])
        elif name == "z":
            kernel.z(q[qubits[0]])
        elif name == "rx":
            kernel.rx(param, q[qubits[0]])
        elif name == "ry":
            kernel.ry(param, q[qubits[0]])
        elif name == "rz":
            kernel.rz(param, q[qubits[0]])
        elif name == "cx":
            kernel.cx(q[qubits[0]], q[qubits[1]])
        else:
            raise ValueError(f"unsupported gate {name!r}")
    return np.asarray(cudaq.get_state(kernel), dtype=complex)


def statevector(
    gates: Sequence[Gate], n_qubits: int, *, backend: str = "auto"
) -> np.ndarray:
    """Simulate a gate list. ``backend``: ``"numpy"``, ``"cudaq"``, or ``"auto"``
    (CUDA-Q when available, else numpy)."""
    if backend == "numpy":
        return numpy_statevector(gates, n_qubits)
    if backend == "cudaq":
        return cudaq_statevector(gates, n_qubits)
    if backend == "auto":
        return cudaq_statevector(gates, n_qubits) if cudaq_available() \
            else numpy_statevector(gates, n_qubits)
    raise ValueError(f"unknown backend {backend!r}")


def ghz_circuit(n_qubits: int) -> List[Gate]:
    """A GHZ-state gate list: H on qubit 0 then a CX ladder."""
    gates: List[Gate] = [("h", (0,), None)]
    gates += [("cx", (i, i + 1), None) for i in range(n_qubits - 1)]
    return gates


# --------------------------------------------------------------------------- #
# GPU-able correlation signal g(t) via a Trotter circuit
# --------------------------------------------------------------------------- #

_PAULI = {
    "I": np.eye(2, dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


def _pauli_matrix(pstring: str) -> np.ndarray:
    M = np.array([[1.0 + 0j]])
    for ch in pstring:
        M = np.kron(M, _PAULI[ch])
    return M


def pauli_decompose(H: np.ndarray, tol: float = 1e-9) -> List[Tuple[float, str]]:
    """Decompose a Hermitian 2^n x 2^n matrix into real Pauli coefficients.

    Returns ``[(coeff, "XIZ"), ...]`` with ``H = sum coeff * P`` and
    ``|coeff| > tol``. Raises if the dimension is not a power of two.
    """
    from itertools import product

    H = np.asarray(H, dtype=complex)
    dim = H.shape[0]
    n = int(round(np.log2(dim)))
    if 2 ** n != dim:
        raise ValueError("pauli_decompose requires a 2^n x 2^n matrix")
    terms: List[Tuple[float, str]] = []
    for letters in product("IXYZ", repeat=n):
        pstring = "".join(letters)
        coeff = np.trace(_pauli_matrix(pstring).conj().T @ H) / dim
        if abs(coeff) > tol:
            terms.append((float(coeff.real), pstring))
    return terms


def _term_gates(coeff: float, pstring: str, dt: float) -> List[Gate]:
    """Gate list for exp(-i coeff dt P) (validated against exact evolution)."""
    active = [q for q, ch in enumerate(pstring) if ch != "I"]
    if not active:
        return []
    pre: List[Gate] = []
    post: List[Gate] = []
    for q in active:
        if pstring[q] == "X":
            pre.append(("h", (q,), None))
            post.append(("h", (q,), None))
        elif pstring[q] == "Y":
            pre.append(("rx", (q,), np.pi / 2))
            post.append(("rx", (q,), -np.pi / 2))
    ladder = [("cx", (active[i], active[i + 1]), None) for i in range(len(active) - 1)]
    unladder = [("cx", (active[i], active[i + 1]), None)
                for i in reversed(range(len(active) - 1))]
    rz = [("rz", (active[-1],), 2.0 * coeff * dt)]
    return pre + ladder + rz + unladder + post


def trotter_gates(terms: Sequence[Tuple[float, str]], t: float, steps: int) -> List[Gate]:
    """First-order Trotter gate list for exp(-iHt) from Pauli ``terms``."""
    dt = t / steps if steps else 0.0
    gates: List[Gate] = []
    for _ in range(steps):
        for coeff, pstring in terms:
            gates += _term_gates(coeff, pstring, dt)
    return gates


def circuit_correlation_signal(
    H: np.ndarray, times: Sequence[float], *, backend: str = "auto",
    trotter_steps: int = 200, prep: str = "plus", pauli_tol: float = 1e-9,
) -> np.ndarray:
    """``g(t) = <psi|exp(-iHt)|psi>`` via a Trotter circuit on the chosen backend.

    This is the GPU-able sibling of ``curverank_signal.correlation_signal``: it
    runs the time evolution as a circuit through :func:`statevector`, so
    ``backend="auto"`` uses the CUDA-Q GPU simulator when available and numpy
    otherwise. ``prep="plus"`` uses |+...+> as the probe state (so g(t) is the
    amplitude of |0...0> after prep -> Trotter -> prep, since H^n is self-inverse).

    The numpy backend is validated against the exact eigendecomposition within
    Trotter error; the CUDA-Q backend runs the identical gate list.
    """
    H = np.asarray(H, dtype=complex)
    dim = H.shape[0]
    n = int(round(np.log2(dim)))
    if 2 ** n != dim:
        raise ValueError("dimension must be a power of two")
    terms = pauli_decompose(H, tol=pauli_tol)
    prep_gates: List[Gate] = ([("h", (q,), None) for q in range(n)]
                              if prep == "plus" else [])
    out = np.empty(len(times), dtype=complex)
    for k, t in enumerate(times):
        gates = prep_gates + trotter_gates(terms, float(t), trotter_steps) + prep_gates
        out[k] = statevector(gates, n, backend=backend)[0]
    return out
