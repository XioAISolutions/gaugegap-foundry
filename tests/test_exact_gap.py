from __future__ import annotations

import unittest

from gaugegap.models.z2_plaquette import hamiltonian_dense
from gaugegap.solvers.exact_gap import exact_gap


class ExactGapTests(unittest.TestCase):
    def test_gap_nonnegative(self) -> None:
        result = exact_gap(hamiltonian_dense())
        self.assertGreaterEqual(result.gap, 0.0)
        self.assertLess(result.residual_norm, 1e-8)
        self.assertIn(result.status, {"finite_system_verified", "warning_high_residual"})


if __name__ == "__main__":
    unittest.main()
