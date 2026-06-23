"""Tests for the Lieb-Robinson light cone (many-body speed limit)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.lieb_robinson import (
    analyze_lieb_robinson,
    chain_hamiltonian,
    evolve_distribution,
    front_position,
    group_velocity,
    lieb_robinson_velocity,
)


class TestLiebRobinson(unittest.TestCase):
    def test_velocities(self):
        self.assertAlmostEqual(group_velocity(1.0), 2.0, places=9)
        self.assertAlmostEqual(lieb_robinson_velocity(1.0), np.e, places=9)
        # the rigorous cone speed exceeds the group velocity
        self.assertGreater(lieb_robinson_velocity(1.5), group_velocity(1.5))

    def test_distribution_normalized(self):
        H = chain_hamiltonian(21, 1.0)
        d = evolve_distribution(H, 10, 2.0)
        self.assertAlmostEqual(float(d.sum()), 1.0, places=9)

    def test_front_respects_linear_cone(self):
        for J in (1.0, 2.0):
            r = analyze_lieb_robinson(n_sites=41, J=J)
            self.assertTrue(r.respects_cone)
            self.assertLessEqual(r.front_velocity, r.v_lr + 1e-6)

    def test_front_grows_with_time(self):
        r = analyze_lieb_robinson(n_sites=41, J=1.0)
        self.assertLess(r.fronts[0], r.fronts[-1])
        self.assertGreater(r.front_velocity, 1.0)   # ballistic, ~2J

    def test_crosscheck_against_quantum_walks(self):
        # activates the dormant quantum_walks CTQW; agreement to ~machine precision
        r = analyze_lieb_robinson(n_sites=31, J=1.0)
        if r.crosscheck_error is not None:        # SciPy present
            self.assertLess(r.crosscheck_error, 1e-9)

    def test_certificate_hole_free(self):
        r = analyze_lieb_robinson(n_sites=21, J=1.0)
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("light_cone", r.lean4)
        self.assertIn("light_cone", r.coq)


if __name__ == "__main__":
    unittest.main()
