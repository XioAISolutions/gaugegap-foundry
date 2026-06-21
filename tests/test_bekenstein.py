"""Tests for the Bekenstein bound (info <-> energy <-> geometry keystone)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.relativity.bekenstein import (
    analyze_bekenstein,
    bekenstein_bound,
    minimal_radius,
)


class TestBekenstein(unittest.TestCase):
    def setUp(self):
        self.H = np.diag([0.0, 1.0, 2.0, 3.0]).astype(complex)
        self.rho = np.diag([0.4, 0.3, 0.2, 0.1]).astype(complex)

    def test_bound_formula(self):
        self.assertAlmostEqual(bekenstein_bound(2.0, 3.0), 2 * np.pi * 2.0 * 3.0, places=9)

    def test_minimal_radius_consistency(self):
        # at R = R_min the bound is saturated: S == 2 pi R_min E
        S, E = 1.5, 0.7
        r = minimal_radius(S, E)
        self.assertAlmostEqual(bekenstein_bound(r, E), S, places=9)

    def test_respected_for_large_region(self):
        b = analyze_bekenstein(self.rho, self.H, radius=5.0)
        self.assertTrue(b.respects_bound)
        self.assertLessEqual(b.entropy_nats, b.bound + 1e-9)

    def test_violated_below_minimal_radius(self):
        b = analyze_bekenstein(self.rho, self.H, radius=1.0)
        rmin = b.minimal_radius
        below = analyze_bekenstein(self.rho, self.H, radius=rmin * 0.5)
        self.assertFalse(below.respects_bound)

    def test_energy_above_ground(self):
        b = analyze_bekenstein(self.rho, self.H, radius=2.0)
        expected_E = float(np.real(np.trace(self.rho @ self.H))) - 0.0
        self.assertAlmostEqual(b.energy, expected_E, places=9)

    def test_certificate_hole_free(self):
        b = analyze_bekenstein(self.rho, self.H, radius=2.0)
        self.assertNotIn("sorry", b.lean4)
        self.assertNotIn("admit", b.lean4.lower())
        self.assertNotIn("Admitted", b.coq)
        self.assertIn("bekenstein", b.lean4)
        self.assertIn("bekenstein", b.coq)


if __name__ == "__main__":
    unittest.main()
