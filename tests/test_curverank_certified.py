"""Tests for the certified Berry-Keating spectral-screening pipeline.

These verify that the certified interval-arithmetic pipeline reproduces the
recorded floating-point screening numbers, that the eigenvalue enclosures are
rigorous and tight, and that the certified mismatch is a valid lower bound.
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import (
    berry_keating_xp,
    berry_keating_xp_interval,
    dirac_rindler_truncated,
    quantum_graph_laplacian,
)
from gaugegap.curverank_spectral import (
    certified_spectral_mismatch,
    riemann_zero_intervals,
    riemann_zero_targets,
    spectral_mismatch,
)
from gaugegap.curverank_certified import (
    certified_dirac_rindler_spectrum,
    certified_family_mismatch,
    certified_quantum_graph_spectrum,
    certified_xp_mismatch,
    certified_xp_spectrum,
)
from gaugegap.rigorous.interval_arithmetic import verified_hermitian_eigenvalues

_GRAPH_EDGES = [(0, 1), (0, 2), (0, 3)]
_GRAPH_LENGTHS = [1.0, float(np.sqrt(2)), float(np.sqrt(3))]

# Recorded floating-point screening values (results/sprint-now), k_zeros=20.
RECORDED = {10: 27.391322449240914, 15: 31.884970126092618, 20: 35.53568994244663}


class TestCertifiedXPSpectrum(unittest.TestCase):
    def test_embedding_eigenvalues_enclosed(self):
        # Every eigenvalue of the embedding's own midpoint matrix must lie
        # inside a certified enclosure (rigorous self-consistency).
        B = berry_keating_xp_interval(8)
        enclosures = verified_hermitian_eigenvalues(B)
        true_eigs = np.sort(np.linalg.eigvalsh(B.to_numpy()))
        for f in true_eigs:
            self.assertTrue(any(e.contains(f) for e in enclosures))

    def test_spectrum_matches_float_operator(self):
        # Certified spectrum midpoints reproduce the complex operator spectrum.
        for n in (8, 12):
            ce = certified_xp_spectrum(n)
            self.assertEqual(len(ce), n)
            mids = np.array(sorted(float(iv.midpoint()) for iv in ce))
            fe = np.sort(np.linalg.eigvalsh(berry_keating_xp(n)))
            np.testing.assert_allclose(mids, fe, atol=1e-9)
            self.assertLess(max(float(iv.width()) for iv in ce), 1e-6)


class TestOtherCertifiedFamilies(unittest.TestCase):
    def test_dirac_rindler_spectrum_matches_float(self):
        for n in (6, 8):
            ce = certified_dirac_rindler_spectrum(n, acceleration=1.0, mass=0.1)
            self.assertEqual(len(ce), 2 * n)
            mids = np.array(sorted(float(iv.midpoint()) for iv in ce))
            fe = np.sort(np.linalg.eigvalsh(dirac_rindler_truncated(n, 1.0, 0.1)))
            np.testing.assert_allclose(mids, fe, atol=1e-9)
            self.assertLess(max(float(iv.width()) for iv in ce), 1e-6)

    def test_quantum_graph_spectrum_matches_float(self):
        for nm in (4, 8):
            ce = certified_quantum_graph_spectrum(_GRAPH_EDGES, _GRAPH_LENGTHS, nm)
            self.assertEqual(len(ce), 3 * nm)
            mids = np.array(sorted(float(iv.midpoint()) for iv in ce))
            fe = np.sort(
                np.linalg.eigvalsh(
                    quantum_graph_laplacian(_GRAPH_EDGES, _GRAPH_LENGTHS, nm)
                )
            )
            np.testing.assert_allclose(mids, fe, atol=1e-8)
            self.assertLess(max(float(iv.width()) for iv in ce), 1e-6)

    def test_family_mismatch_dispatch(self):
        for family, n in (("xp", 10), ("dirac_rindler", 8), ("quantum_graph", 8)):
            mm = certified_family_mismatch(family, n, 20)
            self.assertLessEqual(mm.lower, mm.upper)
            self.assertGreater(float(mm.lower), 0.0)

    def test_unknown_family_raises(self):
        with self.assertRaises(ValueError):
            certified_family_mismatch("nope", 8, 20)


class TestRiemannZeroIntervals(unittest.TestCase):
    def test_first_zero_enclosed(self):
        intervals = riemann_zero_intervals(5)
        self.assertEqual(len(intervals), 5)
        self.assertTrue(intervals[0].contains(14.134725141734693))

    def test_agrees_with_float_targets(self):
        intervals = riemann_zero_intervals(10)
        targets = riemann_zero_targets(10)
        for iv, t in zip(intervals, targets):
            self.assertTrue(iv.contains(float(t)))


class TestCertifiedMismatch(unittest.TestCase):
    def test_reproduces_recorded_values(self):
        for n, recorded in RECORDED.items():
            enclosure = certified_xp_mismatch(n, 20)
            self.assertLessEqual(enclosure.lower, enclosure.upper)
            mid = float(enclosure.midpoint())
            self.assertAlmostEqual(mid, recorded, places=6)
            # Certified enclosure must be tight.
            self.assertLess(float(enclosure.width()), 1e-6)

    def test_lower_bound_is_valid_lower_bound(self):
        # The certified lower endpoint must not exceed the float mismatch.
        for n in (10, 15, 20):
            enclosure = certified_xp_mismatch(n, 20)
            fe = np.linalg.eigvalsh(berry_keating_xp(n))
            float_mismatch = spectral_mismatch(fe, riemann_zero_targets(20))
            self.assertLessEqual(float(enclosure.lower), float_mismatch + 1e-9)

    def test_perfect_match_is_zero(self):
        # Comparing certified zeros against themselves gives mismatch ~ 0.
        zeros = riemann_zero_intervals(5)
        enclosure = certified_spectral_mismatch(zeros, zeros)
        self.assertLess(float(enclosure.lower), 1e-30)

    def test_overlapping_enclosures_stay_a_valid_lower_bound(self):
        # Regression for the order-statistic fix: with overlapping eigenvalue
        # enclosures the naive midpoint pairing would OVERSTATE the lower bound
        # (claiming ~1.06 here), which is not a valid certificate. The true
        # minimum mismatch achievable by some configuration consistent with the
        # intervals is sqrt(1/2); the certified lower bound must not exceed it.
        import mpmath as mp
        from gaugegap.rigorous.interval_arithmetic import Interval

        eigs = [Interval(mp.mpf(0), mp.mpf(10)), Interval(mp.mpf(6), mp.mpf(7))]
        zeros = [Interval(mp.mpf(8), mp.mpf(8)), Interval(mp.mpf("8.5"), mp.mpf("8.5"))]
        enclosure = certified_spectral_mismatch(eigs, zeros)

        true_min = mp.sqrt(mp.mpf(1) / 2)  # config A=8.5, B=7 -> sort [7, 8.5]
        self.assertLessEqual(enclosure.lower, true_min + mp.mpf("1e-30"))
        # And it should be tight (equal to the true achievable minimum here).
        self.assertAlmostEqual(float(enclosure.lower), float(true_min), places=12)


if __name__ == "__main__":
    unittest.main()
