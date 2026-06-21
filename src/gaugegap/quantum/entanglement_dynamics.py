"""Entanglement-formation dynamics: how entanglement BUILDS UP over time.

Inspired by the attosecond-entanglement result (entanglement forms over a finite
time during an interaction, not instantaneously), this evolves an initially
unentangled finite state under an interaction Hamiltonian and measures the
entanglement-build-up timescale via the entanglement entropy S(t).

IMPORTANT / CLAIM BOUNDARY: this is a *finite model* demonstration of entanglement
formation dynamics. It is NOT a reproduction of the TU Wien helium photoionization
experiment, nor a claim about the specific ~232 attosecond figure or any real atom.
The optional physical-time conversion is illustrative only (t = t_model * hbar / E
for a user-supplied energy scale E). Exact statevector evolution, dependency-light.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from gaugegap.quantum.quantum_information import entanglement_entropy

# hbar in eV*attoseconds (hbar = 0.6582119569 eV*fs = 658.2119569 eV*as)
_HBAR_EV_AS = 658.2119569


def evolve_state(H: np.ndarray, psi0: np.ndarray, t: float) -> np.ndarray:
    """exp(-i H t) psi0 via the eigendecomposition (no scipy dependency)."""
    H = (np.asarray(H) + np.asarray(H).conj().T) / 2.0
    evals, evecs = np.linalg.eigh(H)
    coeffs = evecs.conj().T @ np.asarray(psi0, dtype=complex)
    return evecs @ (np.exp(-1j * evals * t) * coeffs)


def entanglement_curve(H: np.ndarray, psi0: np.ndarray, times: Sequence[float],
                       *, keep_qubits: Optional[List[int]] = None) -> List[float]:
    """Entanglement entropy S(t) of the reduced state across a bipartition, for an
    exact-evolved state at each time in ``times``."""
    psi0 = np.asarray(psi0, dtype=complex)
    n = psi0.shape[0]
    n_qubits = int(round(np.log2(n)))
    if (1 << n_qubits) != n:
        raise ValueError("state dimension must be a power of two")
    if keep_qubits is None:
        keep_qubits = list(range(n_qubits // 2))
    H = (np.asarray(H) + np.asarray(H).conj().T) / 2.0
    evals, evecs = np.linalg.eigh(H)
    c0 = evecs.conj().T @ psi0
    out = []
    for t in times:
        psi = evecs @ (np.exp(-1j * evals * t) * c0)
        psi /= np.linalg.norm(psi)
        out.append(float(entanglement_entropy(psi, subsystem_qubits=keep_qubits,
                                              total_qubits=n_qubits).value))
    return out


@dataclass
class BuildupResult:
    times: List[float]
    entropies: List[float]
    s_asymptote: float            # max entanglement reached
    buildup_time: float           # time to reach `fraction` of the asymptote
    fraction: float
    time_unit: str                # "model" or "attoseconds"
    energy_scale_eV: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "kind": "entanglement_buildup",
            "s_asymptote": self.s_asymptote,
            "buildup_time": self.buildup_time,
            "fraction": self.fraction,
            "time_unit": self.time_unit,
            "energy_scale_eV": self.energy_scale_eV,
            "n_samples": len(self.times),
            "claim_boundary": ("finite-model entanglement-formation dynamics inspired "
                               "by attosecond-entanglement work; NOT a reproduction of "
                               "the helium experiment or the 232 as figure; physical "
                               "time is illustrative; not a continuum/Millennium claim"),
        }


def buildup_time(times: Sequence[float], entropies: Sequence[float],
                 fraction: float = 0.9) -> tuple:
    """First time S reaches ``fraction`` of its max (the build-up timescale)."""
    t = np.asarray(times, dtype=float)
    s = np.asarray(entropies, dtype=float)
    s_max = float(s.max()) if s.size else 0.0
    if s_max <= 1e-12:
        return 0.0, s_max
    target = fraction * s_max
    idx = np.argmax(s >= target)           # first crossing
    if s[idx] < target:                     # never reached
        return float(t[-1]), s_max
    if idx == 0:
        return float(t[0]), s_max
    # linear interpolation between idx-1 and idx
    t0, t1, s0, s1 = t[idx - 1], t[idx], s[idx - 1], s[idx]
    tb = t0 + (target - s0) * (t1 - t0) / (s1 - s0) if s1 != s0 else float(t1)
    return float(tb), s_max


def simulate_buildup(H: np.ndarray, psi0: np.ndarray, *, t_max: float = np.pi,
                     n_samples: int = 200, fraction: float = 0.9,
                     energy_scale_eV: Optional[float] = None) -> BuildupResult:
    """Evolve ``psi0`` under ``H`` and measure the entanglement-build-up time.

    If ``energy_scale_eV`` is given, the model time is converted to attoseconds via
    ``t_as = t_model * hbar / E`` (illustrative only)."""
    times = list(np.linspace(0.0, t_max, n_samples))
    ent = entanglement_curve(H, psi0, times)
    tb, s_max = buildup_time(times, ent, fraction)
    unit = "model"
    if energy_scale_eV:
        scale = _HBAR_EV_AS / energy_scale_eV
        times = [t * scale for t in times]
        tb *= scale
        unit = "attoseconds"
    return BuildupResult(times=times, entropies=ent, s_asymptote=s_max,
                         buildup_time=tb, fraction=fraction, time_unit=unit,
                         energy_scale_eV=energy_scale_eV)


def two_qubit_exchange_model(coupling: float = 1.0, detuning: float = 0.0):
    """A minimal 'one excitation affects the partner' model: XX+YY exchange between
    two qubits (excitation hopping) + optional detuning, with the excitation
    initially localized on qubit 0 (|10>) — entanglement builds from zero."""
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    I = np.eye(2, dtype=complex)
    H = coupling * (np.kron(X, X) + np.kron(Y, Y)) + detuning * np.kron(Z, I)
    psi0 = np.array([0, 0, 1, 0], dtype=complex)   # |10>
    return H, psi0
