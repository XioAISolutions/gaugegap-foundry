"""Quantum signal extraction from states and superpositions.

This module extracts *signals* — expectation values, phases, overlaps, and the
spectral content — from a pure state ``|psi>`` living in a finite Hilbert space.
It complements the QPE family in ``curverank_qpe`` with the time-series /
super-resolution route plus several standard primitives.

Every routine supports an **exact (statevector) mode** — the noiseless emulator
limit, computed with numpy — so results are deterministic and hermetically
testable. A ``shots`` argument, where present, opts into sampled estimation.

Contents
--------
- ``hadamard_test``        : Re/Im <psi|U|psi> (the core phase/overlap primitive)
- ``correlation_signal``   : g(t) = <psi|exp(-iHt)|psi> = sum_j |<psi|E_j>|^2 e^{-iE_j t}
- ``prony`` / ``esprit``   : super-resolution recovery of frequencies (eigenvalues)
                             and weights from a sampled signal
- ``extract_eigenvalues``  : H, psi -> eigenvalue estimates via the time series
- ``validate_against_certified`` : check estimates against certified enclosures
- ``classical_shadows`` / ``shadow_expectation`` : many observables from few copies
- ``amplitude_estimation`` : maximum-likelihood amplitude estimation (simulated)

CLAIM BOUNDARY
--------------
These extract signals from *finite* operators/states and benchmark the methods.
A quantum-extracted eigenvalue is a (noisy) estimate, never a certificate: it is
cross-checked against the certified interval kernel. Nothing here is a proof of
the Riemann Hypothesis or any Millennium Prize problem.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# 1. Core primitive: the Hadamard test
# --------------------------------------------------------------------------- #


def hadamard_test(
    psi: np.ndarray, U: np.ndarray, *, part: str = "both", shots: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
) -> complex:
    """Estimate ``<psi|U|psi>`` via the Hadamard test.

    Exact mode (``shots=None``) returns the analytic complex value. With
    ``shots`` set, the real and/or imaginary parts are sampled from the
    ancilla-``Z`` distributions ``P(0) = (1 +/- Re/Im)/2`` (the noiseless
    Hadamard-test statistics), modelling shot noise without a full circuit.
    """
    psi = np.asarray(psi, dtype=complex)
    val = complex(np.vdot(psi, U @ psi))
    if shots is None:
        if part == "real":
            return complex(val.real)
        if part == "imag":
            return complex(1j * val.imag)
        return val
    rng = rng or np.random.default_rng()

    def _sample(expectation: float) -> float:
        p0 = min(max((1.0 + expectation) / 2.0, 0.0), 1.0)
        zeros = rng.binomial(shots, p0)
        return 2.0 * (zeros / shots) - 1.0

    re = _sample(val.real) if part in ("real", "both") else 0.0
    im = _sample(val.imag) if part in ("imag", "both") else 0.0
    return complex(re, im)


# --------------------------------------------------------------------------- #
# 2. The correlation signal g(t)
# --------------------------------------------------------------------------- #


def correlation_signal(
    H: np.ndarray, psi: np.ndarray, times: Sequence[float], *,
    shots: Optional[int] = None, dephasing: float = 0.0,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Return ``g(t) = <psi|exp(-iHt)|psi>`` sampled at ``times``.

    Exact mode uses the Hermitian eigendecomposition, so
    ``g(t) = sum_j |<E_j|psi>|^2 exp(-i E_j t)`` -- a sum of complex exponentials
    whose frequencies are exactly the eigenvalues of ``H``.

    ``dephasing`` (>= 0) applies a global coherence-decay envelope
    ``g(t) -> exp(-dephasing * t) * g(t)`` -- a standard model of hardware
    decoherence. ``shots`` adds Hadamard-test shot noise on the (possibly
    dephased) real and imaginary parts. Both default to the noiseless limit.
    """
    H = np.asarray(H, dtype=complex)
    psi = np.asarray(psi, dtype=complex)
    w, V = np.linalg.eigh(H)
    overlaps = np.abs(V.conj().T @ psi) ** 2  # |<E_j|psi>|^2
    times = np.asarray(times, dtype=float)
    g = np.exp(-1j * np.outer(times, w)) @ overlaps
    if dephasing:
        g = g * np.exp(-float(dephasing) * times)
    if shots is None:
        return g
    rng = rng or np.random.default_rng()

    def _sample(x: np.ndarray) -> np.ndarray:
        p0 = np.clip((1.0 + x) / 2.0, 0.0, 1.0)
        return 2.0 * (rng.binomial(shots, p0) / shots) - 1.0

    return _sample(g.real) + 1j * _sample(g.imag)


