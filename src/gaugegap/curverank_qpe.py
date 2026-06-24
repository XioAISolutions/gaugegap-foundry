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
    "choose_evolution_time_windowed",
    "unwrap_phase_to_eigenvalue",
    "eigenvalue_to_phase",
    "measured_phase_to_eigenvalue",
    "pad_to_power_of_two",
    "hamiltonian_to_sparse_pauli",
    "build_qpe_circuit",
    "build_qpe_circuit_trotter",
    "extract_phase_from_counts",
    "estimate_eigenvalue_qpe",
    "estimate_eigenvalue_iterative_qpe",
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


def choose_evolution_time_windowed(window_radius: float, safety: float = 0.8) -> float:
    """Evolution time for *windowed* QPE targeting one eigenvalue.

    When the prepared state is (close to) an eigenstate and classical screening
    supplies a prior window ``|E - center| <= window_radius``, the global
    no-aliasing constraint of :func:`choose_evolution_time` is unnecessarily
    conservative: the phase only needs to be injective *on the window*.  Taking

        tau = safety * pi / window_radius

    makes one full phase turn correspond to ``2*window_radius/safety``, so the
    per-bin eigenvalue resolution improves by the ratio (spectral radius /
    window radius) relative to the global choice.  The measured phase then
    determines ``E`` only modulo ``2*pi/tau``; :func:`unwrap_phase_to_eigenvalue`
    resolves that wrap using the window prior.

    TRUST MODEL: windowed estimates additionally rely on (i) the prepared state
    being an eigenstate of the targeted eigenvalue and (ii) the classical window
    prior actually containing it.  Out-of-window spectral components alias to
    arbitrary phases (suppressed only by their amplitude in the prepared state).
    """
    if not 0.0 < safety < 1.0:
        raise ValueError("safety must lie strictly in (0, 1)")
    if window_radius <= 0.0:
        raise ValueError("window_radius must be positive")
    return safety * np.pi / window_radius


def unwrap_phase_to_eigenvalue(phase: float, tau: float, center: float) -> float:
    """Invert a (possibly wrapped) QPE phase using a window prior.

    The measured phase determines ``E`` modulo ``2*pi/tau``; among the lattice
    of candidates ``-2*pi*phase/tau + m*(2*pi)/tau`` this returns the one
    closest to ``center``.  With ``tau`` from
    :func:`choose_evolution_time_windowed` exactly one candidate lies inside
    the prior window, so the choice is unambiguous whenever the prior holds.
    """
    if tau == 0:
        raise ValueError("tau must be non-zero")
    period = 2.0 * np.pi / tau
    base = -2.0 * np.pi * phase / tau
    m = round((center - base) / period)
    return float(base + m * period)


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


def hamiltonian_to_sparse_pauli(hamiltonian: np.ndarray, atol: float = 1e-12):
    """Decompose a Hermitian (power-of-two) matrix into a ``SparsePauliOp``.

    This is the bridge from the dense truncated operator to a *gate-efficient*
    representation: once ``H`` is a sum of Pauli strings, ``exp(-iHt)`` can be
    realised by Trotterised Pauli rotations whose depth scales polynomially,
    rather than synthesising a dense controlled unitary (which blows up the
    two-qubit-gate count and is infeasible on hardware).
    """
    from qiskit.quantum_info import Operator, SparsePauliOp

    op = SparsePauliOp.from_operator(Operator(np.asarray(hamiltonian, dtype=complex)))
    return op.simplify(atol=atol)


