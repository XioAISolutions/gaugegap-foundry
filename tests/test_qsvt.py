"""Tests for the certified QSVT eigenvalue transform (Phase 4)."""
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

from gaugegap.quantum.qsvt import qsvt_eigenvalue_transform
from gaugegap.curverank_registry import get_operator


def _random_hermitian(n, seed):
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n))
    return (A + A.T) / 2


class TestQSVT(unittest.TestCase):
    def test_square_transform_certified(self):
        H = get_operator("berry_keating_xp").build(8)
        r = qsvt_eigenvalue_transform(H, [0.0, 0.0, 1.0])   # P(x)=x^2
        self.assertTrue(r.all_inside)
        self.assertLess(r.max_residual, 1e-9)

    def test_cubic_transform_certified(self):
        H = get_operator("berry_keating_xp").build(8)
        r = qsvt_eigenvalue_transform(H, [0.0, 1.5, 0.0, -0.5])
        self.assertTrue(r.all_inside)
        self.assertLess(r.max_residual, 1e-9)

    def test_matches_polynomial_of_eigenvalues(self):
        # transformed eigenvalues == P(rescaled classical eigenvalues)
        H = _random_hermitian(6, seed=2)
        coeffs = [0.2, -0.5, 0.0, 1.0]
        r = qsvt_eigenvalue_transform(H, coeffs)
        self.assertTrue(r.all_inside)
        self.assertEqual(len(r.transformed_eigenvalues), 6)
        self.assertLess(r.max_residual, 1e-9)

    def test_identity_polynomial(self):
        # P(x)=x maps rescaled eigenvalues back; still certified
        H = _random_hermitian(5, seed=3)
        r = qsvt_eigenvalue_transform(H, [0.0, 1.0])
        self.assertTrue(r.all_inside)

    def test_certified_enclosures_bracket_transformed(self):
        H = get_operator("berry_keating_xp").build(8)
        r = qsvt_eigenvalue_transform(H, [0.0, 0.0, 1.0])
        for t in r.transformed_eigenvalues:
            self.assertTrue(any(lo - 1e-9 <= t <= hi + 1e-9
                                for (lo, hi) in r.certified_enclosures))


if __name__ == "__main__":
    unittest.main()
