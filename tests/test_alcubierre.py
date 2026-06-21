"""Tests for the Alcubierre warp-metric energy-condition analysis."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.relativity.alcubierre import (
    analyze_warp_bubble,
    energy_density,
    ford_roman_bound,
    shape_function,
    shape_function_derivative,
)


class TestAlcubierre(unittest.TestCase):
    def test_shape_function_interior_exterior(self):
        # f ~ 1 inside the bubble, ~ 0 far outside.
        self.assertAlmostEqual(float(shape_function(0.0, R=1.0, sigma=8.0)), 1.0, places=3)
        self.assertLess(float(shape_function(3.0, R=1.0, sigma=8.0)), 1e-3)

    def test_energy_density_nonpositive_everywhere(self):
        # rho <= 0 on a random cloud of points (the WEC violation is universal).
        rng = np.random.default_rng(0)
        pts = rng.uniform(-3, 3, size=(500, 3))
        for x, y, z in pts:
            self.assertLessEqual(float(energy_density(x, y, z)), 1e-12)

    def test_energy_density_zero_on_axis(self):
        # On the symmetry axis y=z=0 the (y^2+z^2) factor kills rho.
        for x in (-1.0, 0.0, 0.5, 1.0):
            self.assertAlmostEqual(float(energy_density(x, 0.0, 0.0)), 0.0, places=12)

    def test_wec_violated_and_ring_at_wall(self):
        a = analyze_warp_bubble(v_s=1.0, R=1.0, sigma=8.0, n_grid=60)
        self.assertTrue(a.wec_violated)
        self.assertLess(a.rho_min, 0.0)
        # negative energy concentrates near the bubble wall radius R
        self.assertAlmostEqual(a.ring_radius, 1.0, delta=0.25)

    def test_negative_energy_scales_as_velocity_squared(self):
        a1 = analyze_warp_bubble(v_s=1.0, sigma=8.0, n_grid=60)
        a2 = analyze_warp_bubble(v_s=2.0, sigma=8.0, n_grid=60)
        self.assertAlmostEqual(a2.total_negative_energy / a1.total_negative_energy,
                               4.0, places=4)
        self.assertLess(a1.total_negative_energy, 0.0)

    def test_ford_roman_bound_decreasing_in_sampling_time(self):
        # The QI floor magnitude shrinks as the sampling time grows (~ 1/tau^4).
        self.assertGreater(ford_roman_bound(0.1), ford_roman_bound(1.0))
        self.assertAlmostEqual(ford_roman_bound(1.0) / ford_roman_bound(2.0),
                               16.0, places=6)

    def test_certificate_is_hole_free(self):
        a = analyze_warp_bubble(n_grid=40)
        self.assertNotIn("sorry", a.lean4)
        self.assertNotIn("admit", a.lean4.lower())
        self.assertNotIn("Admitted", a.coq)
        self.assertIn("rho_nonpos", a.lean4)
        self.assertIn("rho_nonpos", a.coq)


if __name__ == "__main__":
    unittest.main()
