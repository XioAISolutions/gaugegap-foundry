"""Tests for certified classical shadows (Phase 2)."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.quantum.certified_shadows import (
    certified_shadow_estimate, median_of_means,
)

_Z = np.diag([1, -1]).astype(complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_I = np.eye(2, dtype=complex)
_BELL = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)


class TestMedianOfMeans(unittest.TestCase):
    def test_basic(self):
        self.assertAlmostEqual(median_of_means([2.0, 2.0, 2.0, 2.0], 2), 2.0)

    def test_robust_to_outlier(self):
        # median-of-means is far less swayed by a single huge outlier than the mean
        vals = [1.0, 1.0, 1.0, 1.0, 1.0, 1000.0]
        self.assertLess(median_of_means(vals, 3), 100.0)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            median_of_means([], 3)


class TestCertifiedShadows(unittest.TestCase):
    def test_ci_covers_exact_bell(self):
        obs = {"Z0Z1": np.kron(_Z, _Z), "X0X1": np.kron(_X, _X),
               "Z0": np.kron(_Z, _I)}
        res = certified_shadow_estimate(_BELL, obs, n_snapshots=800,
                                        n_batches=16, seed=7)
        for name, e in res.items():
            self.assertTrue(e.covered, msg=f"{name}: CI {e.ci_low,e.ci_high} "
                                            f"misses exact {e.exact}")
            self.assertLessEqual(e.ci_low, e.ci_high)

    def test_single_qubit_z_on_zero(self):
        psi = np.array([1, 0], dtype=complex)   # |0>, <Z> = +1
        res = certified_shadow_estimate(psi, {"Z": _Z}, n_snapshots=600,
                                        n_batches=12, seed=3)
        self.assertAlmostEqual(res["Z"].exact, 1.0, places=9)
        self.assertTrue(res["Z"].covered)

    def test_deterministic(self):
        obs = {"Z0Z1": np.kron(_Z, _Z)}
        a = certified_shadow_estimate(_BELL, obs, n_snapshots=400, n_batches=8, seed=1)
        b = certified_shadow_estimate(_BELL, obs, n_snapshots=400, n_batches=8, seed=1)
        self.assertEqual(a["Z0Z1"].estimate, b["Z0Z1"].estimate)
        self.assertEqual(a["Z0Z1"].ci_low, b["Z0Z1"].ci_low)

    def test_non_power_of_two_rejected(self):
        with self.assertRaises(ValueError):
            certified_shadow_estimate(np.ones(3) / np.sqrt(3), {"O": np.eye(3)})


if __name__ == "__main__":
    unittest.main()