# --------------------------------------------------------------------------- #
# 3. Super-resolution spectral estimation (Prony, ESPRIT)
# --------------------------------------------------------------------------- #


def _amplitudes_lstsq(signal: np.ndarray, z: np.ndarray) -> np.ndarray:
    k = np.arange(signal.size)
    vander = z[np.newaxis, :] ** k[:, np.newaxis]  # (M, p)
    amps, *_ = np.linalg.lstsq(vander, signal, rcond=None)
    return amps


def prony(signal: np.ndarray, dt: float, order: int) -> Tuple[np.ndarray, np.ndarray]:
    """Prony's method: model ``signal[k] = sum_j A_j z_j^k`` and recover the
    frequencies ``w_j = -arg(z_j)/dt`` and complex amplitudes ``A_j``.

    Returns ``(frequencies, amplitudes)`` sorted ascending by frequency. Requires
    ``len(signal) >= 2*order``.
    """
    signal = np.asarray(signal, dtype=complex)
    M = signal.size
    if M < 2 * order:
        raise ValueError(f"need >= 2*order ({2*order}) samples, got {M}")
    # Linear-prediction (annihilating-filter) system: sum_{m=0}^{order} a_m s_{k+order-m}=0
    rows = M - order
    A = np.empty((rows, order), dtype=complex)
    b = np.empty(rows, dtype=complex)
    for k in range(rows):
        A[k, :] = signal[k:k + order][::-1]
        b[k] = -signal[k + order]
    coeffs, *_ = np.linalg.lstsq(A, b, rcond=None)
    # Characteristic polynomial z^order + a_1 z^{order-1} + ... + a_order
    poly = np.concatenate(([1.0], coeffs))
    z = np.roots(poly)
    freqs = -np.angle(z) / dt
    amps = _amplitudes_lstsq(signal, z)
    idx = np.argsort(freqs)
    return freqs[idx], amps[idx]


def esprit(signal: np.ndarray, dt: float, order: int) -> Tuple[np.ndarray, np.ndarray]:
    """ESPRIT: SVD-based subspace spectral estimation (more noise-robust than
    Prony). Returns ``(frequencies, amplitudes)`` sorted ascending."""
    signal = np.asarray(signal, dtype=complex)
    M = signal.size
    if M < 2 * order:
        raise ValueError(f"need >= 2*order ({2*order}) samples, got {M}")
    L = M // 2
    if L <= order:
        raise ValueError("signal too short for the requested order")
    # Hankel data matrix.
    rows = M - L + 1
    Hk = np.empty((rows, L), dtype=complex)
    for r in range(rows):
        Hk[r, :] = signal[r:r + L]
    U, _s, _vh = np.linalg.svd(Hk, full_matrices=False)
    Us = U[:, :order]               # signal subspace
    U1, U2 = Us[:-1, :], Us[1:, :]  # rotational invariance
    psi_mat, *_ = np.linalg.lstsq(U1, U2, rcond=None)
    z = np.linalg.eigvals(psi_mat)
    freqs = -np.angle(z) / dt
    amps = _amplitudes_lstsq(signal, z)
    idx = np.argsort(freqs)
    return freqs[idx], amps[idx]