def build_qpe_circuit_trotter(
    pauli_op,
    tau: float,
    n_precision: int = 6,
    reps: int = 2,
    initial_statevector: Optional[np.ndarray] = None,
):
    """QPE circuit whose controlled ``U^(2^k)`` use Trotterised time evolution.

    Identical structure to :func:`build_qpe_circuit`, but each controlled power
    is ``controlled-exp(-i H * tau * 2^k)`` realised with a
    :class:`~qiskit.circuit.library.PauliEvolutionGate` (Lie-Trotter synthesis)
    instead of a dense controlled unitary. The Trotter step count is scaled with
    the evolution time (``reps * 2^k``) so the Trotter synthesis error stays roughly
    uniform across the precision register -- the higher-order bits, which use the
    longest evolutions, get proportionally more steps. (Known limitation: this is
    a Trotter prototype; the per-bit step scaling is a heuristic and the residual
    Trotter error is bounded only approximately, not certified.)

    Parameters
    ----------
    pauli_op
        ``SparsePauliOp`` for the (power-of-two) Hamiltonian.
    tau
        Base evolution time (use :func:`choose_evolution_time`).
    reps
        Trotter steps for the ``k=0`` power; higher powers use ``reps * 2^k``.
    """
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.circuit.library import PauliEvolutionGate, QFTGate
    from qiskit.synthesis import LieTrotter

    n_system = pauli_op.num_qubits
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

    for k in range(n_precision):
        steps = max(1, reps * (2 ** k))
        evo = PauliEvolutionGate(
            pauli_op, time=tau * (2 ** k), synthesis=LieTrotter(reps=steps)
        )
        qc.append(evo.control(1), [precision_reg[k]] + list(system_reg))

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
    method: str = "dense",
    reps: int = 2,
    window: Optional[tuple] = None,
) -> Dict[str, Any]:
    """Estimate one eigenvalue of ``hamiltonian`` via QPE.

    The aliasing-free evolution time is chosen from the full spectrum, the given
    ``eigenvector`` is loaded into the system register, the circuit is run on an
    Aer simulator (or the supplied ``backend``), and the measured phase is
    inverted to an eigenvalue estimate.

    Parameters
    ----------
    method : {"dense", "trotter"}
        ``"dense"`` builds an exact controlled ``exp(-iH tau)`` from the matrix
        (accurate, but synthesises into many gates -- simulator only).
        ``"trotter"`` uses controlled Trotterised Pauli evolution
        (gate-efficient, the path toward real hardware).
    reps
        Trotter steps for the ``k=0`` power when ``method == "trotter"``.
    window : (center, radius), optional
        Classical prior ``|E - center| <= radius`` for the targeted eigenvalue.
        When given, ``tau`` is scaled to the window instead of the full spectral
        radius (:func:`choose_evolution_time_windowed`), improving the per-bin
        resolution by the ratio (spectral radius / window radius); the measured
        phase is unwrapped against ``center``. See that function's TRUST MODEL.

    Returns a dict with the estimate, its uncertainty, the evolution time, the
    measured phase, and circuit metadata.
    """
    from qiskit import transpile

    H = np.asarray(hamiltonian, dtype=complex)
    vec = np.asarray(eigenvector, dtype=complex)

    spectrum = (
        np.asarray(eigenvalues, dtype=float)
        if eigenvalues is not None
        else np.linalg.eigvalsh(H).astype(float)
    )
    if window is not None:
        center, radius = float(window[0]), float(window[1])
        tau = choose_evolution_time_windowed(radius, safety=safety)
    else:
        center = None
        tau = choose_evolution_time(spectrum, safety=safety)

    H_pad, vec_pad = pad_to_power_of_two(H, vec)

    if method == "trotter":
        pauli_op = hamiltonian_to_sparse_pauli(H_pad)
        qc = build_qpe_circuit_trotter(
            pauli_op, tau, n_precision=n_precision, reps=reps, initial_statevector=vec_pad
        )
    elif method == "dense":
        from scipy.linalg import expm

        U = expm(-1j * H_pad * tau)
        qc = build_qpe_circuit(U, n_precision=n_precision, initial_statevector=vec_pad)
    else:
        raise ValueError(f"unknown method {method!r}; choose 'dense' or 'trotter'")

    if backend is None:
        from qiskit_aer import AerSimulator

        backend = AerSimulator()

    tqc = transpile(qc, backend, basis_gates=["u", "cx"], optimization_level=1)
    counts = backend.run(tqc, shots=shots).result().get_counts()

    phase, phase_unc = extract_phase_from_counts(counts, n_precision)
    if center is not None:
        estimate = unwrap_phase_to_eigenvalue(phase, tau, center)
    else:
        estimate = measured_phase_to_eigenvalue(phase, tau)
    # Uncertainty is the resolution scale 2*pi/tau times the phase uncertainty;
    # the same for windowed and global modes (unwrapping only shifts by periods).
    eig_unc = abs(2.0 * np.pi * phase_unc / tau)

    return {
        "estimated_eigenvalue": estimate,
        "eigenvalue_uncertainty": eig_unc,
        "evolution_time": tau,
        "measured_phase": phase,
        "phase_uncertainty": phase_unc,
        "method": method,
        "windowed": window is not None,
        "n_precision": n_precision,
        "shots": shots,
        "n_qubits": qc.num_qubits,
        "circuit_depth": qc.depth(),
        "counts": counts,
    }


