"""CurveRank quantum phase estimation (QPE) for spectral screening.

This module provides the *mathematically correct* QPE primitives used to read
finite eigenvalues of truncated candidate Hilbert-Polya operators out of a
quantum circuit.  It is deliberately split from the runnable script so the
phase <-> eigenvalue logic can be unit-tested without a quantum backend, and so
the same primitives back both ``scripts/run_curverank_qpe.py`` and
``scripts/run_curverank_complete.py``.

Phase convention
----------------
We evolve under ``U = exp(-i H tau)``.  An eigenpair ``H|psi> = E|psi>`` becomes
``U|psi> = exp(-i E tau)|psi> = exp(2*pi*i*phi)|psi>`` where the QPE-measurable
phase is

    phi = (-E * tau / (2*pi))  mod 1   in  [0, 1).

Quantum phase estimation can only resolve ``phi`` modulo 1, so the evolution
time ``tau`` must be small enough that the whole spectrum maps into a window of
width < 1; otherwise distinct eigenvalues *alias* onto the same phase.  The
previous implementation used ``tau = 2*pi / |E_1|``, which sends the very
eigenvalue it is trying to measure to ``phi = 1 == 0`` (mod 1) -- i.e. it
aliases the target to phase zero.  :func:`choose_evolution_time` fixes this by
scaling ``tau`` to the spectral radius with a safety margin.

CLAIM BOUNDARY
--------------
This is spectral screening of finite, truncated toy operators.  It does NOT
prove or disprove the Riemann Hypothesis or the Hilbert-Polya conjecture.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "choose_evolution_time",
    "eigenvalue_to_phase",
    "measured_phase_to_eigenvalue",
    "pad_to_power_of_two",
    "build_qpe_circuit",
    "extract_phase_from_counts",
    "estimate_eigenvalue_qpe",
]


def choose_evolution_time(
    eigenvalues: Sequence[float] | np.ndarray,
    safety: float = 0.8,
) -> float:
    """Pick an evolution time ``tau`` for ``U = exp(-i H tau)`` free of aliasing.

    The QPE-measurable phase of eigenvalue ``E`` is ``-E*tau/(2*pi)`` (mod 1).
    To make the phase map injective on the whole spectrum, the signed phases of
    every eigenvalue must fit inside a window of total width < 1.  With spectral
    radius ``R = max|E|`` the signed phases span ``[-R*tau/(2*pi), R*tau/(2*pi)]``
    of width ``R*tau/pi``; choosing

        tau = safety * pi / R,    0 < safety < 1

    gives a window of width ``safety < 1`` so no two distinct eigenvalues share a
    phase.  ``safety`` also keeps the extreme phases away from the +/-0.5
    wrap point (``|phi| <= safety/2``), which is what
    :func:`measured_phase_to_eigenvalue` relies on to invert the fold.

    Parameters
    ----------
    eigenvalues
        The eigenvalues that the circuit must resolve without aliasing.
    safety
        Fraction of the unit phase window to occupy, in ``(0, 1)``.

    Returns
    -------
    float
        A strictly positive evolution time ``tau``.
    """
    if not 0.0 < safety < 1.0:
        raise ValueError("safety must lie strictly in (0, 1)")
    radius = float(np.max(np.abs(np.asarray(eigenvalues, dtype=float))))
    if radius <= 0.0:
        raise ValueError("spectral radius is zero; cannot choose an evolution time")
    return safety * np.pi / radius


def eigenvalue_to_phase(eigenvalue: float, tau: float) -> float:
    """Map an eigenvalue to its QPE-measurable phase ``phi`` in ``[0, 1)``."""
    return float((-eigenvalue * tau / (2.0 * np.pi)) % 1.0)


def measured_phase_to_eigenvalue(phase: float, tau: float) -> float:
    """Invert :func:`eigenvalue_to_phase`.

    QPE returns ``phi`` in ``[0, 1)``; values above ``0.5`` correspond to
    negative signed phases (the spectrum is folded at ``0.5``).  This undoes the
    fold and recovers ``E = -2*pi*signed_phase/tau``.
    """
    if tau == 0:
        raise ValueError("tau must be non-zero")
    signed = phase - 1.0 if phase > 0.5 else phase
    return float(-2.0 * np.pi * signed / tau)


def pad_to_power_of_two(
    matrix: np.ndarray,
    vector: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Embed a Hermitian ``matrix`` into the next power-of-two dimension.

    QPE needs a system register of whole qubits, i.e. a dimension that is a
    power of two.  We block-embed the operator as ``diag(H, 0)``; the padded
    eigenvalues are exactly ``0`` and the corresponding amplitudes of a properly
    zero-padded eigenvector are ``0``, so a QPE run prepared on an original
    eigenstate is unaffected by the padding.

    Returns the padded matrix and (if given) the zero-padded vector.
    """
    n = matrix.shape[0]
    target = 1 << (n - 1).bit_length()
    if target == n:
        return matrix, vector
    padded = np.zeros((target, target), dtype=complex)
    padded[:n, :n] = matrix
    if vector is None:
        return padded, None
    pv = np.zeros(target, dtype=complex)
    pv[:n] = vector
    return padded, pv


