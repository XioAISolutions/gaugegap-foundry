"""Tests for repeated-seed runs and confidence intervals (A6)."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.repeated_runs import confidence_interval, repeated_run


class TestConfidenceInterval(unittest.TestCase):
    def test_basic_ci(self):
        s = confidence_interval([1.0, 1.0, 1.0, 1.0], level=0.95)
        self.assertEqual(s.mean, 1.0)
        self.assertEqual(s.std, 0.0)
        self.assertEqual(s.ci_low, 1.0)
        self.assertEqual(s.ci_high, 1.0)

    def test_ci_brackets_mean_and_widens_with_spread(self):
        tight = confidence_interval([0.99, 1.0, 1.01], level=0.95)
        wide = confidence_interval([0.5, 1.0, 1.5], level=0.95)
        self.assertAlmostEqual(tight.mean, 1.0, places=6)
        self.assertAlmostEqual(wide.mean, 1.0, places=6)
        self.assertLess(tight.ci_halfwidth, wide.ci_halfwidth)
        # CI brackets the mean.
        self.assertLessEqual(tight.ci_low, tight.mean)
        self.assertLessEqual(tight.mean, tight.ci_high)

    def test_requires_two_samples(self):
        with self.assertRaises(ValueError):
            confidence_interval([1.0])

    def test_unknown_level_rejected(self):
        with self.assertRaises(ValueError):
            confidence_interval([1.0, 2.0], level=0.5)


class TestRepeatedRun(unittest.TestCase):
    def test_repeated_run_is_reproducible(self):
        # Deterministic fn of the seed -> stats fully reproducible.
        fn = lambda s: (s % 100) / 100.0
        a = repeated_run(fn, parent_seed=42, n_runs=10)
        b = repeated_run(fn, parent_seed=42, n_runs=10)
        self.assertEqual(a.samples, b.samples)
        self.assertEqual(a.mean, b.mean)
        self.assertEqual(a.n_runs, 10)

    def test_different_parent_seed_changes_samples(self):
        fn = lambda s: (s % 1000) / 1000.0
        a = repeated_run(fn, parent_seed=1, n_runs=8)
        b = repeated_run(fn, parent_seed=2, n_runs=8)
        self.assertNotEqual(a.samples, b.samples)

    def test_to_dict_has_interpretation(self):
        s = repeated_run(lambda s: float(s % 7), parent_seed=3, n_runs=5)
        d = s.to_dict()
        self.assertIn("interpretation", d)
        self.assertIn("ci", d)


if __name__ == "__main__":
    unittest.main()