def estimate_eigenvalue_iterative_qpe(
    hamiltonian: np.ndarray,
    eigenvector: np.ndarray,
    n_iterations: int = 8,
    shots: int = 2048,
    safety: float = 0.8,
    eigenvalues: Optional[np.ndarray] = None,
    backend: Any = None,
    reps: int = 2,
) -> Dict[str, Any]:
    """Estimate one eigenvalue via *iterative* (Kitaev) phase estimation.

    Iterative QPE uses a **single ancilla** qubit and no inverse-QFT: the phase
    bits are read one at a time (least-significant first) and fed back as a phase
    correction on the ancilla. This trades the wide precision register for
    ``n_iterations`` shallow rounds, which is far friendlier to NISQ hardware
    than a full register of controlled unitaries plus a QFT.

    The controlled evolutions use the same Trotterised Pauli rotations as
    :func:`build_qpe_circuit_trotter`, so this is the most hardware-realistic
    path in the module. Feedback is applied across separate circuit executions
    (one per bit, majority vote), which needs no mid-circuit measurement and so
    runs on any backend.

    Returns a dict with the estimate, the recovered phase, the per-bit values,
    and the evolution time.
    """
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit.circuit.library import PauliEvolutionGate
    from qiskit.synthesis import LieTrotter

    H = np.asarray(hamiltonian, dtype=complex)
    vec = np.asarray(eigenvector, dtype=complex)
    spectrum = (
        np.asarray(eigenvalues, dtype=float)
        if eigenvalues is not None
        else np.linalg.eigvalsh(H).astype(float)
    )
    tau = choose_evolution_time(spectrum, safety=safety)

    H_pad, vec_pad = pad_to_power_of_two(H, vec)
    pauli_op = hamiltonian_to_sparse_pauli(H_pad)
    n_system = pauli_op.num_qubits
    state = vec_pad / np.linalg.norm(vec_pad)

    if backend is None:
        from qiskit_aer import AerSimulator

        backend = AerSimulator()

    def _round(k: int, omega: float) -> int:
        ancilla = QuantumRegister(1, "ancilla")
        system = QuantumRegister(n_system, "system")
        creg = ClassicalRegister(1, "c")
        qc = QuantumCircuit(ancilla, system, creg)
        qc.initialize(state, system)
        qc.h(ancilla[0])
        steps = max(1, reps * (2 ** k))
        evo = PauliEvolutionGate(
            pauli_op, time=tau * (2 ** k), synthesis=LieTrotter(reps=steps)
        )
        qc.append(evo.control(1), [ancilla[0]] + list(system))
        qc.p(-2.0 * np.pi * omega, ancilla[0])  # classical feedback
        qc.h(ancilla[0])
        qc.measure(ancilla[0], creg[0])
        tqc = transpile(qc, backend, basis_gates=["u", "cx"], optimization_level=1)
        counts = backend.run(tqc, shots=shots).result().get_counts()
        return 1 if counts.get("1", 0) > counts.get("0", 0) else 0

    bits: Dict[int, int] = {}
    # Process exponents from high to low; round at exponent k yields bit index
    # (n-1-k) of the n-bit phase, with feedback from already-known lower bits.
    n = n_iterations
    for k in range(n - 1, -1, -1):
        target_bit = n - 1 - k
        omega = sum(bits[j] * 2.0 ** (j + k - n) for j in range(target_bit))
        bits[target_bit] = _round(k, omega)

    m = sum(bits[j] * (2 ** j) for j in range(n))
    phase = m / (2 ** n)
    estimate = measured_phase_to_eigenvalue(phase, tau)

    return {
        "estimated_eigenvalue": estimate,
        "evolution_time": tau,
        "measured_phase": phase,
        "phase_bits": [bits[j] for j in range(n)],
        "method": "iterative",
        "n_iterations": n_iterations,
        "shots": shots,
        "n_qubits": n_system + 1,
    }