def build_qpe_circuit(
    unitary: np.ndarray,
    n_precision: int = 6,
    initial_statevector: Optional[np.ndarray] = None,
):
    """Build a textbook QPE circuit for the (power-of-two) ``unitary``.

    Parameters
    ----------
    unitary
        ``U = exp(-i H tau)``; its dimension must be a power of two.
    n_precision
        Number of counting/precision qubits (phase resolution ``2**-n``).
    initial_statevector
        State to load into the system register.  For a clean read this should be
        (close to) an eigenvector of ``U``.  If ``None`` the system register is
        left in an equal superposition over the computational basis.

    Notes
    -----
    Qiskit is imported lazily so this module stays importable in environments
    that only install the classical/spectral extras.
    """
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.circuit.library import QFTGate, UnitaryGate

    dim = unitary.shape[0]
    n_system = dim.bit_length() - 1
    if 1 << n_system != dim:
        raise ValueError(
            f"unitary dimension {dim} is not a power of two; "
            "pad the operator with pad_to_power_of_two() first"
        )

    precision_reg = QuantumRegister(n_precision, "precision")
    system_reg = QuantumRegister(n_system, "system")
    classical_reg = ClassicalRegister(n_precision, "c")
    qc = QuantumCircuit(precision_reg, system_reg, classical_reg)

    for i in range(n_precision):
        qc.h(precision_reg[i])

    if initial_statevector is not None:
        state = np.asarray(initial_statevector, dtype=complex)
        norm = np.linalg.norm(state)
        if norm == 0:
            raise ValueError("initial_statevector must be non-zero")
        qc.initialize(state / norm, system_reg)
    else:
        for q in system_reg:
            qc.h(q)

    # Controlled-U^(2^k); the k-th counting qubit controls U raised to 2**k.
    for k in range(n_precision):
        u_power = np.linalg.matrix_power(unitary, 2 ** k)
        gate = UnitaryGate(u_power, label=f"U^2^{k}").control(1)
        qc.append(gate, [precision_reg[k]] + list(system_reg))

    qc.append(QFTGate(n_precision).inverse(), precision_reg)
    qc.measure(precision_reg, classical_reg)
    return qc


def extract_phase_from_counts(
    counts: Dict[str, int],
    n_precision: int,
) -> Tuple[float, float]:
    """Read the most likely phase ``phi`` in ``[0, 1)`` from measurement counts.

    Returns ``(phase, uncertainty)``.  The counting register is read with the
    standard Qiskit big-endian convention, so ``phi = int(bits, 2) / 2**n``.
    """
    if not counts:
        return 0.0, 1.0
    best_bits = max(counts, key=counts.get)
    # Counts keys may contain spaces if several classical registers exist; we
    # only created one, but strip defensively.
    bits = best_bits.replace(" ", "")
    value = int(bits, 2)
    phase = value / (2 ** n_precision)

    total = sum(counts.values())
    best = counts[best_bits]
    # Resolution-limited uncertainty, widened when the peak is not dominant.
    confidence = best / total if total else 0.0
    uncertainty = (1.0 / (2 ** n_precision)) / max(confidence, 1e-9) ** 0.5
    return phase, uncertainty


def estimate_eigenvalue_qpe(
    hamiltonian: np.ndarray,
    eigenvector: np.ndarray,
    n_precision: int = 8,
    shots: int = 4096,
    safety: float = 0.8,
    eigenvalues: Optional[np.ndarray] = None,
    backend: Any = None,
) -> Dict[str, Any]:
    """Estimate one eigenvalue of ``hamiltonian`` via QPE on a simulator.

    The aliasing-free evolution time is chosen from the full spectrum, the given
    ``eigenvector`` is loaded into the system register, the circuit is run on an
    Aer simulator (or the supplied ``backend``), and the measured phase is
    inverted to an eigenvalue estimate.

    Returns a dict with the estimate, its uncertainty, the evolution time, the
    measured phase, and the predicted phase for cross-checking.
    """
    from qiskit import transpile

    H = np.asarray(hamiltonian, dtype=complex)
    vec = np.asarray(eigenvector, dtype=complex)

    spectrum = (
        np.asarray(eigenvalues, dtype=float)
        if eigenvalues is not None
        else np.linalg.eigvalsh(H).astype(float)
    )
    tau = choose_evolution_time(spectrum, safety=safety)

    H_pad, vec_pad = pad_to_power_of_two(H, vec)
    from scipy.linalg import expm

    U = expm(-1j * H_pad * tau)
    qc = build_qpe_circuit(U, n_precision=n_precision, initial_statevector=vec_pad)

    if backend is None:
        from qiskit_aer import AerSimulator

        backend = AerSimulator()

    tqc = transpile(qc, backend, basis_gates=["u", "cx"], optimization_level=1)
    counts = backend.run(tqc, shots=shots).result().get_counts()

    phase, phase_unc = extract_phase_from_counts(counts, n_precision)
    estimate = measured_phase_to_eigenvalue(phase, tau)
    eig_unc = abs(measured_phase_to_eigenvalue(phase_unc, tau) - measured_phase_to_eigenvalue(0.0, tau))

    return {
        "estimated_eigenvalue": estimate,
        "eigenvalue_uncertainty": eig_unc,
        "evolution_time": tau,
        "measured_phase": phase,
        "phase_uncertainty": phase_unc,
        "n_precision": n_precision,
        "shots": shots,
        "n_qubits": qc.num_qubits,
        "circuit_depth": qc.depth(),
        "counts": counts,
    }
