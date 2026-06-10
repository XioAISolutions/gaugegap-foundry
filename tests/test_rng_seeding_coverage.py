"""Seed-coverage regression tests for the remaining stochastic call sites (A6).

These were ported off the global numpy.random state to local seeded generators:
optimal_control.grape_optimization / crab_optimization,
tensor_network_quantum_hybrid.hybrid_vqe, and
adiabatic_quantum.gauge_theory_adiabatic_preparation. Each must be reproducible
under a fixed seed and must not touch the global RNG.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _global_untouched(call):
    """Run `call` and assert it leaves the global numpy RNG stream unchanged."""
    np.random.seed(20240101)
    sentinel = np.random.random()
    np.random.seed(20240101)
    call()
    return np.random.random() == sentinel


def test_grape_reproducible_and_isolated():
    from gaugegap.quantum import optimal_control as oc

    Hd = np.diag([1.0, -1.0])
    Hc = [np.array([[0.0, 1.0], [1.0, 0.0]])]
    p0 = np.array([1.0, 0.0], dtype=complex)
    p1 = np.array([0.0, 1.0], dtype=complex)
    kw = dict(T=1.0, n_steps=8, max_iterations=3, seed=11)
    r1 = oc.grape_optimization(Hd, Hc, p0, p1, **kw)
    r2 = oc.grape_optimization(Hd, Hc, p0, p1, **kw)
    assert r1.final_fidelity == r2.final_fidelity
    assert _global_untouched(lambda: oc.grape_optimization(Hd, Hc, p0, p1, **kw))


def test_gauge_theory_adiabatic_prep_reproducible_and_isolated():
    from gaugegap.quantum import adiabatic_quantum as aq

    a = aq.gauge_theory_adiabatic_preparation(2, seed=3)
    b = aq.gauge_theory_adiabatic_preparation(2, seed=3)
    assert a["ground_state_fidelity"] == b["ground_state_fidelity"]
    assert _global_untouched(lambda: aq.gauge_theory_adiabatic_preparation(2, seed=3))


def test_hybrid_vqe_reproducible_and_isolated():
    from gaugegap.quantum import tensor_network_quantum_hybrid as tn

    H = np.diag([1.0, -1.0, 0.5, -0.5])
    mps = [np.ones((1, 2, 1)), np.ones((1, 2, 1))]
    kw = dict(n_quantum_layers=1, n_classical_sweeps=1, seed=4)
    r1 = tn.hybrid_vqe(H, mps, **kw)
    r2 = tn.hybrid_vqe(H, mps, **kw)
    assert r1.energy == r2.energy
    assert _global_untouched(lambda: tn.hybrid_vqe(H, mps, **kw))


def test_no_global_numpy_random_in_quantum_sources():
    """Static guard: no module should call the global numpy.random.* helpers."""
    import re

    pat = re.compile(r"np\.random\.(randn|rand|choice|normal|uniform|standard_normal|seed|randint|permutation|shuffle)\(")
    offenders = []
    for path in (ROOT / "src" / "gaugegap").rglob("*.py"):
        if path.name == "seeding.py":
            continue
        if pat.search(path.read_text()):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"global numpy.random usage remains: {offenders}"
