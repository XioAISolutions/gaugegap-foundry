"""Tests for the optional cvxpy-gated SDP lower bound (Phase 5A optional)."""
from __future__ import annotations
import importlib.util, sys, warnings
from pathlib import Path
import unittest
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.dual_vqe import sdp_ground_energy_lower_bound
_HAS_CVXPY = importlib.util.find_spec("cvxpy") is not None


class TestDualVQE(unittest.TestCase):
    def test_gated_without_cvxpy(self):
        if _HAS_CVXPY:
            self.skipTest("cvxpy present")
        with self.assertRaises(RuntimeError):
            sdp_ground_energy_lower_bound(np.diag([1.0, 2.0]))

    @unittest.skipUnless(_HAS_CVXPY, "cvxpy not installed")
    def test_sdp_matches_e0(self):
        H = np.diag([-1.5, 0.3, 2.0]).astype(float)
        lb = sdp_ground_energy_lower_bound(H)
        self.assertLessEqual(lb, -1.5 + 1e-4)
        self.assertAlmostEqual(lb, -1.5, places=3)


if __name__ == "__main__":
    unittest.main()
