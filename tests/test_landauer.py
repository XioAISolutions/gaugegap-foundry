"""Tests for Landauer's principle (info <-> energy keystone)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.landauer import (
    analyze_landauer,
    erasure_cost,
    landauer_bit,
    landauer_bound,
)

_LN2 = float(np.log(2.0))


class TestLandauer(unittest.TestCase):
    def test_mixed_qubit_costs_one_bit(self):
        half = np.eye(2, dtype=complex) / 2
        r = analyze_landauer(half, T=1.0)
        self.assertAlmostEqual(r.entropy_nats, _LN2, places=9)
        self.assertAlmostEqual(r.erasure_cost, r.bit_floor, places=9)
        self.assertAlmostEqual(r.bits_erased, 1.0, places=9)
        self.assertTrue(r.above_bit_floor)

    def test_pure_state_no_cost(self):
        pure = np.zeros((2, 2), complex); pure[0, 0] = 1.0
        self.assertAlmostEqual(erasure_cost(pure, T=1.0), 0.0, places=12)

    def test_cost_scales_with_temperature(self):
        half = np.eye(2, dtype=complex) / 2
        c1 = erasure_cost(half, T=1.0)
        c2 = erasure_cost(half, T=2.0)
        self.assertAlmostEqual(c2 / c1, 2.0, places=9)

    def test_landauer_bit_value(self):
        self.assertAlmostEqual(landauer_bit(T=1.0), _LN2, places=12)
        self.assertAlmostEqual(landauer_bound(_LN2, T=3.0), 3.0 * _LN2, places=12)

    def test_si_cost_reported(self):
        half = np.eye(2, dtype=complex) / 2
        r = analyze_landauer(half, T=1.0, temperature_K=300.0)
        # k_B T ln2 at 300 K ~ 0.0179 eV
        self.assertAlmostEqual(r.erasure_cost_eV, 8.617333262e-5 * 300.0 * _LN2, places=9)

    def test_certificate_hole_free(self):
        r = analyze_landauer(np.eye(2, dtype=complex) / 2, T=1.0)
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("landauer_floor", r.lean4)
        self.assertIn("landauer_floor", r.coq)


if __name__ == "__main__":
    unittest.main()
