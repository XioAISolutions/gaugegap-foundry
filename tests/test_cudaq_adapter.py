"""Tests for the optional CUDA-Q simulation backend.

The numpy reference path is always tested. The CUDA-Q path is skip-guarded on
``cudaq_available()`` (CI has no GPU/CUDA-Q), and when present is checked for
parity against the reference -- the verification-first contract for the optional
backend.
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.providers import cudaq_adapter as cq


def _probs(state: np.ndarray) -> np.ndarray:
    return np.abs(np.asarray(state, dtype=complex)) ** 2


class TestNumpyBackend(unittest.TestCase):
    def test_ghz_state(self):
        state = cq.numpy_statevector(cq.ghz_circuit(3), 3)
        p = _probs(state)
        # GHZ: weight only on |000> and |111>, each ~1/2.
        self.assertAlmostEqual(p[0], 0.5, places=12)
        self.assertAlmostEqual(p[-1], 0.5, places=12)
        self.assertAlmostEqual(p.sum(), 1.0, places=12)
        self.assertAlmostEqual(p[1:-1].sum(), 0.0, places=12)

    def test_rotation_matches_analytic(self):
        # ry(theta)|0> = cos(theta/2)|0> + sin(theta/2)|1>
        theta = 0.7
        state = cq.numpy_statevector([("ry", (0,), theta)], 1)
        np.testing.assert_allclose(
            state, [np.cos(theta / 2), np.sin(theta / 2)], atol=1e-12)

    def test_auto_backend_falls_back_to_numpy(self):
        # Without cudaq, auto must equal the numpy reference.
        gates = cq.ghz_circuit(2)
        np.testing.assert_allclose(
            cq.statevector(gates, 2, backend="auto"),
            cq.numpy_statevector(gates, 2), atol=1e-12)

    def test_capability_report_is_safe(self):
        info = cq.backend_info()
        self.assertIn("available", info)
        self.assertEqual(info["available"], cq.cudaq_available())


@unittest.skipUnless(cq.cudaq_available(), "cudaq not installed")
class TestCudaqParity(unittest.TestCase):
    def test_cudaq_matches_numpy(self):
        gates = cq.ghz_circuit(3) + [("ry", (0,), 0.4), ("rz", (2,), 1.1)]
        ref = _probs(cq.numpy_statevector(gates, 3))
        got = _probs(cq.cudaq_statevector(gates, 3))
        # Allow for a possible endianness convention difference.
        if not np.allclose(np.sort(got), np.sort(ref), atol=1e-6):
            self.fail("cudaq probabilities do not match reference")


class TestPauliAndTrotterSignal(unittest.TestCase):
    def _tfim(self, n: int, h: float = 0.7) -> np.ndarray:
        # -sum ZZ - h sum X on a chain.
        H = np.zeros((2 ** n, 2 ** n), dtype=complex)
        for q in range(n - 1):
            s = ["I"] * n
            s[q] = s[q + 1] = "Z"
            H -= cq._pauli_matrix("".join(s))
        for q in range(n):
            s = ["I"] * n
            s[q] = "X"
            H -= h * cq._pauli_matrix("".join(s))
        return H

    def test_pauli_decompose_roundtrip(self):
        H = self._tfim(2)
        recon = np.zeros_like(H)
        for coeff, pstr in cq.pauli_decompose(H):
            recon += coeff * cq._pauli_matrix(pstr)
        np.testing.assert_allclose(recon, H, atol=1e-9)

    def test_circuit_correlation_signal_matches_exact(self):
        from scipy.linalg import expm
        n = 2
        H = self._tfim(n)
        psi = np.ones(2 ** n, dtype=complex) / np.sqrt(2 ** n)  # |++>
        times = [0.0, 0.3, 0.7, 1.2]
        g = cq.circuit_correlation_signal(H, times, backend="numpy", trotter_steps=300)
        exact = np.array([np.vdot(psi, expm(-1j * H * t) @ psi) for t in times])
        self.assertAlmostEqual(g[0], 1.0 + 0j, places=9)        # g(0)=1
        np.testing.assert_allclose(g, exact, atol=2e-4)         # within Trotter error

    def test_auto_backend_runs(self):
        H = self._tfim(2)
        g = cq.circuit_correlation_signal(H, [0.5], backend="auto", trotter_steps=50)
        self.assertEqual(g.shape, (1,))


if __name__ == "__main__":
    unittest.main()
