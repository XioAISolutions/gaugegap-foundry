"""Tests for independently certified Riemann-zero enclosures (Arb).

The Arb-backed tests are skipped when the optional ``python-flint`` dependency
is not installed; the method-dispatch tests run everywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_spectral import riemann_zero_intervals, riemann_zero_targets
from gaugegap.rigorous.certified_zeros import arb_available


class TestMethodDispatch(unittest.TestCase):
    def test_invalid_method_raises(self):
        with self.assertRaises(ValueError):
            riemann_zero_intervals(5, method="nope")

    def test_invalid_k_raises(self):
        with self.assertRaises(ValueError):
            riemann_zero_intervals(0)

    def test_zetazero_path_still_works(self):
        intervals = riemann_zero_intervals(5, method="zetazero")
        targets = riemann_zero_targets(5)
        self.assertEqual(len(intervals), 5)
        for iv, t in zip(intervals, targets):
            self.assertTrue(iv.contains(float(t)))

    def test_auto_works_regardless_of_flint(self):
        # auto must return valid enclosures whether or not Arb is installed.
        intervals = riemann_zero_intervals(10)
        targets = riemann_zero_targets(10)
        self.assertEqual(len(intervals), 10)
        for iv, t in zip(intervals, targets):
            self.assertTrue(iv.contains(float(t)))

    def test_arb_method_raises_cleanly_when_unavailable(self):
        if arb_available():
            self.skipTest("python-flint installed; unavailability path not testable")
        with self.assertRaises(ImportError):
            riemann_zero_intervals(5, method="arb")


@unittest.skipUnless(arb_available(), "python-flint >= 0.7 not installed")
class TestArbZeroIntervals(unittest.TestCase):
    def test_contains_reference_floats(self):
        intervals = riemann_zero_intervals(50, method="arb")
        targets = riemann_zero_targets(50)
        self.assertEqual(len(intervals), 50)
        for iv, t in zip(intervals, targets):
            self.assertTrue(iv.contains(float(t)))

    def test_enclosures_are_tight(self):
        # Guard-inflated widths must still be astronomically tighter than the
        # zetazero path (and than any spectral scale in the pipeline).
        intervals = riemann_zero_intervals(20, method="arb")
        for iv in intervals:
            self.assertLess(float(iv.width()), 1e-35)

    def test_disjoint_and_ascending(self):
        # Index correctness requires strictly ordered, pairwise-disjoint
        # enclosures.
        intervals = riemann_zero_intervals(50, method="arb")
        for j in range(len(intervals) - 1):
            self.assertLess(intervals[j].upper, intervals[j + 1].lower)

    def test_mutually_consistent_with_zetazero(self):
        # The two independent implementations must agree: every Arb enclosure
        # must intersect the corresponding zetazero enclosure.
        arb_ivs = riemann_zero_intervals(20, method="arb")
        zz_ivs = riemann_zero_intervals(20, method="zetazero")
        for a, z in zip(arb_ivs, zz_ivs):
            self.assertLess(a.lower, z.upper)
            self.assertLess(z.lower, a.upper)

    def test_certified_mismatch_reproduces_recorded_value(self):
        # End-to-end: the headline certified mismatch is unchanged when the
        # trusted zetazero intervals are replaced by Arb enclosures.
        from gaugegap.curverank_certified import certified_xp_mismatch

        enclosure = certified_xp_mismatch(10, 20)
        self.assertAlmostEqual(
            float(enclosure.midpoint()), 27.391322449240914, places=6
        )
        self.assertLess(float(enclosure.width()), 1e-6)


if __name__ == "__main__":
    unittest.main()