# --------------------------------------------------------------------------- #
# 4. End-to-end eigenvalue extraction + certified validation
# --------------------------------------------------------------------------- #


@dataclass
class ExtractionResult:
    method: str
    eigenvalues: np.ndarray      # estimated (real), weight-sorted descending
    weights: np.ndarray          # |amplitude| per recovered mode
    dt: float
    n_times: int


def extract_eigenvalues(
    H: np.ndarray, psi: np.ndarray, *, order: Optional[int] = None,
    n_times: Optional[int] = None, dt: Optional[float] = None,
    method: str = "esprit", shots: Optional[int] = None,
    dephasing: float = 0.0, rng: Optional[np.random.Generator] = None,
) -> ExtractionResult:
    """Recover eigenvalues of ``H`` from the correlation signal of ``|psi>``.

    Chooses a safe (sub-Nyquist) ``dt`` from the spectral radius unless given,
    samples ``g(t)``, and applies Prony or ESPRIT. Modes with negligible weight
    are dropped. The result is *evidence*, validated separately against the
    certified enclosures.
    """
    H = np.asarray(H, dtype=complex)
    dim = H.shape[0]
    w = np.linalg.eigvalsh(H)
    radius = float(np.max(np.abs(w))) or 1.0
    if order is None:
        order = dim
    if dt is None:
        dt = 0.8 * np.pi / radius            # sub-Nyquist for max |eigenvalue|
    if n_times is None:
        n_times = max(4 * order, 2 * order + 2)
    times = np.arange(n_times) * dt
    g = correlation_signal(H, psi, times, shots=shots, dephasing=dephasing, rng=rng)
    estimator = {"prony": prony, "esprit": esprit}[method]
    freqs, amps = estimator(g, dt, order)
    weights = np.abs(amps)
    keep = weights > 1e-6 * max(weights.max(), 1e-30)
    freqs, weights = freqs[keep], weights[keep]
    order_by_weight = np.argsort(weights)[::-1]
    return ExtractionResult(
        method=method, eigenvalues=freqs[order_by_weight],
        weights=weights[order_by_weight], dt=dt, n_times=n_times,
    )


def _qcels_residual(g: np.ndarray, t: np.ndarray, theta: float) -> float:
    """Least-squares residual of a single complex exponential fit at frequency
    ``theta`` (with the optimal amplitude projected out)."""
    A = np.mean(g * np.exp(1j * theta * t))
    return float(np.sum(np.abs(g - A * np.exp(-1j * theta * t)) ** 2))


@dataclass
class QCELSResult:
    eigenvalue: float            # estimated dominant eigenvalue
    total_time: int              # final evolution time used
    levels: int
    dt: float


def qcels(
    H: np.ndarray, psi: np.ndarray, *, total_time: float = 80.0, levels: int = 5,
    grid: int = 200, shots: Optional[int] = None, dephasing: float = 0.0,
    rng: Optional[np.random.Generator] = None,
) -> QCELSResult:
    """Quantum Complex Exponential Least Squares for the *dominant* eigenvalue.

    Fits ``g(t) ~ A e^{-i theta t}`` for the eigenvalue carrying the largest
    overlap weight in ``|psi>``, refining a multilevel schedule that doubles the
    evolution time. The sampling step ``dt`` is held sub-Nyquist (so longer time
    means more samples, not coarser ones), and each level parabolically refines
    the residual minimum. With a clean signal the error scales roughly like
    ``1/total_time`` -- a Heisenberg-style improvement from longer coherent
    evolution rather than more ancillas.
    """
    H = np.asarray(H, dtype=complex)
    w = np.linalg.eigvalsh(H)
    radius = float(np.max(np.abs(w))) or 1.0
    dt = 0.5 * np.pi / radius  # sub-Nyquist for the full band
    rng = rng or np.random.default_rng()
    lo, hi = -radius, radius
    best = 0.0
    for level in range(levels):
        T = total_time / (2 ** (levels - 1 - level))
        n = max(20, int(T / dt))
        t = np.arange(n) * dt
        g = correlation_signal(H, psi, t, shots=shots, dephasing=dephasing, rng=rng)
        thetas = np.linspace(lo, hi, grid)
        res = np.array([_qcels_residual(g, t, th) for th in thetas])
        i = int(np.argmin(res))
        best = float(thetas[i])
        if 0 < i < grid - 1:  # parabolic sub-grid refinement
            y0, y1, y2 = res[i - 1], res[i], res[i + 1]
            denom = y0 - 2 * y1 + y2
            if denom != 0:
                best = thetas[i] + 0.5 * (y0 - y2) / denom * (thetas[1] - thetas[0])
        half = (hi - lo) / 6.0
        lo, hi = best - half, best + half
    return QCELSResult(eigenvalue=best, total_time=int(total_time), levels=levels, dt=dt)


