"""Tests for finite Lindbladian open-system steady states (Phase 5B)."""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import unittest
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.open_system import (
    lindbladian_superoperator, solve_open_system, steady_state, evolve,
    relaxation_spectrum,
)

_SM = np.array([[0, 1], [0, 0]], dtype=complex)


class TestOpenSystem(unittest.TestCase):
    def test_amplitude_damping_steady_state_is_ground(self):
        g = 0.7
        res = solve_open_system(np.zeros((2, 2), dtype=complex), [np.sqrt(g) * _SM])
        self.assertTrue(res.is_valid_density_matrix)
        self.assertTrue(np.allclose(res.steady_state, np.array([[1, 0], [0, 0]]),
                                    atol=1e-6))
        self.assertLess(res.residual_norm, 1e-8)

    def test_steady_state_is_valid_density_matrix(self):
        H = np.array([[0, 1], [1, 0]], dtype=complex)
        res = solve_open_system(H, [0.5 * _SM])
        rho = res.steady_state
        self.assertAlmostEqual(float(np.trace(rho).real), 1.0, places=6)
        self.assertTrue(np.allclose(rho, rho.conj().T, atol=1e-6))
        self.assertGreaterEqual(float(np.linalg.eigvalsh(rho)[0].real), -1e-6)

    def test_relaxation_spectrum_nonpositive(self):
        H = np.array([[0, 1], [1, 0]], dtype=complex)
        L = lindbladian_superoperator(H, [0.5 * _SM])
        spec = relaxation_spectrum(L)
        self.assertTrue(np.all(spec.real <= 1e-9))

    def test_long_time_matches_steady(self):
        g = 0.6
        H = np.zeros((2, 2), dtype=complex)
        L = lindbladian_superoperator(H, [np.sqrt(g) * _SM])
        rho_ss = steady_state(L)
        rho_t = evolve(L, np.eye(2) / 2, 60.0)
        self.assertTrue(np.allclose(rho_t, rho_ss, atol=1e-4))


if __name__ == "__main__":
    unittest.main()
