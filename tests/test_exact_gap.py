from __future__ import annotations

import unittest

import numpy as np

from gaugegap.models.z2_plaquette import hamiltonian_dense
from gaugegap.solvers.exact_gap import exact_gap


class ExactGapTests(unittest.TestCase):
    def test_gap_nonnegative(self) -> None:
        result = exact_gap(hamiltonian_dense())
        self.assertGreaterEqual(result.gap, 0.0)
        self.assertTrue(np.isfinite(result.gap))
        self.assertLess(result.residual_norm, 1e-8)
        self.assertIn(result.status, {"finite_system_verified", "warning_high_residual"})

    def test_rejects_non_hermitian_matrix(self) -> None:
        with self.assertRaises(ValueError):
            exact_gap(np.array([[0.0, 1.0], [0.0, 0.0]]))

    def test_rejects_non_finite_matrix(self) -> None:
        with self.assertRaises(ValueError):
            exact_gap(np.array([[0.0, np.nan], [np.nan, 1.0]]))

    def test_rejects_bad_degeneracy_tolerance(self) -> None:
        with self.assertRaises(ValueError):
            exact_gap(np.eye(2), degeneracy_tol=-1.0)


if __name__ == "__main__":
    unittest.main()