def validate_against_certified(
    estimates: Sequence[float], enclosures, *, pad: float = 1e-6,
) -> List[Dict]:
    """Check each estimate against certified eigenvalue enclosures.

    ``enclosures`` is a list of objects with ``.lower``/``.upper`` (e.g. the
    ``Interval`` outputs of ``certified_*_spectrum``). Returns, per estimate,
    whether it lands inside some certified enclosure and the nearest one.
    """
    bounds = [(float(iv.lower), float(iv.upper)) for iv in enclosures]
    report = []
    for est in estimates:
        inside = any(lo - pad <= est <= hi + pad for lo, hi in bounds)
        nearest = min(bounds, key=lambda b: min(abs(est - b[0]), abs(est - b[1])))
        report.append({
            "estimate": float(est),
            "in_certified_enclosure": bool(inside),
            "nearest_enclosure": [nearest[0], nearest[1]],
        })
    return report


# --------------------------------------------------------------------------- #
# 5. Classical shadows (many observables from few copies)
# --------------------------------------------------------------------------- #

_PAULI = {
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
    "I": np.eye(2, dtype=complex),
}
# Rotation that maps the measurement basis to Z (U|b> are basis eigenstates).
_ROT = {  # U such that U applied before a Z-measurement measures that Pauli
    "X": np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),       # H
    "Y": np.array([[1, -1j], [1, 1j]], dtype=complex) / np.sqrt(2),     # H S^dagger
    "Z": np.eye(2, dtype=complex),
}


def classical_shadows(
    psi: np.ndarray, n_qubits: int, n_shadows: int, *,
    seed: Optional[int] = None,
) -> List[Tuple[str, Tuple[int, ...]]]:
    """Collect ``n_shadows`` random-Pauli classical shadows of ``|psi>``.

    Each shadow is ``(bases, outcomes)`` with a uniformly random Pauli basis per
    qubit and a measured bit per qubit, sampled from the true outcome
    distribution. Post-process with :func:`shadow_expectation`.
    """
    rng = np.random.default_rng(seed)
    psi = np.asarray(psi, dtype=complex).reshape(-1)
    shadows: List[Tuple[str, Tuple[int, ...]]] = []
    for _ in range(n_shadows):
        bases = "".join(rng.choice(list("XYZ")) for _ in range(n_qubits))
        Ufull = np.array([[1.0 + 0j]])
        for ch in bases:
            Ufull = np.kron(Ufull, _ROT[ch])
        rotated = Ufull @ psi
        probs = np.abs(rotated) ** 2
        probs /= probs.sum()
        idx = int(rng.choice(probs.size, p=probs))
        bits = tuple((idx >> (n_qubits - 1 - q)) & 1 for q in range(n_qubits))
        shadows.append((bases, bits))
    return shadows


