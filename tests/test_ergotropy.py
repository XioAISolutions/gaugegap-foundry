"""Tests for ergotropy / passivity (certified no-free-energy bound)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.ergotropy import (
    analyze_ergotropy,
    ergotropy,
    is_passive,
    mean_energy,
    passive_density_matrix,
    passive_energy,
    thermal_state,
)


def _ladder(n):
    return np.diag(np.arange(n, dtype=float)).astype(complex)


class TestErgotropy(unittest.TestCase):
    def test_ground_state_is_passive(self):
        H = _ladder(4)
        g = np.zeros((4, 4), complex); g[0, 0] = 1.0
        self.assertAlmostEqual(ergotropy(g, H), 0.0, places=12)
        self.assertTrue(is_passive(g, H))

    def test_thermal_state_is_passive(self):
        H = _ladder(5)
        for beta in (0.2, 1.0, 5.0):
            self.assertAlmostEqual(ergotropy(thermal_state(H, beta), H), 0.0, places=9)

    def test_excited_state_max_ergotropy(self):
        H = _ladder(4)
        ex = np.zeros((4, 4), complex); ex[3, 3] = 1.0
        # fully excited: W = <H> - E0 = 3 - 0
        self.assertAlmostEqual(ergotropy(ex, H), 3.0, places=9)

    def test_no_perpetual_motion_second_cycle_zero(self):
        H = _ladder(4)
        pops = np.array([0.1, 0.2, 0.3, 0.4])
        rho = np.diag(pops).astype(complex)
        r = analyze_ergotropy(rho, H)
        self.assertGreater(r.ergotropy, 0.0)
        self.assertLess(r.second_cycle_ergotropy, 1e-9)

    def test_ergotropy_bracket_valid(self):
        H = _ladder(4)
        rng = np.random.default_rng(1)
        for _ in range(20):
            p = rng.random(4); p /= p.sum()
            rho = np.diag(p).astype(complex)
            r = analyze_ergotropy(rho, H)
            self.assertGreaterEqual(r.ergotropy, -1e-9)
            self.assertLessEqual(r.ergotropy, r.work_bound + 1e-9)

    def test_passive_energy_is_minimum_over_unitaries(self):
        H = _ladder(4)
        p = np.array([0.1, 0.2, 0.3, 0.4])
        rho = np.diag(p).astype(complex)
        pe = passive_energy(rho, H)
        rng = np.random.default_rng(2)
        for _ in range(500):
            A = rng.standard_normal((4, 4)) + 1j * rng.standard_normal((4, 4))
            Q, _ = np.linalg.qr(A)
            e = float(np.real(np.trace(Q @ rho @ Q.conj().T @ H)))
            self.assertGreaterEqual(e, pe - 1e-9)

    def test_passive_state_same_spectrum(self):
        H = _ladder(4)
        p = np.array([0.1, 0.2, 0.3, 0.4])
        rho = np.diag(p).astype(complex)
        rp = passive_density_matrix(rho, H)
        np.testing.assert_allclose(np.sort(np.linalg.eigvalsh(rp)),
                                   np.sort(p), atol=1e-9)
        self.assertAlmostEqual(mean_energy(rp, H), passive_energy(rho, H), places=9)

    def test_certificate_hole_free(self):
        H = _ladder(4)
        rho = np.diag([0.1, 0.2, 0.3, 0.4]).astype(complex)
        r = analyze_ergotropy(rho, H)
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("no_free_energy", r.lean4)
        self.assertIn("no_free_energy", r.coq)


if __name__ == "__main__":
    unittest.main()
