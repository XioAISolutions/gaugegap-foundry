"""Deep correctness audit: known-answer checks across advanced-quantum modules.

A second correctness pass beyond the topological braiding fix. Each test pins a
module's headline behaviour to a textbook-known value or property, so silent
regressions (or stubs masquerading as implementations) are caught.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

BELL = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
CNOT = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)
SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)
ISWAP = np.array([[1, 0, 0, 0], [0, 0, 1j, 0], [0, 1j, 0, 0], [0, 0, 0, 1]], dtype=complex)


# --- quantum_information ----------------------------------------------------

def test_concurrence_bell_and_product():
    from gaugegap.quantum import quantum_information as qi

    rho_bell = np.outer(BELL, BELL.conj())
    c = qi.concurrence(rho_bell)
    c = c.value if hasattr(c, "value") else c
    assert np.isclose(float(c), 1.0, atol=1e-6)              # maximally entangled

    prod = np.zeros(4, dtype=complex); prod[0] = 1.0          # |00>
    c0 = qi.concurrence(np.outer(prod, prod.conj()))
    c0 = c0.value if hasattr(c0, "value") else c0
    assert np.isclose(float(c0), 0.0, atol=1e-6)             # product state


def test_negativity_bell_value():
    from gaugegap.quantum import quantum_information as qi

    res = qi.negativity(np.outer(BELL, BELL.conj()), [0], 2)
    # The plain negativity N = (||rho^{T}||_1 - 1)/2 = 0.5 for a Bell state;
    # the reported value is the logarithmic negativity log2(2N+1) = 1.
    meta = getattr(res, "metadata", {}) or {}
    if "negativity" in meta:
        assert np.isclose(float(meta["negativity"]), 0.5, atol=1e-6)
    assert np.isclose(float(res.value), 1.0, atol=1e-6)


# --- quantum_walks ----------------------------------------------------------

def test_ctqw_conserves_probability():
    from gaugegap.quantum import quantum_walks as qw

    A = np.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], dtype=float)
    r = qw.continuous_time_quantum_walk(A, time=2.3, initial_vertex=0)
    assert np.isclose(float(np.sum(r.probability_distribution)), 1.0, atol=1e-9)


def test_dtqw_is_ballistic_and_conserves_probability():
    from gaugegap.quantum import quantum_walks as qw

    n_steps = 50
    r = qw.discrete_time_quantum_walk_1d(n_steps=n_steps, n_sites=2 * n_steps + 1,
                                         initial_position=n_steps)
    p = r.probability_distribution
    assert np.isclose(float(p.sum()), 1.0, atol=1e-9)
    x = np.arange(len(p))
    mean = float(np.sum(x * p))
    std = float(np.sqrt(np.sum((x - mean) ** 2 * p)))
    # Quantum walk spreads ballistically (std ~ t), far beyond classical
    # diffusion (std ~ sqrt(t)). This distinguishes a real QW from a stub.
    assert std > 3.0 * np.sqrt(n_steps)


# --- advanced_compilation (KAK Makhlin invariants) --------------------------

def test_kak_makhlin_invariants_known_gates():
    from gaugegap.quantum import advanced_compilation as ac

    expected = {
        "CNOT": (CNOT, 0.0, 1.0, True),
        "SWAP": (SWAP, -1.0, -3.0, True),
        "iSWAP": (ISWAP, 0.0, -1.0, True),
        "local": (np.kron(np.array([[0, 1], [1, 0]], dtype=complex), np.eye(2, dtype=complex)),
                  1.0, 3.0, False),
    }
    for U, g1, g2, entangling in expected.values():
        res = ac.kak_decomposition(U)
        inv = res["makhlin_invariants"]
        assert np.isclose(inv["G1"].real, g1, atol=1e-9)
        assert np.isclose(inv["G2"].real, g2, atol=1e-9)
        assert res["is_entangling"] is entangling