def _single_qubit_snapshot(basis: str, bit: int) -> np.ndarray:
    """3 U^dagger |b><b| U - I  for one qubit (the inverse-channel estimator)."""
    U = _ROT[basis]
    ket = np.array([1, 0], dtype=complex) if bit == 0 else np.array([0, 1], dtype=complex)
    state = U.conj().T @ ket
    proj = np.outer(state, state.conj())
    return 3.0 * proj - np.eye(2, dtype=complex)


def shadow_expectation(
    shadows: Sequence[Tuple[str, Tuple[int, ...]]], observable: str, *,
    batches: int = 8,
) -> float:
    """Median-of-means estimate of ``<O>`` for a Pauli ``observable`` string
    (e.g. ``"ZII"``, ``"XX"``) from classical shadows."""
    paulis = [_PAULI[c] for c in observable]
    per_shadow = []
    for bases, bits in shadows:
        val = 1.0 + 0j
        for q, P in enumerate(paulis):
            if observable[q] == "I":
                continue
            rho = _single_qubit_snapshot(bases[q], bits[q])
            val *= np.trace(P @ rho)
        per_shadow.append(val.real)
    per_shadow = np.asarray(per_shadow)
    batches = max(1, min(batches, per_shadow.size))
    means = [b.mean() for b in np.array_split(per_shadow, batches)]
    return float(np.median(means))


# --------------------------------------------------------------------------- #
# 6. Amplitude estimation (maximum-likelihood, simulated)
# --------------------------------------------------------------------------- #


def amplitude_estimation(
    psi: np.ndarray, marked: Sequence[int], *,
    powers: Optional[Sequence[int]] = None, shots: int = 256,
    seed: Optional[int] = None, grid: int = 2000,
) -> Dict[str, float]:
    """Maximum-likelihood amplitude estimation of ``a = ||P_marked |psi>||``.

    Faithfully simulates the Grover operator ``Q = -(I - 2|psi><psi|)(I - 2P)``:
    for each Grover power ``m``, ``Q^m|psi>`` has marked-probability
    ``sin^2((2m+1) theta)`` with ``a = sin(theta)``. Outcomes are sampled and a
    grid MLE recovers ``a`` -- the Heisenberg-style schedule beats plain sampling.
    """
    rng = np.random.default_rng(seed)
    psi = np.asarray(psi, dtype=complex).reshape(-1)
    dim = psi.size
    P = np.zeros((dim, dim), dtype=complex)
    for i in marked:
        P[i, i] = 1.0
    a_true = float(np.sqrt(np.real(np.vdot(psi, P @ psi))))
    R_psi = np.eye(dim, dtype=complex) - 2.0 * np.outer(psi, psi.conj())
    R_good = np.eye(dim, dtype=complex) - 2.0 * P
    Q = -R_psi @ R_good
    if powers is None:
        powers = [0, 1, 2, 4, 8]

    # Sample marked-counts at each Grover power from the exact probability.
    data = []
    Qm = np.eye(dim, dtype=complex)
    cache = {0: psi.copy()}
    state = psi.copy()
    for m in range(max(powers) + 1):
        cache[m] = state.copy()
        state = Q @ state
    for m in powers:
        sm = cache[m]
        p_good = float(np.real(np.vdot(sm, P @ sm)))
        p_good = min(max(p_good, 0.0), 1.0)
        hits = int(rng.binomial(shots, p_good))
        data.append((m, hits))

    thetas = np.linspace(1e-6, np.pi / 2 - 1e-6, grid)
    loglik = np.zeros_like(thetas)
    for m, hits in data:
        pm = np.sin((2 * m + 1) * thetas) ** 2
        pm = np.clip(pm, 1e-12, 1 - 1e-12)
        loglik += hits * np.log(pm) + (shots - hits) * np.log(1 - pm)
    a_hat = float(np.sin(thetas[int(np.argmax(loglik))]))
    return {"a_estimate": a_hat, "a_true": a_true, "abs_error": abs(a_hat - a_true)}
