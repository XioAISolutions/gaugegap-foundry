"""Tests for quantum signal extraction (exact/statevector mode, deterministic)."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import berry_keating_xp
from gaugegap.curverank_certified import certified_xp_spectrum
from gaugegap import curverank_signal as cs


def _random_state(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim) + 1j * rng.standard_normal(dim)
    return v / np.linalg.norm(v)


class TestPrimitives(unittest.TestCase):
    def test_hadamard_test_exact_matches_inner_product(self):
        psi = _random_state(4, 1)
        U = np.diag([1, 1j, -1, -1j]).astype(complex)
        self.assertAlmostEqual(cs.hadamard_test(psi, U), complex(np.vdot(psi, U @ psi)))

    def test_correlation_signal_is_sum_of_exponentials(self):
        H = berry_keating_xp(6)
        psi = _random_state(6, 2)
        w, V = np.linalg.eigh(H)
        wt = np.abs(V.conj().T @ psi) ** 2
        times = np.linspace(0, 1.0, 7)
        g = cs.correlation_signal(H, psi, times)
        manual = np.array([np.sum(wt * np.exp(-1j * w * t)) for t in times])
        np.testing.assert_allclose(g, manual, atol=1e-12)
        # g(0) = <psi|psi> = 1
        self.assertAlmostEqual(g[0], 1.0 + 0j, places=12)

    def test_hadamard_test_shots_mode_is_close(self):
        psi = _random_state(4, 3)
        U = np.diag(np.exp(1j * np.array([0.1, -0.4, 0.7, -0.2]))).astype(complex)
        val = cs.hadamard_test(psi, U, shots=20000, rng=np.random.default_rng(0))
        self.assertLess(abs(val - np.vdot(psi, U @ psi)), 0.05)


class TestSpectralEstimation(unittest.TestCase):
    def test_prony_and_esprit_recover_eigenvalues(self):
        H = berry_keating_xp(8)
        true = np.sort(np.linalg.eigvalsh(H))
        psi = _random_state(8, 4)
        for method in ("prony", "esprit"):
            r = cs.extract_eigenvalues(H, psi, method=method,
                                       rng=np.random.default_rng(5))
            est = np.sort(r.eigenvalues)
            max_err = max(min(abs(t - e) for e in est) for t in true)
            self.assertLess(max_err, 1e-6, f"{method} max match err {max_err}")

    def test_extracted_eigenvalues_lie_in_certified_enclosures(self):
        H = berry_keating_xp(8)
        psi = _random_state(8, 6)
        r = cs.extract_eigenvalues(H, psi, method="esprit",
                                   rng=np.random.default_rng(7))
        report = cs.validate_against_certified(r.eigenvalues, certified_xp_spectrum(8))
        self.assertTrue(all(x["in_certified_enclosure"] for x in report))

    def test_prony_needs_enough_samples(self):
        with self.assertRaises(ValueError):
            cs.prony(np.ones(3, dtype=complex), dt=0.1, order=4)


class TestClassicalShadows(unittest.TestCase):
    def test_bell_state_correlators(self):
        bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        sh = cs.classical_shadows(bell, 2, 6000, seed=11)
        self.assertAlmostEqual(cs.shadow_expectation(sh, "XX"), 1.0, delta=0.15)
        self.assertAlmostEqual(cs.shadow_expectation(sh, "ZZ"), 1.0, delta=0.15)
        self.assertAlmostEqual(cs.shadow_expectation(sh, "ZI"), 0.0, delta=0.15)

    def test_product_state_single_qubit(self):
        # |0>|+>  => <ZI>=+1, <IX>=+1
        plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
        state = np.kron(np.array([1, 0], dtype=complex), plus)
        sh = cs.classical_shadows(state, 2, 6000, seed=12)
        self.assertAlmostEqual(cs.shadow_expectation(sh, "ZI"), 1.0, delta=0.15)
        self.assertAlmostEqual(cs.shadow_expectation(sh, "IX"), 1.0, delta=0.15)


class TestAmplitudeEstimation(unittest.TestCase):
    def test_recovers_marked_amplitude(self):
        psi = np.array([np.sqrt(0.3)] + [np.sqrt(0.7 / 3)] * 3, dtype=complex)
        out = cs.amplitude_estimation(psi, marked=[0], shots=1024, seed=13)
        self.assertAlmostEqual(out["a_true"], np.sqrt(0.3), places=12)
        self.assertLess(out["abs_error"], 0.03)


if __name__ == "__main__":
    unittest.main()
