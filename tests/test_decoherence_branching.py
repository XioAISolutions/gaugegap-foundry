"""Tests for the decoherence/branching (einselection) model."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.decoherence_branching import (
    analyze_branching,
    born_weights,
    branch_density_matrix,
    coherence_l1,
    decoherence_sweep,
    effective_branches,
    purity,
    verify_reduced_state,
)


class TestDecoherenceBranching(unittest.TestCase):
    def test_analytic_reduced_state_matches_statevector(self):
        # The analytic reduced state IS the partial trace of the literal statevector.
        for n_env in (1, 2, 4, 6):
            self.assertLess(verify_reduced_state(n_env=n_env, theta=0.7), 1e-12)

    def test_born_weights_normalized_and_uniform(self):
        rho = branch_density_matrix(4, n_env=5, overlap=0.6)
        w = born_weights(rho)
        self.assertAlmostEqual(sum(w), 1.0, places=12)
        for p in w:
            self.assertAlmostEqual(p, 0.25, places=12)

    def test_coherence_decays_with_environment(self):
        ns, coh, _ = decoherence_sweep(d=3, overlap=0.6, n_env_max=20)
        # strictly decreasing and -> 0
        for a, b in zip(coh, coh[1:]):
            self.assertGreaterEqual(a + 1e-15, b)
        self.assertLess(coh[-1], 1e-3)

    def test_effective_branches_run_from_one_to_d(self):
        for d in (2, 3, 5):
            rho0 = branch_density_matrix(d, n_env=0, overlap=0.6)
            self.assertAlmostEqual(effective_branches(rho0), 1.0, places=9)  # pure
            rho_inf = branch_density_matrix(d, n_env=200, overlap=0.6)
            self.assertAlmostEqual(effective_branches(rho_inf), float(d), places=6)

    def test_branch_count_bracketed(self):
        for d in (2, 3, 4, 6):
            for n in (0, 1, 5, 12):
                rho = branch_density_matrix(d, n_env=n, overlap=0.6)
                ne = effective_branches(rho)
                self.assertGreaterEqual(ne, 1.0 - 1e-9)
                self.assertLessEqual(ne, d + 1e-9)

    def test_purity_bounds(self):
        rho = branch_density_matrix(3, n_env=50, overlap=0.6)
        self.assertAlmostEqual(purity(rho), 1.0 / 3.0, places=6)  # maximally mixed
        rho_pure = branch_density_matrix(3, n_env=0, overlap=0.6)
        self.assertAlmostEqual(purity(rho_pure), 1.0, places=9)

    def test_certificate_is_hole_free(self):
        r = analyze_branching(d=3, n_env=10, overlap=0.6)
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("branch_bracket", r.lean4)
        self.assertIn("branch_bracket", r.coq)
        self.assertTrue(r.branch_bracket_valid)

    def test_overlap_one_no_decoherence(self):
        # overlap=1 (environment records nothing) => stays a coherent single state.
        rho = branch_density_matrix(3, n_env=20, overlap=1.0)
        self.assertAlmostEqual(effective_branches(rho), 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
