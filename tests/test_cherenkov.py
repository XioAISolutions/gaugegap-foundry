"""Tests for Cherenkov radiation (local speed limit & cone geometry)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.cherenkov import (
    analyze_cherenkov,
    cherenkov_threshold,
    cone_angle,
    emits,
    wavefront_cone,
)


class TestCherenkov(unittest.TestCase):
    def test_threshold(self):
        self.assertAlmostEqual(cherenkov_threshold(1.33), 1 / 1.33, places=9)
        self.assertFalse(emits(1.33, 0.5))      # below threshold
        self.assertTrue(emits(1.33, 0.9))       # above threshold

    def test_no_emission_below_threshold(self):
        self.assertIsNone(cone_angle(1.33, 0.5))
        r = analyze_cherenkov(1.33, 0.5)
        self.assertFalse(r.emits)
        self.assertFalse(r.cone_valid)

    def test_cone_formula_recovered_from_simulation(self):
        # cos(theta_c) = 1/(n beta) recovered from the wavefront pile-up
        for n, beta in [(1.33, 0.9), (1.33, 0.99), (1.5, 0.8)]:
            r = analyze_cherenkov(n, beta)
            self.assertAlmostEqual(r.cos_theta_c, 1.0 / (n * beta), places=9)
            self.assertLess(r.recovery_error, 1e-2)
            self.assertTrue(r.cone_valid)

    def test_angle_increases_with_speed(self):
        # faster particle -> wider Cherenkov angle
        a1 = cone_angle(1.33, 0.8)
        a2 = cone_angle(1.33, 0.99)
        self.assertLess(a1, a2)

    def test_recovery_matches_closed_form_directly(self):
        sim = wavefront_cone(1.4, 0.95)
        self.assertAlmostEqual(sim["cos_theta_c_recovered"], 1.0 / (1.4 * 0.95),
                               delta=1e-2)

    def test_certificate_hole_free(self):
        r = analyze_cherenkov(1.33, 0.9)
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("cone_valid", r.lean4)
        self.assertIn("cone_valid", r.coq)


if __name__ == "__main__":
    unittest.main()
