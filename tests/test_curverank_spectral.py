from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_spectral import (
    gue_spacing_statistic,
    rank_candidates,
    riemann_zero_targets,
    spectral_mismatch,
    truncation_stability,
)


class TestRiemannZeroTargets(unittest.TestCase):
    def test_first_zero(self):
        zeros = riemann_zero_targets(1)
        self.assertAlmostEqual(zeros[0], 14.134725141734693, places=8)

    def test_count(self):
        zeros = riemann_zero_targets(50)
        self.assertEqual(len(zeros), 50)

    def test_full_table(self):
        zeros = riemann_zero_targets(100)
        self.assertEqual(len(zeros), 100)

    def test_monotonic(self):
        zeros = riemann_zero_targets(100)
        for i in range(1, len(zeros)):
            self.assertGreater(zeros[i], zeros[i - 1])

    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            riemann_zero_targets(0)
        with self.assertRaises(ValueError):
            riemann_zero_targets(101)


class TestSpectralMismatch(unittest.TestCase):
    def test_perfect_match(self):
        targets = riemann_zero_targets(5)
        mismatch = spectral_mismatch(targets, targets)
        self.assertAlmostEqual(mismatch, 0.0, places=10)

    def test_shifted_spectrum(self):
        targets = riemann_zero_targets(5)
        shifted = targets + 1.0
        mismatch = spectral_mismatch(shifted, targets)
        self.assertGreater(mismatch, 0.0)

    def test_empty_returns_inf(self):
        targets = riemann_zero_targets(5)
        mismatch = spectral_mismatch(np.array([]), targets)
        self.assertEqual(mismatch, float("inf"))


class TestGUESpacingStatistic(unittest.TestCase):
    def test_known_uniform(self):
        eigs = np.arange(1.0, 11.0)
        stats = gue_spacing_statistic(eigs)
        self.assertAlmostEqual(stats["mean_ratio"], 1.0, places=10)

    def test_too_few_eigenvalues(self):
        stats = gue_spacing_statistic(np.array([1.0]))
        self.assertTrue(np.isnan(stats["mean_ratio"]))

    def test_random_gue_like(self):
        rng = np.random.default_rng(42)
        M = rng.standard_normal((50, 50))
        M = (M + M.T) / 2
        eigs = np.linalg.eigvalsh(M)
        stats = gue_spacing_statistic(eigs)
        self.assertGreater(stats["mean_ratio"], 0.3)
        self.assertLess(stats["mean_ratio"], 0.9)


class TestTruncationStability(unittest.TestCase):
    def test_basic_sweep(self):
        def diagonal_op(n):
            return np.diag(np.arange(1.0, n + 1.0))

        results = truncation_stability(diagonal_op, [5, 10, 15], k=3)
        self.assertEqual(len(results), 3)
        self.assertTrue(np.isnan(results[0]["drift_from_previous"]))
        self.assertAlmostEqual(results[1]["drift_from_previous"], 0.0, places=10)


class TestRankCandidates(unittest.TestCase):
    def test_ranking_order(self):
        candidates = [
            {"family": "test", "n_basis": 5, "operator": np.diag(np.arange(1.0, 6.0))},
            {"family": "test", "n_basis": 10, "operator": np.diag(np.arange(1.0, 11.0))},
        ]
        ranked = rank_candidates(candidates, k=5)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[1]["rank"], 2)
        self.assertLessEqual(ranked[0]["composite_score"], ranked[1]["composite_score"])

    def test_has_required_fields(self):
        candidates = [
            {"family": "xp", "n_basis": 8, "operator": np.eye(8)},
        ]
        ranked = rank_candidates(candidates, k=5)
        for field in ["spectral_mismatch", "gue_mean_ratio", "composite_score", "rank"]:
            self.assertIn(field, ranked[0])


if __name__ == "__main__":
    unittest.main()
